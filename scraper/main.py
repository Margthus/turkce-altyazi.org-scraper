from scraper import SubtitleScraper
from utils import ensure_dir, print_results, print_subtitles


def choose_language():
    print("Altyazi dili secin:")
    print("1. Turkce")
    print("2. Ingilizce")
    print("3. Hepsi")
    raw = input("Secim (1-3, varsayilan 1): ").strip() or "1"
    mapping = {"1": "tr", "2": "en", "3": "all"}
    return mapping.get(raw, "tr")

def choose_season_episode():
    season_raw = input("Sezon (opsiyonel, bos birak = fark etmez): ").strip()
    episode_raw = input("Bolum (opsiyonel, bos birak = fark etmez): ").strip()

    season = int(season_raw) if season_raw.isdigit() else None
    episode = int(episode_raw) if episode_raw.isdigit() else None
    return season, episode

def choose_download_mode():
    print("Indirme modu:")
    print("1. Tek altyazi sec")
    print("2. Filtrelenenlerin hepsini indir (toplu)")
    raw = input("Secim (1-2, varsayilan 1): ").strip() or "1"
    return "bulk" if raw == "2" else "single"


def main():
    scraper = SubtitleScraper()
    ensure_dir("downloads")

    query = input("Aramak istediginiz film/dizi adini girin: ").strip()
    if not query:
        print("Bos arama yapilamaz.")
        return

    print("Araniyor...")
    try:
        results = scraper.search(query)
        if not results:
            print("Sonuc bulunamadi.")
            return

        print("Arama Sonuclari:")
        print_results(results)

        choice = int(input(f"Secmek istediginiz filmin numarasini girin (1-{len(results)}): "))
        if choice < 1 or choice > len(results):
            print("Gecersiz secim.")
            return

        selected_movie = results[choice - 1]
        print(f"Secilen: {selected_movie['title']}")

        lang = choose_language()
        season, episode = choose_season_episode()
        print("Altyazilar yukleniyor...")
        subtitles = scraper.get_subtitles(
            selected_movie["url"],
            language=lang,
            season=season,
            episode=episode,
        )
        if scraper.last_warning:
            print(scraper.last_warning)
        if not subtitles:
            print("Bu filtrede altyazi bulunamadi.")
            return

        print("Altyazilar:")
        print_subtitles(subtitles)
        mode = choose_download_mode()

        if mode == "bulk":
            downloaded = 0
            skipped = 0
            for idx, sub in enumerate(subtitles, 1):
                print(f"[{idx}/{len(subtitles)}] Isleniyor: {sub['season_ep']}")
                filepath, is_new = scraper.download_subtitle(sub["url"], skip_existing=True)
                if is_new:
                    downloaded += 1
                    print(f"  Indirildi: {filepath}")
                else:
                    skipped += 1
                    print(f"  Atlandi (zaten var): {filepath}")
            print(f"Toplu indirme bitti. Yeni: {downloaded}, Atlanan: {skipped}")
        else:
            sub_choice = int(input(f"Indirmek istediginiz altyazinin numarasini girin (1-{len(subtitles)}): "))
            if sub_choice < 1 or sub_choice > len(subtitles):
                print("Gecersiz secim.")
                return

            selected_sub = subtitles[sub_choice - 1]
            print(f"Indiriliyor: {selected_sub['season_ep']}")

            filepath, is_new = scraper.download_subtitle(selected_sub["url"], skip_existing=True)
            if is_new:
                print(f"Indirme tamamlandi: {filepath}")
            else:
                print(f"Dosya zaten var, atlandi: {filepath}")

    except Exception as e:
        print(f"Hata: {e}")


if __name__ == "__main__":
    main()
