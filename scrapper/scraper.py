import os
import random
import re
import time
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class SubtitleScraper:
    def __init__(self, base_url="https://turkcealtyazi.org/"):
        self.base_url = base_url
        self.session = requests.Session()
        self._last_request_at = 0.0
        self._min_request_interval = 1.2  # etik/hafif tempo
        self._cache = {}
        self.last_warning = None
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            }
        )

    def _respectful_sleep(self):
        now = time.time()
        wait = self._min_request_interval - (now - self._last_request_at)
        if wait > 0:
            # sabit pattern yerine az jitter
            time.sleep(wait + random.uniform(0.05, 0.35))

    def _request(self, method, url, params=None, data=None, timeout=25, allow_redirects=True):
        key = (
            method.upper(),
            url,
            tuple(sorted((params or {}).items())),
            tuple(sorted((data or {}).items())),
        )
        if method.upper() == "GET" and key in self._cache:
            return self._cache[key]

        last_exc = None
        for attempt in range(3):
            try:
                self._respectful_sleep()
                resp = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    timeout=timeout,
                    allow_redirects=allow_redirects,
                )
                self._last_request_at = time.time()
                if resp.status_code in (429, 500, 502, 503, 504):
                    time.sleep((attempt + 1) * 1.5)
                    continue
                if method.upper() == "GET":
                    self._cache[key] = resp
                return resp
            except requests.RequestException as exc:
                last_exc = exc
                time.sleep((attempt + 1) * 1.5)

        if last_exc:
            raise last_exc
        raise Exception("Istek basarisiz")

    def _extract_movie_results(self, html):
        soup = BeautifulSoup(html, "lxml")
        seen = set()
        results = []

        for link in soup.find_all("a", href=True):
            href = (link.get("href") or "").strip()
            title = link.get_text(strip=True)
            if "/mov/" not in href or not title:
                continue

            full_url = urljoin(self.base_url, href)
            if full_url in seen:
                continue
            seen.add(full_url)
            results.append({"title": title, "url": full_url})

        return results

    def _normalize_text(self, text):
        return re.sub(r"\s+", " ", (text or "").strip().lower())

    def _score_result(self, query, title, url):
        q = self._normalize_text(query)
        t = self._normalize_text(title)
        slug = self._normalize_text(urlparse(url).path.split("/")[-1].replace(".html", "").replace("-", " "))

        score = 0

        # En güçlü sinyaller
        if t == q:
            score += 1000
        if slug == q:
            score += 900
        if t.startswith(q + " "):
            score += 250
        if slug.startswith(q + " "):
            score += 220

        # Kelime bazlı eşleşme (tam kelime öncelikli)
        q_words = [w for w in q.split(" ") if w]
        t_words = set(re.findall(r"[a-z0-9]+", t))
        s_words = set(re.findall(r"[a-z0-9]+", slug))
        for w in q_words:
            if w in t_words:
                score += 70
            elif w in t:
                score += 25

            if w in s_words:
                score += 60
            elif w in slug:
                score += 20

        # Tüm query metni geçiyorsa ekstra puan
        if q and q in t:
            score += 120
        if q and q in slug:
            score += 100

        # Çok uzun/alakasız başlıkları az biraz kırp
        score -= max(0, len(t_words) - max(2, len(q_words))) * 2
        return score

    def search(self, query):
        collected = []

        def collect(results):
            for r in results:
                sc = self._score_result(query, r["title"], r["url"])
                if sc > 0:
                    collected.append(
                        {"title": r["title"], "url": r["url"], "_score": sc}
                    )

        # 1) Asil endpoint
        find_url = urljoin(self.base_url, "find.php")
        trials = [
            {"cat": "sub", "find": query},
            {"find": query},
            {"cat": "all", "find": query},
        ]

        for params in trials:
            resp = self._request("GET", find_url, params=params, timeout=25)
            if resp.status_code != 200:
                continue
            resp.encoding = resp.apparent_encoding or resp.encoding
            results = self._extract_movie_results(resp.text)
            if results:
                collect(results)

        # 2) Eski endpoint fallback
        search_url = urljoin(self.base_url, "search.php")
        resp = self._request(
            "POST",
            search_url,
            data={"search": query, "submit": "Ara"},
            timeout=25,
        )
        if resp.status_code == 200:
            resp.encoding = resp.apparent_encoding or resp.encoding
            results = self._extract_movie_results(resp.text)
            if results:
                collect(results)

        # 3) Harici fallback (DDG): sadece site içi arama boş kaldıysa dene.
        if not collected:
            ddg = self._request(
                "GET",
                "https://duckduckgo.com/html/",
                params={"q": f"site:turkcealtyazi.org/mov/ {query}"},
                timeout=25,
            )
            if ddg.status_code == 200:
                soup = BeautifulSoup(ddg.text, "lxml")
                seen = set()
                added = 0

                for link in soup.find_all("a", href=True):
                    href = (link.get("href") or "").strip()
                    title = link.get_text(strip=True)
                    if not href:
                        continue

                    target_url = href
                    if "duckduckgo.com/l/" in href:
                        parsed = urlparse(href)
                        uddg = parse_qs(parsed.query).get("uddg")
                        if uddg:
                            target_url = unquote(uddg[0])

                    if "turkcealtyazi.org/mov/" not in target_url:
                        continue
                    if target_url in seen:
                        continue

                    seen.add(target_url)
                    item_title = title or target_url
                    sc = self._score_result(query, item_title, target_url)
                    if sc > 0:
                        collected.append(
                            {"title": item_title, "url": target_url, "_score": sc}
                        )
                        added += 1
                        if added >= 20:
                            break

        if not collected:
            return []

        # URL bazlı unique + skor sıralama
        best_by_url = {}
        for item in collected:
            u = item["url"]
            if u not in best_by_url or item["_score"] > best_by_url[u]["_score"]:
                best_by_url[u] = item

        ranked = sorted(best_by_url.values(), key=lambda x: x["_score"], reverse=True)
        return [{"title": x["title"], "url": x["url"]} for x in ranked[:10]]

    def _extract_language(self, row):
        lang_div = row.find("div", class_="aldil")
        if not lang_div:
            return ("unknown", "Unknown")

        # Sitede genelde <span class="flagtr"> gibi tutuluyor.
        span = lang_div.find("span")
        classes = span.get("class", []) if span else []
        code = None
        for cls in classes:
            if cls.startswith("flag") and len(cls) >= 6:
                code = cls[4:].lower()
                break

        if not code:
            text = lang_div.get_text(" ", strip=True).lower()
            if "turk" in text:
                code = "tr"
            elif "english" in text or "ingiliz" in text:
                code = "en"
            else:
                code = "unknown"

        labels = {
            "tr": "Turkce",
            "en": "Ingilizce",
        }
        return (code, labels.get(code, code.upper() if code != "unknown" else "Unknown"))

    def get_subtitles(self, movie_url, language="all", season=None, episode=None):
        self.last_warning = None
        response = self._request("GET", movie_url, timeout=25)
        if response.status_code != 200:
            raise Exception(f"Sayfa yuklenemedi: {response.status_code}")

        soup = BeautifulSoup(response.text, "lxml")
        subtitles = []
        # Her altyazı satırı .altsonsez* bloklarında duruyor.
        row_selectors = [
            "div[class*='altsonsez']",
            "div[class*='row-class']",
        ]
        rows = []
        for sel in row_selectors:
            rows = soup.select(sel)
            if rows:
                break
        if not rows:
            # Selector kirilmasi kontrolu
            sub_links = soup.find_all("a", href=lambda h: h and "/sub/" in h)
            if sub_links:
                self.last_warning = (
                    "UYARI: Altyazi satir selectoru degismis olabilir. "
                    "Fallback parse devreye alinmali."
                )
            else:
                self.last_warning = (
                    "UYARI: Sayfada altyazi linki bulunamadi. "
                    "Site yapisi degismis olabilir veya kayit yok."
                )

        seen = set()
        for row in rows:
            link_tag = row.find("a", href=lambda h: h and "/sub/" in h)
            if not link_tag:
                continue
            full_link = urljoin(self.base_url, link_tag["href"])
            if full_link in seen:
                continue
            seen.add(full_link)

            title = link_tag.get_text(strip=True)
            lang_code, lang_label = self._extract_language(row)
            selected_lang = (language or "all").lower()
            if selected_lang in ("tr", "en") and lang_code != selected_lang:
                continue

            cd = row.find("div", class_="alcd")
            cd_text = cd.get_text(" ", strip=True) if cd else "-"
            season_ep_match = re.search(r"S\s*0?(\d+)\s*\|\s*E\s*0?(\d+)", cd_text, flags=re.IGNORECASE)
            row_season = int(season_ep_match.group(1)) if season_ep_match else None
            row_episode = int(season_ep_match.group(2)) if season_ep_match else None
            if season is not None and row_season != season:
                continue
            if episode is not None and row_episode != episode:
                continue

            fps = row.find("div", class_="alfps")
            downloads = row.find("div", class_="alindirme")
            translator = row.find("div", class_="alcevirmen")

            subtitles.append(
                {
                    "season_ep": title,
                    "translator": (
                        (translator.get_text(" ", strip=True) or "-")
                        if translator
                        else "-"
                    ),
                    "fps": fps.get_text(" ", strip=True) if fps else "-",
                    "downloads": downloads.get_text(" ", strip=True) if downloads else "-",
                    "cd": cd_text,
                    "season": row_season,
                    "episode": row_episode,
                    "language": lang_label,
                    "language_code": lang_code,
                    "url": full_link,
                }
            )

        return subtitles

    def download_subtitle(self, sub_url, save_path="downloads", skip_existing=True):
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        response = self._request("GET", sub_url, timeout=25, allow_redirects=True)
        if response.status_code != 200:
            raise Exception(f"Altyazi sayfasi yuklenemedi: {response.status_code}")

        def filename_from_headers(resp):
            cd = resp.headers.get("content-disposition", "")
            m = re.search(r'filename="?([^";]+)"?', cd, flags=re.IGNORECASE)
            if m:
                return m.group(1).strip()
            return None

        def save_response_content(resp, default_name):
            filename = filename_from_headers(resp)
            if not filename:
                path_name = urlparse(resp.url).path.split("/")[-1]
                filename = path_name or default_name
            filepath = os.path.join(save_path, filename)
            if skip_existing and os.path.exists(filepath):
                return filepath, False
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return filepath, True

        content_type = (response.headers.get("content-type") or "").lower()
        if "application/octet-stream" in content_type or "application/zip" in content_type:
            return save_response_content(response, "subtitle.zip")

        soup = BeautifulSoup(response.text, "lxml")

        # TurkceAltyazi'da indirme genelde /ind endpoint'ine POST formu ile yapiliyor.
        ind_form = soup.find("form", action=lambda a: a and "/ind" in a)
        if ind_form:
            action_url = urljoin(self.base_url, ind_form.get("action", "/ind"))
            payload = {}
            for inp in ind_form.find_all("input"):
                name = inp.get("name")
                if name:
                    payload[name] = inp.get("value", "")

            ind_resp = self._request("POST", action_url, data=payload, timeout=25, allow_redirects=True)
            if ind_resp.status_code == 200:
                ind_ct = (ind_resp.headers.get("content-type") or "").lower()
                if "application/octet-stream" in ind_ct or "application/zip" in ind_ct:
                    return save_response_content(ind_resp, "subtitle.zip")
                if "text/plain" in ind_ct or "application/x-subrip" in ind_ct:
                    return save_response_content(ind_resp, "subtitle.srt")

        # Fallback: direkt indirilebilir link ara.
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            if any(x in href for x in ["/download", ".zip", ".srt"]):
                file_url = urljoin(self.base_url, a["href"])
                file_resp = self._request("GET", file_url, timeout=25, allow_redirects=True)
                if file_resp.status_code == 200:
                    return save_response_content(file_resp, "subtitle.zip")

        raise Exception("Indirme linki bulunamadi")
