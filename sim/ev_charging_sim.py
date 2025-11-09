"""EV şarj oturumu termal/direnç anomali simülatörü

Araç tarafı konnektörde bakır yerine demir gibi uygunsuz bir iletken malzeme
bulunması sonucu artan temas direncini simüle eder. Model I^2R kayıplarını,
basit bir termal kapasitans ve ısı iletim direnci modelini kullanarak
konektör sıcaklığını hesaplar, hızlı sıcaklık artışını veya eşik aşımını
algılar, derating adımları uygular ve kritik sıcaklığa ulaşılırsa kontağı açar.

Çalıştırma:
    python -m sim.ev_charging_sim --scenario iron

Çıktılar:
    - ISO biçimli logları stdout'a yazdırır
    - 'sim/ev_simulation.log' dosyasına log yazar

Bu kod kasıtlı olarak basit tutulmuş ve denemeler için parametrelenmiştir.
"""
from __future__ import annotations

import argparse
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Tuple


LOG_FILE = Path(__file__).parent / "ev_simulation.log"


class Connector:
    """Konnektör/pin için termal ve elektriksel basit model.

    Elektriksel: P_loss = I^2 * R_contact
    Termal: C * dT/dt = P_loss - (T - T_amb) / Rth
    (Burada model basit tutulmuştur; amaç kavramsal gösterimdir.)
    """

    def __init__(
        self,
        contact_resistance_ohm: float,
        temp_c: float = 25.0,
        heat_capacity_j_per_c: float = 200.0,
        thermal_resistance_c_per_w: float = 0.5,
    ) -> None:
        self.contact_resistance = contact_resistance_ohm
        self.temp_c = temp_c
        self.heat_capacity = heat_capacity_j_per_c
        self.thermal_resistance = thermal_resistance_c_per_w

    def step(self, current_a: float, dt_s: float, t_amb: float = 25.0) -> Tuple[float, float]:
        """Advance thermal state by dt seconds under current `current_a`.

        Returns:
            (power_loss_watts, dT_dt_c_per_s)
        """
        p_loss = (current_a ** 2) * self.contact_resistance
    # ortamaya ısı akışı (W)
        heat_flow = (self.temp_c - t_amb) / self.thermal_resistance
        dT_dt = (p_loss - heat_flow) / self.heat_capacity
        self.temp_c += dT_dt * dt_s
        return p_loss, dT_dt


class ChargingStation:
    def __init__(self, station_id: str, nominal_current_a: float = 32.0):
        self.station_id = station_id
        self.nominal_current_a = nominal_current_a
    # uyarı durumunda sırasıyla uygulanacak akım düşürme adımları (A)
        self.derate_steps = [nominal_current_a, 16.0, 10.0, 0.0]
        self.current_idx = 0

    @property
    def current_a(self) -> float:
        return self.derate_steps[self.current_idx]

    def derate_once(self) -> None:
        if self.current_idx < len(self.derate_steps) - 1:
            self.current_idx += 1


class Simulator:
    def __init__(
        self,
        station: ChargingStation,
        connector: Connector,
        user_id: str = "U-987",
        conn_id: int = 1,
        v_nominal: float = 230.0,
        line_impedance_ohm: float = 0.02,
    ) -> None:
        self.station = station
        self.connector = connector
        self.user_id = user_id
        self.conn_id = conn_id
        self.v_nominal = v_nominal
        self.line_impedance = line_impedance_ohm
        self.t_amb = 25.0

    # algılama eşikleri
        self.warn_temp_c = 80.0
        self.critical_temp_c = 100.0
        # dT/dt threshold in C/s (sample dT/dt in description ~ 6 C/min -> 0.1 C/s)
    # dT/dt eşiği C/s cinsinden (ör: 6 °C/dak = 0.1 °C/s civarı)
    self.dTdt_warn_c_per_s = 0.08

        # logging
        self.logger = logging.getLogger("ev_sim")
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fmt = logging.Formatter("%(message)s")
        fh.setFormatter(fmt)
        if not self.logger.handlers:
            self.logger.addHandler(fh)

    def _log(self, timestamp: datetime, event: str, ac_v: float, ac_i: float, t_conn: float, dTdt_c_per_min: float) -> None:
        # Örnek log formatına benzer biçim
        s = (
            f"{timestamp.isoformat(timespec='seconds')}Z | StationID: {self.station.station_id} | UserID: {self.user_id} | "
            f"Conn: {self.conn_id} | AC_V: {ac_v:.1f}V | AC_I: {ac_i:.1f}A | T_conn: {t_conn:.1f}C | "
            f"dTdt: {dTdt_c_per_min:.1f}C/min | Olay: {event}"
        )
        print(s)
        self.logger.debug(s)

    def run(self, max_minutes: float = 20.0, dt_s: float = 1.0) -> List[str]:
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        end_time = now + timedelta(minutes=max_minutes)

        last_event_time = now
        stopped = False
        logs: List[str] = []

    # Başlangıç kaydı: oturum başlıyor
    self._log(now, "OturumBaşlatıldı", self.v_nominal, self.station.current_a, self.connector.temp_c, 0.0)

        t = now
    # dT/dt hesabı için küçük bir tampon (saniye cinsinden)
        last_temp = self.connector.temp_c
        while t < end_time and not stopped:
            ac_i = self.station.current_a
            # hat geriliminde hafif sarkma simülasyonu: V = V_nominal - I * Z_line
            v_line = self.v_nominal - ac_i * self.line_impedance

            p_loss, dTdt = self.connector.step(ac_i, dt_s, t_amb=self.t_amb)
            # dT/dt (C/dak) formatında raporlanır (örnekle eşleşmesi için)
            dTdt_per_min = dTdt * 60.0

            # yaklaşık teslim edilen şarj gücünü hesapla
            charging_power_w = v_line * ac_i

            # Algılama mantığı
            #  - hızlı sıcaklık artışı
            if dTdt > self.dTdt_warn_c_per_s and self.station.current_a > 0:
                # akımı düşür ve uyarı kaydı
                event = "Yüksek temas direnci şüphesi; akım azaltıldı"
                self.station.derate_once()
                self._log(t, event, v_line, self.station.current_a, self.connector.temp_c, dTdt_per_min)

            #  - uyarı sıcaklığına ulaşıldı
            if self.connector.temp_c >= self.warn_temp_c and self.station.current_a > 0:
                # kademeli akım düşürme
                event = "Konnektör sıcaklığı uyarı eşiğini aştı; akım azaltıldı"
                self.station.derate_once()
                self._log(t, event, v_line, self.station.current_a, self.connector.temp_c, dTdt_per_min)

            #  - kritik sıcaklık: kontaktörü aç ve oturumu durdur
            if self.connector.temp_c >= self.critical_temp_c:
                event = "Kontaktör açıldı; StopTransaction nedeni=YüksekSıcaklık"
                self._log(t, event, v_line, 0.0, self.connector.temp_c, dTdt_per_min)
                stopped = True
                break

            # Her 30 saniyede bir periyodik durum kaydı
            if (t - last_event_time).total_seconds() >= 30:
                self._log(t, "PeriyodikDurum", v_line, self.station.current_a, self.connector.temp_c, dTdt_per_min)
                last_event_time = t

            # advance time
            t += timedelta(seconds=dt_s)

        if not stopped:
            self._log(t, "StopTransaction nedeni=Normal", v_line, self.station.current_a, self.connector.temp_c, 0.0)

        return []


def build_scenario(scenario_name: str) -> Tuple[ChargingStation, Connector]:
    station = ChargingStation("ST-123", nominal_current_a=32.0)
    if scenario_name == "iron":
        # iron contact: significantly higher contact resistance
        contact_r = 0.0035  # ohm (tuned to produce rapid heating in simulation)
        # smaller heat capacity for a small pin
        connector = Connector(contact_r, temp_c=25.0, heat_capacity_j_per_c=120.0, thermal_resistance_c_per_w=0.4)
    else:
        # copper contact: low contact resistance
        contact_r = 0.00005
        connector = Connector(contact_r, temp_c=25.0, heat_capacity_j_per_c=200.0, thermal_resistance_c_per_w=0.5)
    return station, connector


def main() -> None:
    parser = argparse.ArgumentParser(description="EV şarj kontak direnci termal anomali simülatörü")
    parser.add_argument("--scenario", choices=["iron", "copper"], default="iron")
    parser.add_argument("--duration-min", type=float, default=20.0)
    args = parser.parse_args()

    station, connector = build_scenario(args.scenario)
    sim = Simulator(station, connector)
    sim.run(max_minutes=args.duration_min, dt_s=1.0)


if __name__ == "__main__":
    main()
