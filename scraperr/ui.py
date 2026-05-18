import tkinter as tk
from tkinter import messagebox, ttk

from scraper import SubtitleScraper


class ScraperUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TurkceAltyazi Scraper")
        self.root.geometry("980x620")

        self.scraper = SubtitleScraper()
        self.movies = []
        self.subtitles = []

        self._build()

    def _build(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Arama").pack(side="left")
        self.query_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.query_var, width=40).pack(side="left", padx=8)
        ttk.Button(top, text="Ara", command=self.search).pack(side="left")

        ttk.Label(top, text="Dil").pack(side="left", padx=(16, 4))
        self.lang_var = tk.StringVar(value="tr")
        ttk.Combobox(
            top,
            textvariable=self.lang_var,
            values=["tr", "en", "all"],
            state="readonly",
            width=8,
        ).pack(side="left")

        ttk.Label(top, text="Sezon").pack(side="left", padx=(16, 4))
        self.season_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.season_var, width=6).pack(side="left")

        ttk.Label(top, text="Bolum").pack(side="left", padx=(8, 4))
        self.episode_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.episode_var, width=6).pack(side="left")

        body = ttk.Panedwindow(self.root, orient="horizontal")
        body.pack(fill="both", expand=True, padx=10, pady=10)

        left = ttk.Frame(body)
        right = ttk.Frame(body)
        body.add(left, weight=1)
        body.add(right, weight=1)

        ttk.Label(left, text="Filmler").pack(anchor="w")
        self.movie_list = tk.Listbox(left, height=20)
        self.movie_list.pack(fill="both", expand=True)
        self.movie_list.bind("<<ListboxSelect>>", self.load_subtitles)

        ttk.Label(right, text="Altyazilar").pack(anchor="w")
        self.sub_list = tk.Listbox(right, height=20)
        self.sub_list.pack(fill="both", expand=True)

        btns = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        btns.pack(fill="x")
        ttk.Button(btns, text="Secileni indir", command=self.download_selected).pack(side="left")
        ttk.Button(btns, text="Tumunu indir", command=self.download_all).pack(side="left", padx=8)

        self.status_var = tk.StringVar(value="Hazir")
        ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w").pack(
            fill="x", side="bottom"
        )

    def _parse_int(self, value):
        value = (value or "").strip()
        return int(value) if value.isdigit() else None

    def search(self):
        query = self.query_var.get().strip()
        if not query:
            messagebox.showwarning("Uyari", "Arama metni bos olamaz.")
            return
        self.status_var.set("Araniyor...")
        self.root.update_idletasks()
        try:
            self.movies = self.scraper.search(query)
        except Exception as exc:
            messagebox.showerror("Hata", str(exc))
            self.status_var.set("Hata")
            return

        self.movie_list.delete(0, tk.END)
        self.sub_list.delete(0, tk.END)
        self.subtitles = []

        for item in self.movies:
            self.movie_list.insert(tk.END, item["title"])
        self.status_var.set(f"{len(self.movies)} sonuc bulundu")

    def load_subtitles(self, _event=None):
        idxs = self.movie_list.curselection()
        if not idxs:
            return
        movie = self.movies[idxs[0]]
        lang = self.lang_var.get()
        season = self._parse_int(self.season_var.get())
        episode = self._parse_int(self.episode_var.get())

        self.status_var.set("Altyazilar yukleniyor...")
        self.root.update_idletasks()
        try:
            self.subtitles = self.scraper.get_subtitles(
                movie["url"], language=lang, season=season, episode=episode
            )
        except Exception as exc:
            messagebox.showerror("Hata", str(exc))
            self.status_var.set("Hata")
            return

        if self.scraper.last_warning:
            messagebox.showwarning("Uyari", self.scraper.last_warning)

        self.sub_list.delete(0, tk.END)
        for sub in self.subtitles:
            se = ""
            if sub.get("season") is not None and sub.get("episode") is not None:
                se = f"S{sub['season']:02d}E{sub['episode']:02d} "
            release = sub.get("release", "-")
            text = (
                f"[{sub.get('language', 'Unknown')}] {se}{sub['season_ep']} "
                f"- {sub['translator']} - FPS:{sub['fps']} - Release:{release}"
            )
            self.sub_list.insert(tk.END, text)
        self.status_var.set(f"{len(self.subtitles)} altyazi bulundu")

    def download_selected(self):
        idxs = self.sub_list.curselection()
        if not idxs:
            messagebox.showwarning("Uyari", "Bir altyazi secin.")
            return
        sub = self.subtitles[idxs[0]]
        self._download_one(sub)

    def download_all(self):
        if not self.subtitles:
            messagebox.showwarning("Uyari", "Indirilecek altyazi yok.")
            return
        new_count = 0
        skipped = 0
        for sub in self.subtitles:
            _, is_new = self.scraper.download_subtitle(sub["url"], skip_existing=True)
            if is_new:
                new_count += 1
            else:
                skipped += 1
        self.status_var.set(f"Toplu indirme tamamlandi. Yeni:{new_count} Atlanan:{skipped}")
        messagebox.showinfo("Bitti", f"Yeni: {new_count}\nAtlanan: {skipped}")

    def _download_one(self, sub):
        self.status_var.set("Indiriliyor...")
        self.root.update_idletasks()
        try:
            filepath, is_new = self.scraper.download_subtitle(sub["url"], skip_existing=True)
        except Exception as exc:
            messagebox.showerror("Hata", str(exc))
            self.status_var.set("Hata")
            return
        if is_new:
            messagebox.showinfo("Basarili", f"Indirildi:\n{filepath}")
            self.status_var.set("Indirme tamamlandi")
        else:
            messagebox.showinfo("Bilgi", f"Dosya zaten var:\n{filepath}")
            self.status_var.set("Dosya zaten vardi")


def main():
    root = tk.Tk()
    ScraperUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
