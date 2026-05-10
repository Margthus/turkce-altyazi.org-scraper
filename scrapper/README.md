# Türkçe Altyazı Scraper

Bu proje, https://turkcealtyazi.org/ sitesinden Türkçe altyazı aramak ve indirmek için bir web scraper'dır.

## Kurulum

1. Python 3.8+ yüklü olduğundan emin olun.
2. Gerekli paketleri yükleyin:
   ```
   pip install -r requirements.txt
   ```

## Kullanım

1. Ana script'i çalıştırın:
   ```
   python main.py
   ```

2. Arama terimini girin (film/dizi adı).
3. Sonuçlardan film/dizi seçin.
4. Altyazı listesinden indirmek istediğinizi seçin.
5. Altyazı downloads/ klasörüne indirilir.

## Özellikler

- Film/dizi arama
- Altyazı listesi görüntüleme
- Altyazı indirme (desteklenen formatlar: .srt, .zip vb.)

## Notlar

- Scraper eğitim amaçlıdır. Site kurallarına uyun.
- İndirme için siteye login gerekebilir (şu anda desteklenmiyor).
- Yasal uyarı: Altyazılar telif haklarına tabi olabilir.

## Yapı

- `scraper.py`: Ana scraper sınıfı
- `utils.py`: Yardımcı fonksiyonlar
- `main.py`: Kullanıcı arayüzü
- `requirements.txt`: Bağımlılıklar