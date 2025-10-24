from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple


#
# EV Şarj İstasyonu Güvenlik Senaryosu
# Konu: Saldırgan "tüketilen enerji" (kWh) değerini düşük göstererek faturalamayı manipüle ediyor (örn: 50 kW -> 5 kWh'a eşdeğer rapor).
# Amaç: Gelen telemetri çerçevelerindeki güç (kW) ve süre üzerinden beklenen enerji ile raporlanan enerji arasındaki tutarsızlığı yakalamak.
#


@dataclass
class TelemetryFrame:
    ts: float  # saniye cinsinden zaman damgası (simülasyon zamanı)
    station_id: str
    session_id: str
    power_kw: float  # anlık güç (kW)
    energy_kwh: float  # istasyonun raporladığı kümülatif tüketim (kWh)


@dataclass
class DetectionResult:
    is_anomaly: bool
    risk_score: int  # 0-100
    reason: str
    expected_energy_kwh: float
    reported_energy_kwh: float
    relative_error: float  # |reported - expected| / max(expected, 1e-6)


class EnergyAnomalyDetector:
    def __init__(self, *, error_threshold: float = 0.15):
        # Beklenen enerji ile raporlanan enerji arasındaki bağıl hata eşiği
        self.error_threshold = error_threshold

    @staticmethod
    def _integrate_energy(frames: List[TelemetryFrame]) -> float:
        # Basit dikdörtgen integrasyon: sum(power_kw * delta_t_sec) / 3600
        if not frames:
            return 0.0
        energy = 0.0
        for i in range(1, len(frames)):
            dt = frames[i].ts - frames[i - 1].ts
            if dt < 0:
                # Zaman geri gidiyorsa, veri bozuk say; atla
                continue
            # Gücü "önceki örnek" üzerinden entegre et
            energy += frames[i - 1].power_kw * dt / 3600.0
        return energy

    def evaluate(self, frames: List[TelemetryFrame]) -> DetectionResult:
        if not frames:
            return DetectionResult(False, 0, "Veri yok", 0.0, 0.0, 0.0)

        # Raporlanan kümülatif enerji olarak son çerçeveyi kullan
        reported = max(frames[-1].energy_kwh, 0.0)
        expected = max(self._integrate_energy(frames), 0.0)

        # Bağıl hata
        denom = max(expected, 1e-6)
        rel_err = abs(reported - expected) / denom

        # Eşik üzerinde ise anomali
        is_anom = rel_err > self.error_threshold

        # Basit risk skoru haritalaması
        if not is_anom:
            score = 0
            reason = "Tutarsızlık yok veya eşik altında"
        else:
            # 15% üzeri hatada 50-100 arası risk, logaritmik değil doğrusal basitçe
            over = min(max((rel_err - self.error_threshold) / (1.0 - self.error_threshold), 0.0), 1.0)
            score = int(50 + 50 * over)
            reason = (
                f"Raporlanan kWh beklenen değerden anlamlı derecede sapıyor (hata oranı={rel_err:.2%} > eşik={self.error_threshold:.0%})"
            )

        return DetectionResult(is_anom, score, reason, expected, reported, rel_err)


def simulate_session(
    *,
    station_id: str,
    session_id: str,
    duration_sec: int,
    rated_power_kw: float,
    anomaly: bool = False,
    anomaly_factor: float = 0.1,
) -> List[TelemetryFrame]:
    """
    Basit bir oturum telemetri üretimi.
    - Normalde enerji artışı: energy += power * dt / 3600
    - Anomalide (anomaly=True) raporlanan enerji, gerçek beklenenin belirli bir katsayısı ile manipüle edilir (ör: 0.1 = %10'u).
    """
    frames: List[TelemetryFrame] = []
    energy_kwh = 0.0
    t = 0.0
    step = 1.0  # 1 saniye aralıklarla örnekleme

    while t <= duration_sec:
        # Sabit güç altında küçük dalgalanma olabilir; basit tutuyoruz
        power_kw = rated_power_kw
        # Gerçek (beklenen) enerji artışı
        if frames:
            energy_kwh += frames[-1].power_kw * step / 3600.0

        reported_energy = energy_kwh if not anomaly else energy_kwh * anomaly_factor

        frames.append(
            TelemetryFrame(
                ts=t,
                station_id=station_id,
                session_id=session_id,
                power_kw=power_kw,
                energy_kwh=reported_energy,
            )
        )
        t += step

    return frames


def run_normal_flow() -> None:
    print("\n=== NORMAL AKIŞ: Doğru faturalama (kWh manipülasyonu yok) ===")
    detector = EnergyAnomalyDetector(error_threshold=0.15)
    frames = simulate_session(
        station_id="ST-1001",
        session_id="S-ABC",
        duration_sec=60,  # 1 dakika
        rated_power_kw=50.0,
        anomaly=False,
    )

    result = detector.evaluate(frames)
    print(
        f"[normal] expected_kWh={result.expected_energy_kwh:.3f}, reported_kWh={result.reported_energy_kwh:.3f}, "
        f"rel_err={result.relative_error:.2%}, is_anomaly={result.is_anomaly}, risk={result.risk_score}"
    )
    assert not result.is_anomaly, "Normal akışta anomali beklenmez"
    print("[normal] ✅ Anomali yok, değerler tutarlı.")


def run_anomaly_flow() -> None:
    print("\n=== ANOMALİ AKIŞI: Faturalama için kWh düşürme manipülasyonu ===")
    detector = EnergyAnomalyDetector(error_threshold=0.15)
    frames = simulate_session(
        station_id="ST-1001",
        session_id="S-DEF",
        duration_sec=60,
        rated_power_kw=50.0,
        anomaly=True,
        anomaly_factor=0.10,  # raporlanan enerji gerçek değerin %10'u (ör: 50kW -> 5kWh etkisi)
    )

    result = detector.evaluate(frames)
    print(
        f"[anomaly] expected_kWh={result.expected_energy_kwh:.3f}, reported_kWh={result.reported_energy_kwh:.3f}, "
        f"rel_err={result.relative_error:.2%}, is_anomaly={result.is_anomaly}, risk={result.risk_score}"
    )
    assert result.is_anomaly, "Anomali akışında tespit beklenir"
    print("[anomaly] ⚠️ KWh manipülasyonu tespit edildi.")


def print_scenario_summary() -> None:
    print("\n=== SENARYO ÖZETİ (Tabloya Kopyalanabilir) ===")
    print("- Senaryo Başlığı: Tüketilen enerji (kWh) manipülasyonu ile faturalama düşürme")
    print(
        "- Senaryo Özeti: Saldırgan, telemetrideki kümülatif 'tüketilen enerji' alanını gerçek değerden daha düşük raporlar (ör. 50kW yük için %10 kWh). "
        "Güç (kW) ve süre entegrasyonundan beklenen enerji ile raporlanan enerji arasındaki fark eşik üstünde ise anomali olarak işaretlenir."
    )
    print("- Tespit: expected_kWh vs reported_kWh bağıl hata > %15, kWh monoton artış ve süre/güç tutarlılığı kontrolü.")
    print("- Çözüm: Sayaç imzası/doğrulama, idari çapraz doğrulama, cihaz tarafında signed metrology, sunucu entegrasyonunda yeniden hesaplama ve eşik tabanlı alarmlar.")


if __name__ == "__main__":
    run_normal_flow()
    run_anomaly_flow()
    print_scenario_summary()
