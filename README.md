# TurkceAltyazi.org Scrapper

Bu proje, `turkcealtyazi.org` uzerinden film/dizi altyazisi aramak ve indirmek icin terminal tabanli bir aractir.

## Ozellikler

- Akilli film/dizi arama ve siralama
- Dil filtresi: `Turkce / Ingilizce / Hepsi`
- Dizi icin `Sezon` ve `Bolum` filtresi
- Tekli indirme veya toplu indirme
- Ayni dosya varsa tekrar indirmeyi atlama
- Daha dengeli istek hizi (ban riskini azaltmak icin gecikme/retry)

## Kurulum

1. Python 3.8+ kurulu olmali.
2. Proje klasorune girin:
   ```bash
   cd scrapper
   ```
3. Bagimliliklari yukleyin:
   ```bash
   pip install -r requirements.txt
   ```

## Kullanim

Scripti calistirin:

```bash
python main.py
```

Uygulama sirasiyla su adimlari sorar:

1. Film/dizi adi
2. Arama sonucundan secim
3. Altyazi dili (`Turkce`, `Ingilizce`, `Hepsi`)
4. Sezon (opsiyonel)
5. Bolum (opsiyonel)
6. Indirme modu:
   - `1`: Tek altyazi sec
   - `2`: Filtrelenenlerin hepsini indir (toplu)

Indirilen dosyalar `downloads/` klasorune kaydedilir.

## Ornek Akis

```text
Aramak istediginiz film/dizi adini girin: from
Secmek istediginiz filmin numarasini girin (1-10): 1
Altyazi dili secin: 1
Sezon: 4
Bolum: 2
Indirme modu: 2
```

Bu secimde `From` dizisinin `S04E02` icin filtrelenen altyazilar toplu indirilir.

## Notlar

- Arac egitim ve kisisel kullanim amaclidir.
- Site kurallarina ve telif kosullarina uyun.
- Site HTML yapisi degisirse selector uyarisi verebilir; bu durumda parser guncellenmelidir.

## Dosya Yapisi

- `main.py`: CLI akisi
- `scraper.py`: Arama, filtreleme, indirme mantigi
- `utils.py`: Yazdirma ve yardimci fonksiyonlar
- `requirements.txt`: Python bagimliliklari
