"""
ornek_veri_uret.py — SİMÜLE (yapay) örnek veri üretir.

AMAÇ: Gerçek laboratuvar verisi toplanmadan önce veri işleme + model eğitme
hattının (pipeline) uçtan uca çalıştığını göstermek. Değerler, her arıza
türünde ağın tipik davranışına göre elle belirlenmiş dağılımlardan çekilir;
gürültü ve sınıflar arası örtüşme bilerek eklenmiştir.
Bu verinin sonuçları gerçek başarı olarak SUNULMAMALIDIR.
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
N = 250  # sınıf başına örnek


def kirp(x, alt=0):
    return np.round(np.maximum(x, alt), 1)


def uret(etiket, n):
    d = {}
    if etiket == "normal":
        d["gw_ping_ok"] = np.ones(n)
        d["gw_rtt_ms"] = kirp(rng.gamma(2, 1.0, n) + 0.5)
        d["ext_ping_ok"] = np.ones(n)
        d["rtt_avg"] = kirp(rng.normal(25, 6, n), 5)
        d["rtt_std"] = kirp(rng.gamma(2, 1.5, n))
        d["loss_pct"] = rng.choice([0, 0, 0, 0, 0, 0, 0, 0, 20], n).astype(float)
        d["dns_ok"] = rng.choice([1] * 49 + [0], n)
        d["dns_time_ms"] = np.where(d["dns_ok"] == 1, kirp(rng.gamma(3, 10, n), 5), 2000)
        d["tcp_ok"] = np.ones(n)
        d["tcp_ms"] = kirp(rng.normal(35, 10, n), 5)
    elif etiket == "dns_error":
        d["gw_ping_ok"] = np.ones(n)
        d["gw_rtt_ms"] = kirp(rng.gamma(2, 1.0, n) + 0.5)
        d["ext_ping_ok"] = np.ones(n)
        d["rtt_avg"] = kirp(rng.normal(26, 7, n), 5)
        d["rtt_std"] = kirp(rng.gamma(2, 1.5, n))
        d["loss_pct"] = rng.choice([0] * 9 + [20], n).astype(float)
        d["dns_ok"] = rng.choice([0] * 9 + [1], n)  # ara sıra önbellekten yanıt
        d["dns_time_ms"] = np.where(d["dns_ok"] == 1, kirp(rng.normal(900, 300, n), 200), 2000)
        d["tcp_ok"] = rng.choice([1, 1, 0], n)  # IP ile bağlantı çoğunlukla çalışır
        d["tcp_ms"] = np.where(d["tcp_ok"] == 1, kirp(rng.normal(36, 10, n), 5), 2000)
    elif etiket == "gateway_error":
        d["gw_ping_ok"] = rng.choice([0] * 19 + [1], n)
        d["gw_rtt_ms"] = np.where(d["gw_ping_ok"] == 1, kirp(rng.gamma(2, 3, n) + 1), -1)
        d["ext_ping_ok"] = np.zeros(n)
        d["rtt_avg"] = -np.ones(n)
        d["rtt_std"] = -np.ones(n)
        d["loss_pct"] = np.full(n, 100.0)
        d["dns_ok"] = np.zeros(n)
        d["dns_time_ms"] = np.full(n, 2000.0)
        d["tcp_ok"] = np.zeros(n)
        d["tcp_ms"] = np.full(n, 2000.0)
    elif etiket == "congestion":
        d["gw_ping_ok"] = np.ones(n)
        d["gw_rtt_ms"] = kirp(rng.gamma(3, 15, n) + 2)
        d["ext_ping_ok"] = rng.choice([1] * 19 + [0], n)
        d["rtt_avg"] = np.where(d["ext_ping_ok"] == 1, kirp(rng.normal(180, 70, n), 40), -1)
        d["rtt_std"] = np.where(d["ext_ping_ok"] == 1, kirp(rng.gamma(3, 15, n)), -1)
        d["loss_pct"] = np.where(d["ext_ping_ok"] == 1, rng.choice([0, 0, 20, 20, 40, 60], n), 100).astype(float)
        d["dns_ok"] = rng.choice([1] * 4 + [0], n)
        d["dns_time_ms"] = np.where(d["dns_ok"] == 1, kirp(rng.normal(300, 150, n), 30), 2000)
        d["tcp_ok"] = rng.choice([1] * 4 + [0], n)
        d["tcp_ms"] = np.where(d["tcp_ok"] == 1, kirp(rng.normal(350, 150, n), 50), 2000)
    elif etiket == "service_error":
        d["gw_ping_ok"] = np.ones(n)
        d["gw_rtt_ms"] = kirp(rng.gamma(2, 1.0, n) + 0.5)
        d["ext_ping_ok"] = np.ones(n)
        d["rtt_avg"] = kirp(rng.normal(25, 6, n), 5)
        d["rtt_std"] = kirp(rng.gamma(2, 1.5, n))
        d["loss_pct"] = rng.choice([0] * 9 + [20], n).astype(float)
        d["dns_ok"] = rng.choice([1] * 49 + [0], n)
        d["dns_time_ms"] = np.where(d["dns_ok"] == 1, kirp(rng.gamma(3, 10, n), 5), 2000)
        d["tcp_ok"] = rng.choice([0] * 9 + [1], n)  # bazen port açık ama uygulama yanıtsız
        d["tcp_ms"] = np.where(d["tcp_ok"] == 1, kirp(rng.normal(40, 10, n), 5), 2000)
    df = pd.DataFrame(d)
    df["label"] = etiket
    return df


if __name__ == "__main__":
    siniflar = ["normal", "dns_error", "gateway_error", "congestion", "service_error"]
    df = pd.concat([uret(s, N) for s in siniflar], ignore_index=True).sample(frac=1, random_state=1)
    for c in ["gw_ping_ok", "ext_ping_ok", "dns_ok", "tcp_ok"]:
        df[c] = df[c].astype(int)
    df.to_csv("data/ornek_veri.csv", index=False)
    print(df["label"].value_counts())
    print("data/ornek_veri.csv yazıldı (SİMÜLE veri).")
