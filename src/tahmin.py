"""
tahmin.py — Bilgisayarın şu anki bağlantısını ölçer ve eğitilmiş modelle
olası arıza türünü tahmin eder (canlı demo).

    python src/tahmin.py --gateway 192.168.1.1
    python src/tahmin.py --gateway 192.168.1.1 --dns 10.255.255.1    (DNS arızası taklidi)
"""
import argparse
import joblib
import pandas as pd
from veri_topla import olcum

OZELLIKLER = ["gw_ping_ok", "gw_rtt_ms", "ext_ping_ok", "rtt_avg", "rtt_std",
              "loss_pct", "dns_ok", "dns_time_ms", "tcp_ok", "tcp_ms"]

ACIKLAMA = {
    "normal": "Bağlantı normal görünüyor.",
    "dns_error": "DNS hatası: ağ geçidi ve IP bağlantısı çalışıyor ama alan adı çözümlenemiyor. DNS sunucu ayarını kontrol et.",
    "gateway_error": "Ağ geçidi sorunu: yerel ağdan dışarı çıkılamıyor. Varsayılan ağ geçidi / IP ayarlarını kontrol et.",
    "congestion": "Yoğunluk: gecikme ve paket kaybı yüksek. Bant genişliği kullanımını kontrol et.",
    "service_error": "Servis erişim sorunu: ağ çalışıyor ama hedef porta bağlanılamıyor. Servis veya firewall kuralını kontrol et.",
}

p = argparse.ArgumentParser()
p.add_argument("--gateway", required=True)
p.add_argument("--dis-ip", default="8.8.8.8")
p.add_argument("--dns", default=None)
p.add_argument("--alan-adi", default="www.google.com")
p.add_argument("--hedef", default="www.google.com")
p.add_argument("--port", type=int, default=443)
p.add_argument("--ping-adet", type=int, default=5)
p.add_argument("--model", default="sonuclar/en_iyi_model.joblib")
a = p.parse_args()
a.etiket = "?"

model = joblib.load(a.model)
o = olcum(a)
X = pd.DataFrame([o])[OZELLIKLER]
print("Ölçüm:", {k: o[k] for k in OZELLIKLER})
olasilik = dict(zip(model.classes_, model.predict_proba(X)[0]))
tahmin = max(olasilik, key=olasilik.get)
print(f"\nBağlantı sorununun olası türü: {tahmin}  (güven: %{olasilik[tahmin] * 100:.0f})")
print(ACIKLAMA.get(tahmin, ""))
print("\nTüm olasılıklar:", {k: round(float(v), 2) for k, v in sorted(olasilik.items(), key=lambda x: -x[1])})
