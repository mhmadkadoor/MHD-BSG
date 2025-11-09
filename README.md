# EV konnektör temas direnci anomali simülatörü

Bu küçük Python simülatörü, araç tarafı konnektöründe artan temas direnci
(örneğin bakır yerine demir kullanımı) durumunu modeller. Model I2R kayıplarının
konnektörde hızlı ısınmaya yol açtığını, istasyonun akımı kademeli olarak
azaltabileceğini ve kritik sıcaklık aşıldığında oturumu durdurabileceğini gösterir.

Dosyalar
- `sim/ev_charging_sim.py`: ana simülatör. Python 3.8+ ile çalışır.

Hızlı çalışma

PowerShell'de proje kökünden çalıştırın:

```powershell
python -m sim.ev_charging_sim --scenario iron --duration-min 20
```

Notlar
- Script logları hem konsola yazdırır hem de `sim/ev_simulation.log` dosyasına kaydeder.
- Model gösterim amaçlı basitleştirilmiştir; daha gerçekçi analizler için
  termal/elektriksel parametreleri `build_scenario()` içinde ayarlayabilirsiniz.

Öneriler / Sonraki adımlar
- Derating ve durdurma davranışını doğrulayan küçük birim testleri ekleyin.
- Çalışma sonrası sıcaklık-zaman grafiği için basit bir çizim (matplotlib) ekleyin.
