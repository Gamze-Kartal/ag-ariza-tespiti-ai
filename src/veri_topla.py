"""
veri_topla.py — Ağ ölçümlerini toplayıp CSV'ye etiketli satır olarak ekler.

Windows, Linux ve macOS'ta çalışır. Gerekli paket:  pip install dnspython

Arızayı "taklit etmek" için ölçümü yanlış hedeflere yönlendirebilirsin
(gerçek laboratuvar kurulana kadar kendi bilgisayarında mini-laboratuvar):

  Normal bağlantı:
    python src/veri_topla.py --etiket normal --gateway 192.168.1.1
  DNS hatası (yanıt vermeyen DNS sunucusu):
    python src/veri_topla.py --etiket dns_error --gateway 192.168.1.1 --dns 10.255.255.1
  Ağ geçidi hatası (olmayan bir ağ geçidi adresi + dış bağlantı yok):
    python src/veri_topla.py --etiket gateway_error --gateway 192.168.1.250 --dis-ip 10.255.255.2
  Servis erişim hatası (kapalı port):
    python src/veri_topla.py --etiket service_error --gateway 192.168.1.1 --port 81

Ağ geçidi adresini öğrenmek için:  Windows: ipconfig   |  Linux/macOS: ip route / netstat -rn
"""
import argparse, csv, os, platform, re, socket, statistics, subprocess, time
from datetime import datetime

try:
    import dns.resolver
except ImportError:
    raise SystemExit("Önce şunu çalıştır:  pip install dnspython")

WIN = platform.system() == "Windows"
ALANLAR = ["zaman", "gw_ping_ok", "gw_rtt_ms", "ext_ping_ok", "rtt_avg", "rtt_std",
           "loss_pct", "dns_ok", "dns_time_ms", "tcp_ok", "tcp_ms", "label"]


def ping(hedef, adet=5, zaman_asimi=1):
    """Ping atar; (başarılı_mı, ort_rtt, std_rtt, kayıp_yüzdesi) döndürür."""
    if WIN:
        komut = ["ping", "-n", str(adet), "-w", str(zaman_asimi * 1000), hedef]
    else:
        komut = ["ping", "-c", str(adet), "-W", str(zaman_asimi), hedef]
    try:
        cikti = subprocess.run(komut, capture_output=True, timeout=adet * (zaman_asimi + 1) + 5).stdout
        cikti = cikti.decode("utf-8", errors="ignore")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        cikti = ""
    # Yalnızca yanıt satırları (TTL içerenler); özet satırları (Minimum = ...) sayılmaz.
    # "time=12ms", "süre=12ms", "time<1ms", "time=1.23 ms" gibi biçimleri yakalar.
    rtt = []
    for satir in cikti.splitlines():
        if "ttl" in satir.lower():
            m = re.search(r"(?:=|<)\s*(\d+(?:[.,]\d+)?)\s*ms", satir, re.I)
            if m:
                rtt.append(float(m.group(1).replace(",", ".")))
    yanit = len(rtt)
    kayip = round(100 * (adet - yanit) / adet, 1)
    if yanit == 0:
        return 0, -1, -1, 100.0
    return 1, round(statistics.mean(rtt), 2), round(statistics.pstdev(rtt), 2), kayip


def dns_sorgu(alan_adi, sunucu=None, zaman_asimi=2):
    r = dns.resolver.Resolver()
    if sunucu:
        r.nameservers = [sunucu]
    r.lifetime = zaman_asimi
    t0 = time.perf_counter()
    try:
        r.resolve(alan_adi, "A")
        return 1, round((time.perf_counter() - t0) * 1000, 1)
    except Exception:
        return 0, zaman_asimi * 1000


def tcp_test(host, port, zaman_asimi=2):
    t0 = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=zaman_asimi):
            return 1, round((time.perf_counter() - t0) * 1000, 1)
    except Exception:
        return 0, zaman_asimi * 1000


def olcum(a):
    gw_ok, gw_rtt, _, _ = ping(a.gateway, adet=3)
    ext_ok, rtt_avg, rtt_std, loss = ping(a.dis_ip, adet=a.ping_adet)
    dns_ok, dns_ms = dns_sorgu(a.alan_adi, a.dns)
    tcp_ok, tcp_ms = tcp_test(a.hedef, a.port)
    return dict(zaman=datetime.now().isoformat(timespec="seconds"), gw_ping_ok=gw_ok, gw_rtt_ms=gw_rtt,
                ext_ping_ok=ext_ok, rtt_avg=rtt_avg, rtt_std=rtt_std, loss_pct=loss,
                dns_ok=dns_ok, dns_time_ms=dns_ms, tcp_ok=tcp_ok, tcp_ms=tcp_ms, label=a.etiket)


def main():
    p = argparse.ArgumentParser(description="Etiketli ağ ölçümü toplar")
    p.add_argument("--etiket", required=True, help="normal / dns_error / gateway_error / congestion / service_error")
    p.add_argument("--gateway", required=True, help="Ağ geçidi IP adresi (ipconfig ile bul)")
    p.add_argument("--dis-ip", default="8.8.8.8", help="Dış bağlantı testi için IP")
    p.add_argument("--dns", default=None, help="Kullanılacak DNS sunucusu (boşsa sistemdeki)")
    p.add_argument("--alan-adi", default="www.google.com")
    p.add_argument("--hedef", default="www.google.com", help="Servis testi yapılacak sunucu")
    p.add_argument("--port", type=int, default=443)
    p.add_argument("--tekrar", type=int, default=10, help="Kaç ölçüm alınacak")
    p.add_argument("--ping-adet", type=int, default=5)
    p.add_argument("--dosya", default="data/lab_veri.csv")
    a = p.parse_args()

    yeni = not os.path.exists(a.dosya)
    with open(a.dosya, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ALANLAR)
        if yeni:
            w.writeheader()
        for i in range(a.tekrar):
            satir = olcum(a)
            w.writerow(satir)
            f.flush()
            print(f"[{i + 1}/{a.tekrar}] {satir}")
    print(f"\n{a.tekrar} ölçüm '{a.dosya}' dosyasına eklendi.")


if __name__ == "__main__":
    main()
