# Yapay Zekâ ile Ağ Arızası Türü Belirleme

**Bitirme Projesi** — Bağlantı ölçümlerine bakarak ağ sorununun olası türünü sınıflandıran sistem.

> “Bağlantı sorununun olası türü: DNS hatası / ağ geçidi sorunu / yoğunluk / servis erişim sorunu.”

## Proje nasıl çalışır?

1. **Sanal laboratuvar:** Arızalar bilerek oluşturulur (yanlış DNS, yanlış ağ geçidi, trafik yoğunluğu, kapalı servis).
2. **Ölçüm:** Her durumda ping (gecikme, paket kaybı), DNS sorgusu ve port bağlantı testi yapılır.
3. **Veri tablosu:** Ölçümler, doğru arıza etiketiyle birlikte CSV dosyasına kaydedilir.
4. **Model eğitimi:** Decision Tree ve Random Forest gibi modeller eğitilir ve karşılaştırılır.
5. **Tahmin:** Yeni bir ölçümde olası arıza türü tahmin edilir.

| Arıza | Tipik belirti |
|---|---|
| `gateway_error` | Ağ geçidine bile ulaşılamıyor |
| `dns_error` | Ping çalışıyor, alan adı çözülemiyor |
| `congestion` | Gecikme ve paket kaybı yüksek |
| `service_error` | Ağ sağlam, hedef port kapalı |

## Klasör yapısı

```
src/        Python kodları (veri toplama, model eğitimi, tahmin)
data/       Veri setleri (CSV)
sonuclar/   Model karşılaştırma tablosu ve grafikler
docs/       Ara rapor, yol haritası ve ağ / yapay zekâ çalışma notları
```

## Kurulum

```bash
pip install -r requirements.txt
```

## Kullanım

Tüm komutlar proje ana klasöründen çalıştırılır.

```bash
# 1) Deneme verisi üret ve modelleri eğit
python src/ornek_veri_uret.py
python src/model_egit.py data/ornek_veri.csv

# 2) Canlı tahmin (ağ geçidi adresini ipconfig / ip route ile bul)
python src/tahmin.py --gateway 192.168.1.1

# 3) Etiketli gerçek ölçüm topla
python src/veri_topla.py --etiket normal    --gateway 192.168.1.1 --tekrar 30
python src/veri_topla.py --etiket dns_error --gateway 192.168.1.1 --dns 10.255.255.1 --tekrar 30
python src/model_egit.py data/lab_veri.csv
```

## Durum

- [x] Ölçüm toplama betiği
- [x] Model eğitim ve karşılaştırma hattı
- [x] Canlı tahmin demosu
- [ ] Sanal laboratuvar kurulumu
- [ ] Gerçek laboratuvar verisinin toplanması
- [ ] HTTP durum kodu özelliğinin eklenmesi
- [ ] (İsteğe bağlı) RAG / Agent açıklama katmanı

## Kısıt

`data/ornek_veri.csv` **simüle edilmiş** veridir. Yalnızca yazılımın uçtan uca çalıştığını göstermek için kullanılır ve sonuçları gerçek model başarısı değildir. Sistem, oluşturulan sanal ağdaki seçili arıza türleri için doğrulanacaktır. Farklı gerçek ağlardaki başarısını değerlendirmek için ek testler gerekir.
