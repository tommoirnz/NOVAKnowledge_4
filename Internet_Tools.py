"""
internet_tools.py  –  Web-awareness layer for AutoCoder
--------------------------------------------------------
Provides four capabilities:
  1. Weather data  (Open-Meteo, free / no key required)
  2. Web search    (Brave API – uses BRAVE_KEY env var)
  3. URL fetch     (generic page → clean text)
  4. GitHub clone + install

Usage:
  from internet_tools import InternetTools
  tools = InternetTools(log_callback=print)
  ctx   = tools.enrich_task(task_string)
  # ctx is a string block you can prepend to the AI prompt
"""

import os
import re
import json
import subprocess
import textwrap
import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional
try:
    import trafilatura
    _HAS_TRAFILATURA = True
except ImportError:
    _HAS_TRAFILATURA = False
# ---------------------------------------------------------------------------
# Optional deps – import softly so missing packages don't crash the app
# ---------------------------------------------------------------------------
try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

try:
    from bs4 import BeautifulSoup
    _HAS_BS4 = True
except ImportError:
    _HAS_BS4 = False

try:
    import fitz  # PyMuPDF
    _HAS_PYMUPDF = True
except ImportError:
    _HAS_PYMUPDF = False

# ===========================================================================
# DETECTION PATTERNS
# ===========================================================================

_WEATHER_PATTERNS = [
    r'\bweather\b', r'\btemperature\b', r'\bforecast\b', r'\brain\b',
    r'\bhumidity\b', r'\bwind\s*speed\b', r'\bclimate\b',
    r'\bmax\s*temp\b', r'\bmin\s*temp\b', r'\bdegrees?\b',
    r'\bprecipitation\b',
   ]
_ARXIV_PATTERN = r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})'
_ARXIV_ID_PATTERN = r'(?:arxiv:)?(\d{4}\.\d{4,5})'

_SEARCH_PATTERNS = [
    r'\bsearch\s+for\b', r'\blook\s+up\b', r'\bfind\s+info\b',
    r'\blatest\b', r'\bcurrent\b', r'\bnews\b', r'\bwho\s+is\b',
    r'\bwhat\s+is\s+the\s+price\b', r'\bstock\s+price\b',
    r'\bmost\s+common\b', r'\btop\s+\d+\b', r'\bfind\s+the\b',
    r'\blist\s+of\b', r'\bstatistics\b', r'\bdata\s+on\b',
    r'\bpopulation\b', r'\branking\b', r'\bper\s+capita\b',

    ##
    r'\bscore\b',
    r'\bresults?\b',
    r'\bstandings?\b',
    r'\btable\b',
    r'\bwho\s+won\b',
    r'\bmatch\b',
    r'\bgame\b',
    r'\branking\b',
    r'\brugb[y]\b',
    r'\bfootball\b',
    r'\bcricket\b',
    r'\bscottish\b',


    ##
    # ── More ──────────────────────────────────────────
    r'\bsearch\s+the\s+internet\b',
    r'\bfind\s+.*\s+on\s+(github|the\s+internet|online)\b',
    r'\bdownload\s+.*\s+(game|program|app)\b',
    r'\blook\s+online\b',
    r'\bheadlines\b', r'\bbreaking\s+news\b',
    r'\bcost\s+of\b',
    r'\bhow\s+much\b',
    r'\bprice\s+of\b',
    r'\bwhat\s+does\b',
    r'\bfind\s+.*\s+price\b',
    r'\bfind\s+.*\s+cost\b',
    # ───────────────────────────────────────────────────────
]

_GITHUB_PATTERNS = [
    r'github\.com/[^\s]+',
    r'\bclone\s+.*github\b',
    r'\binstall\s+from\s+github\b',
    r'\bdownload\s+.*github\b',
    r'\bgit\s+clone\b',
]

_URL_PATTERNS = [
    r'https?://[^\s]+',
]

# Location words that appear near weather keywords
_LOCATION_STOPWORDS = {
    'the', 'a', 'an', 'in', 'at', 'for', 'over', 'past', 'last',
    'of', 'and', 'or', 'with', 'on', 'from', 'to', 'days', 'week',
    'hours', 'hour', 'day', 'plot', 'show', 'graph', 'chart', 'data',
    'temperature', 'weather', 'forecast', 'degrees', 'max', 'min',
    'search', 'the', 'internet', 'for', 'find', 'get', 'show', 'display',
    'graphically', 'graphical', 'format', 'aesthetically', 'pleasing',
    'and', 'in', 'on', 'of', 'that', 'it', 'is', 'so',
}


# ===========================================================================
class InternetTools:
    """
    Drop-in internet awareness layer.

    Call  enrich_task(task)  before AI code generation – it returns a
    context block (string) that embeds fetched data directly into the
    prompt so the AI writes code that already *has* the numbers.
    """

    def __init__(self, log_callback=None, brave_key: str = None):
        self._log = log_callback or print
        self._brave_key = brave_key or os.getenv("BRAVE_KEY", "")
        self._rate_last = 0.0
        self._rate_min_interval = 1.2
        self.override_image_query = None
        self.override_search_query = None

        self._paper_chunks = {}

    # ------------------------------------------------------------------
    # PUBLIC ENTRY POINT
    # ------------------------------------------------------------------

    def enrich_task(self, task: str) -> str:
        """
        Analyse *task* and return a context block to prepend to the AI prompt.
        Returns an empty string if no internet data is needed.
        """
        self._log(f"[INTERNET] enrich_task triggered for: {task}")
        task_lower = task.lower()
        parts = []

        # --- arXiv paper request ---
        arxiv_id = self._extract_arxiv_id(task)
        self._log(f"[INTERNET] arXiv detected → {arxiv_id}")
        if arxiv_id:
            paper = self._fetch_arxiv(arxiv_id, task)
            if paper:
                parts.append(paper)

        # --- local PDF file request ---
        pdf_match = re.search(r'([A-Za-z0-9_\-\\/:\.]+\.pdf)', task)

        if pdf_match:
            pdf_path = pdf_match.group(1)

            if os.path.exists(pdf_path):
                pdf_text = self._extract_pdf_text(pdf_path)

                if pdf_text:
                    parts.append(
                        f"LOCAL PDF DOCUMENT:\n{pdf_text}"
                    )

        # --- 1. GitHub install request? ---
        gh_urls = self._extract_github_urls(task)

        if gh_urls:
            for url in gh_urls:
                self._log(f"[INTERNET] GitHub URL detected: {url}")
                # If user explicitly asks to install/clone → do install
                if re.search(r'\b(install|clone|download|setup)\b', task.lower()):
                    result = self._github_clone_install(url)

                # Otherwise just read the repository
                else:
                    result = self._fetch_github_readme(url)

                if result:
                    parts.append(result)
        # --- 2. Arbitrary URL to fetch? (non-GitHub) ---
        plain_urls = [
            u for u in self._extract_urls(task)
            if 'github.com' not in u and 'arxiv.org' not in u
        ]
        for url in plain_urls[:2]:           # cap at 2 to avoid prompt bloat
            content = self._fetch_url(url)
            if content:
                parts.append(f"[FETCHED URL: {url}]\n{content[:3000]}\n")

        # --- 2b. Image URLs? Pre-download them ---
        image_urls = [u for u in self._extract_urls(task)
                      if re.search(r'\.(jpg|jpeg|png|gif|webp|bmp)', u, re.I)]
        if image_urls:
            local_paths = []
            for url in image_urls[:5]:
                path = self._fetch_image(url)
                if path:
                    local_paths.append(f"  '{url}' → r'{path}'")
            if local_paths:
                parts.append(
                    "PRE-DOWNLOADED IMAGES (use these local paths instead of URLs):\n" +
                    "\n".join(local_paths) +
                    "\nUse PIL.Image.open(local_path) to load them."
                )

        # ---- IMAGE CONTEXT ----
        # ---- IMAGE CONTEXT ----
        image_dir = "downloaded_images"
        image_keywords = ['image', 'photo', 'picture', 'show', 'display', 'gallery', 'slideshow', 'photograph']

        if os.path.exists(image_dir) and any(kw in task_lower for kw in image_keywords):

            files = [
                f for f in os.listdir(image_dir)
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"))
            ][:6]

            if files:

                image_context = "\nLOCAL IMAGE FILES ALREADY DOWNLOADED\n"
                image_context += "Use these files instead of downloading images again.\n\n"
                image_context += f"Directory: {image_dir}\n\n"

                for f in files:
                    image_context += f"{image_dir}/{f}\n"

                image_context += """
        CRITICAL INSTRUCTION FOR CODE GENERATION:

        If the user asked to see images:
        You MUST display these local image files.

        Do NOT:
        - download new images
        - create placeholder graphics
        - generate synthetic plots

        Load and display these files using:

        from PIL import Image
        import matplotlib.pyplot as plt

        Example:

        img = Image.open("downloaded_images/example.jpg")
        plt.imshow(img)
        plt.axis("off")
        plt.show()

        """

                parts.append(image_context)

        # --- 3. Weather data? ---
        if self._needs_weather(task_lower):
            location = self._extract_location(task) or "Auckland, New Zealand"
            days = self._extract_days(task_lower)
            weather = self._fetch_weather(location, days)
            if weather:
                parts.append(weather)




        # --- 4. Generic web search ---
        # --- 4. Generic web search ---

        # Use override query if set
        if self.override_search_query:

            query = self.override_search_query
            self.override_search_query = None



            if hasattr(self, "internet_indicator_callback"):
                self.internet_indicator_callback(True)

            results = self._brave_search(query)

            if hasattr(self, "internet_indicator_callback"):
                self.internet_indicator_callback(False)

            if results:
                parts.append(results)

        elif self._needs_search(task_lower):

            query = self._extract_search_query(task)

            self._log(f"[INTERNET] 🔍 Brave search: '{query}'")

            if hasattr(self, "internet_indicator_callback"):
                self.internet_indicator_callback(True)

            results = self._brave_search(query)

            if hasattr(self, "internet_indicator_callback"):

                self.internet_indicator_callback(False)

            if results:
                parts.append(results)
################
        elif not parts and self._needs_search(task_lower):

            query = self._extract_search_query(task)

            self._log(f"[INTERNET] 🔍 Brave search: '{query}'")

            if hasattr(self, "internet_indicator_callback"):
                self.internet_indicator_callback(True)

            results = self._brave_search(query)

            if hasattr(self, "internet_indicator_callback"):
                self.internet_indicator_callback(False)


            if results:
                parts.append(results)

            elif self._needs_search(task_lower):

                query = self._extract_search_query(task)

                self._log(f"[INTERNET] 🔍 Brave search: '{query}'")

                if hasattr(self, "internet_indicator_callback"):
                    self.internet_indicator_callback(True)

                results = self._brave_search(query)

                if hasattr(self, "internet_indicator_callback"):
                    self.internet_indicator_callback(False)


                if results:
                    parts.append(results)

        # --- 5. Image search needed? ---
        image_keywords = ['image', 'photo', 'picture', 'show me', 'display image',
                          'slideshow', 'gallery', 'portrait', 'photograph']

        if any(kw in task_lower for kw in image_keywords):
            #################
            query = self.override_image_query or self._extract_search_query(task)
            self.override_image_query = None  # reset after use
            urls = self._brave_image_search(query, count=8)

            seen_urls = set()
            local_paths = []
            for url in urls:
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                path = self._fetch_image(url)
                if path and path not in local_paths:  # Also dedup by local path
                    local_paths.append(f"  r'{path}'")
            if local_paths:
                parts.append(
                    "PRE-DOWNLOADED IMAGES (use these local paths with PIL.Image.open()):\n" +
                    "\n".join(local_paths)
                )
        if not parts:
            return ""

        header = (
                "\n" + "=" * 60 + "\n"
                                  "DOCUMENT CONTEXT (RETRIEVED SOURCE MATERIAL)\n"
                + "=" * 60 + "\n"
                             "The following document excerpts are the source material.\n"
                             "You must answer using ONLY the information below.\n"
                             "Do NOT invent details or substitute another paper.\n"
                             "If the answer is not present in the text, say so.\n\n"
        )
        return header + "\n".join(parts) + "\n" + "=" * 60 + "\n"

    # ------------------------------------------------------------------
    # WEATHER  (Open-Meteo – free, no key)
    # ------------------------------------------------------------------
    def _chunk_text(self, text: str, chunk_size: int = 1200, overlap: int = 200):
        """Split text into overlapping chunks."""
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap

        return chunks

    def _fetch_weather(self, location: str, days: int = 3) -> str:
        """
        Returns a formatted block with historical + forecast temperature
        data for *location* covering the last *days* days.
        """
        if not _HAS_REQUESTS:
            self._log("[INTERNET] requests not installed – skipping weather fetch")
            return ""

        self._log(f"[INTERNET] 🌤 Fetching weather: {location}, {days} days")

        # Step 1: geocode
        lat, lon, resolved = self._geocode(location)
        if lat is None:
            self._log(f"[INTERNET] ❌ Could not geocode '{location}'")
            return ""

        # Step 2: decide date range
        today = datetime.utcnow().date()
        # Open-Meteo archive is available up to yesterday; forecast covers today+
        end_hist   = today - timedelta(days=1)
        start_hist = end_hist - timedelta(days=days - 1)

        # Step 3: historical data (archive endpoint)
        hist_url = "https://archive-api.open-meteo.com/v1/archive"
        hist_params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_hist.isoformat(),
            "end_date": end_hist.isoformat(),
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max",
            "hourly": "relativehumidity_2m",
            "timezone": "auto",
        }

        try:
            r = requests.get(hist_url, params=hist_params, timeout=15)
            r.raise_for_status()
            hist = r.json()
            # Average hourly humidity per day
            hourly_times = hist.get("hourly", {}).get("time", [])
            hourly_humid = hist.get("hourly", {}).get("relativehumidity_2m", [])
            daily_dates = hist.get("daily", {}).get("time", [])
            if hourly_times and hourly_humid and daily_dates:
                daily_humid = []
                for day in daily_dates:
                    day_vals = [hourly_humid[i] for i, t in enumerate(hourly_times) if t.startswith(day)]
                    daily_humid.append(round(sum(day_vals) / len(day_vals), 1) if day_vals else None)
                hist["daily"]["relativehumidity_2m_mean"] = daily_humid
        except Exception as e:
            self._log(f"[INTERNET] ❌ Weather archive error: {e}")
            hist = {}


        # Step 4: today's forecast (forecast endpoint)
        fore_url = "https://api.open-meteo.com/v1/forecast"
        fore_params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max",
            "hourly": "relativehumidity_2m",
            "forecast_days": 1,
            "timezone": "auto",
        }

        try:
            r2 = requests.get(fore_url, params=fore_params, timeout=15)
            r2.raise_for_status()
            fore = r2.json()
            # Average hourly humidity into a daily value
            hourly_humid = fore.get("hourly", {}).get("relativehumidity_2m", [])
            if hourly_humid:
                avg = round(sum(hourly_humid) / len(hourly_humid), 1)
                fore.setdefault("daily", {})["relativehumidity_2m_mean"] = [avg]
        except Exception as e:
            self._log(f"[INTERNET] ⚠ Forecast fetch error: {e}")
            fore = {}


        # Step 5: merge and format
        rows = []

        def _extract_daily(data_json):
            d = data_json.get("daily", {})
            dates = d.get("time", [])
            t_max = d.get("temperature_2m_max", [])
            t_min = d.get("temperature_2m_min", [])
            precip = d.get("precipitation_sum", [])
            wind = d.get("windspeed_10m_max", [])
            return list(zip(
                dates,
                t_max or [None] * len(dates),
                t_min or [None] * len(dates),
                precip or [None] * len(dates),
                wind or [None] * len(dates),
            ))


        for row in _extract_daily(hist):
            rows.append(row)
        for row in _extract_daily(fore):
            if not any(r[0] == row[0] for r in rows):
                rows.append(row)

        if not rows:
            return ""

        lines = [
            f"WEATHER DATA – {resolved}  (lat={lat:.4f}, lon={lon:.4f})",
            f"Source: Open-Meteo archive + forecast (UTC)",
            "",
            f"{'Date':<12}  {'TMax(°C)':>8}  {'TMin(°C)':>8}  {'Rain(mm)':>9}  {'Wind(km/h)':>10}",
            "-" * 56,
        ]
        for date, tmax, tmin, rain, wind in sorted(rows):
            def _f(v): return f"{v:.1f}" if v is not None else "N/A"

            lines.append(f"{date:<12}  {_f(tmax):>8}  {_f(tmin):>8}  {_f(rain):>9}  {_f(wind):>10}")


        # Also emit as Python dict literal for easy copy-paste into code
        py_dates = [r[0] for r in sorted(rows)]
        py_tmax = [r[1] for r in sorted(rows)]
        py_tmin = [r[2] for r in sorted(rows)]
        py_rain = [r[3] for r in sorted(rows)]

        lines += [
            "",
            "# ── Python-ready data ──────────────────────────────────",
            f"weather_location = {json.dumps(resolved)}",
            f"weather_dates    = {json.dumps(py_dates)}",
            f"weather_tmax     = {json.dumps(py_tmax)}",
            f"weather_tmin     = {json.dumps(py_tmin)}",
            f"weather_rain_mm  = {json.dumps(py_rain)}",
            "# ────────────────────────────────────────────────────────",
        ]


        self._log(f"[INTERNET] ✅ Weather data: {len(rows)} rows for {resolved}")
        return "\n".join(lines)

    def _fetch_github_readme(self, repo_url: str):

        if not _HAS_REQUESTS:
            return ""

        try:
            headers = {"User-Agent": "NovaAssistant/1.0"}

            # ── Parse repo URL ──
            parts = repo_url.rstrip("/").split("/")
            user, repo = parts[-2], parts[-1]
            repo = repo.replace(".git", "").strip()

            self._log(f"[INTERNET] Repo parsed → user={user}, repo={repo}")

            # ── Get repository info (to detect default branch) ──
            repo_info_url = f"https://api.github.com/repos/{user}/{repo}"

            self._log(f"[INTERNET] Fetching repo info: {repo_info_url}")

            r = requests.get(repo_info_url, headers=headers, timeout=(5, 10))

            if r.status_code != 200:
                self._log(f"[INTERNET] Repo info request failed: {r.status_code}")
                return ""

            data = r.json()
            branch = data.get("default_branch", "main")

            self._log(f"[INTERNET] Default branch → {branch}")

            # ── Fetch README ──
            readme_url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/README.md"

            self._log(f"[INTERNET] Trying README: {readme_url}")
            self._log("[INTERNET] Requesting README...")

            r = requests.get(readme_url, headers=headers, timeout=(5, 10))

            self._log(f"[INTERNET] README response code: {r.status_code}")

            if r.status_code != 200:
                return ""

            text = r.text

            # save README
            os.makedirs("downloaded_repos", exist_ok=True)

            path = os.path.join("downloaded_repos", f"{repo}_README.md")

            with open(path, "w", encoding="utf-8") as f:
                f.write(text)

            self._log(f"[INTERNET] README saved → {path}")

            # RETURN the README so the AI can read it
            return (
                f"GITHUB REPOSITORY: {repo_url}\n\n"
                f"README CONTENT:\n{text[:4000]}"
            )

        except Exception as e:
            self._log(f"[INTERNET] README fetch error: {e}")

        return ""


    def _extract_pdf_text(self, pdf_path: str, max_chars: int = 12000) -> str:
        """Extract text from a PDF using PyMuPDF."""
        if not _HAS_PYMUPDF:
            self._log("[INTERNET] PyMuPDF not installed – cannot read PDF")
            return ""

        try:
            doc = fitz.open(pdf_path)
            text_parts = []

            for page in doc:
                text_parts.append(page.get_text())

            text = "\n".join(text_parts)
            text = text.strip()

            self._log(f"[INTERNET] 📖 Extracted text from {pdf_path}")

            return text[:max_chars]

        except Exception as e:
            self._log(f"[INTERNET] ❌ PDF extraction failed: {e}")
            return ""

    def _geocode(self, location: str):
        """Return (lat, lon, resolved_name) or (None, None, None)."""
        try:
            r = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": location, "count": 1, "language": "en", "format": "json"},
                timeout=10,
            )
            r.raise_for_status()
            results = r.json().get("results", [])
            if not results:
                return None, None, None
            best = results[0]
            name = best.get("name", location)
            country = best.get("country", "")
            resolved = f"{name}, {country}".strip(", ")
            return best["latitude"], best["longitude"], resolved
        except Exception as e:
            self._log(f"[INTERNET] Geocode error: {e}")
            return None, None, None

    # ------------------------------------------------------------------
    # WEB SEARCH  (Brave)
    # ------------------------------------------------------------------
    def _brave_search(self, query: str, count: int = 6) -> str:

        query = self.override_search_query or query
        self.override_search_query = None

        if not _HAS_REQUESTS:
            return ""

        if not self._brave_key:
            self._log("[INTERNET] No BRAVE_KEY – skipping web search")
            return ""

        # Rate limiting
        elapsed = time.time() - self._rate_last
        if elapsed < self._rate_min_interval:
            time.sleep(self._rate_min_interval - elapsed)

        self._log(f"[INTERNET] 🔍 Brave search: '{query}'")

        try:
            r = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={
                    "X-Subscription-Token": self._brave_key,
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "User-Agent": "AutoCoder/2.0"
                },
                params={"q": query, "count": count},
                timeout=20,
            )

            self._rate_last = time.time()
            r.raise_for_status()
            data = r.json()

        except Exception as e:
            self._log(f"[INTERNET] ❌ Brave search error: {e}")
            return ""

        hits = data.get("web", {}).get("results", [])

        if not hits:
            return ""

        lines = [f"WEB SEARCH RESULTS for: {query}", ""]

        for i, h in enumerate(hits, 1):
            lines.append(f"{i}. {h.get('title', '')}")

            url = h.get("link")

            # fallback only if it looks like a real URL
            if not url or len(url) < 15:
                fallback = h.get("url") or h.get("display_url")
                if fallback and fallback.startswith("http") and len(fallback) > 20:
                    url = fallback
                else:
                    url = "[no valid URL]"

            lines.append(f"   URL: {url}")
            lines.append(f"   {h.get('description', h.get('snippet', ''))}")
            lines.append("")

        self._log(f"[INTERNET] ✅ {len(hits)} search results")

        # ---------------------------------------------------------
        # Fetch content from up to 3 unique domains
        # ---------------------------------------------------------

        seen_domains = set()
        bad_domains = ["twitter", "x.com", "facebook", "instagram", "pinterest"]

        for h in hits:

            url = h.get("url", "")

            if not url:
                continue

            # Skip social media
            if any(b in url.lower() for b in bad_domains):
                continue

            try:
                domain = url.split("/")[2]
            except Exception:
                continue

            # Avoid duplicate domains
            if domain in seen_domains:
                continue

            seen_domains.add(domain)

            if len(seen_domains) > 3:
                break

            try:

                page = requests.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=10
                )

                if page.status_code != 200:
                    continue

                # Skip extremely large pages
                if len(page.text) > 2_000_000:
                    self._log(f"[INTERNET] ⚠️ Page too large, skipping: {url}")
                    continue

                # ---------------------------------------------
                # Extract main article text
                # ---------------------------------------------

                clean = None

                if _HAS_TRAFILATURA:
                    try:
                        clean = trafilatura.extract(page.text)
                    except Exception:
                        clean = None

                # Fallback extraction
                if not clean:

                    soup = BeautifulSoup(page.text, "html.parser")

                    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                        tag.decompose()

                    clean = soup.get_text(" ", strip=True)

                clean = re.sub(r"\s+", " ", clean).strip()

                # Skip low-content pages
                if len(clean) < 200:
                    self._log(f"[INTERNET] ⚠️ Skipping low-content page: {url}")
                    continue

                lines.append(f"\nFULL PAGE CONTENT ({url}):")
                lines.append(clean[:5000])

                self._log(f"[INTERNET] 📄 Fetched page: {url}")

            except Exception as e:

                self._log(f"[INTERNET] ⚠️ Could not fetch page: {e}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # URL FETCH
    # ------------------------------------------------------------------
    def fetch_url(self, url: str, max_chars: int = 4000) -> str:
        """Public wrapper so agents can call internet.fetch_url()."""
        return self._fetch_url(url, max_chars)

    def _clean_url(self, url: str) -> str:
        """Remove punctuation accidentally attached to URLs."""
        url = url.strip()

        # Remove common trailing punctuation
        while url and url[-1] in '.,;:!?\'"`':
            url = url[:-1]

        # Remove unmatched closing brackets
        if url.endswith(")") and url.count("(") < url.count(")"):
            url = url[:-1]

        if url.endswith("]") and url.count("[") < url.count("]"):
            url = url[:-1]

        if url.endswith("}") and url.count("{") < url.count("}"):
            url = url[:-1]

        return url

    def _fetch_url(self, url: str, max_chars: int = 4000) -> str:
        """Fetch a URL and return cleaned text."""

        # ---------------------------------------------------------
        # Fix model formatting mistakes (e.g. "url: https://...")
        # ---------------------------------------------------------
        if url.lower().startswith("url:"):
            url = url[4:].strip()

        if url.lower().startswith("link:"):
            url = url[5:].strip()

        url = url.strip()

        if not _HAS_REQUESTS:
            return "FETCH_ERROR: requests library not available"

        self._log(f"[INTERNET] 🌐 Fetching URL: {url}")

        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=20)
            r.raise_for_status()

            content_type = r.headers.get("content-type", "").lower()

            # ---------------------------------------------------------
            # PDF handling
            # ---------------------------------------------------------
            if "pdf" in content_type or url.lower().endswith(".pdf"):

                if not _HAS_PYMUPDF:
                    self._log("[INTERNET] PyMuPDF not installed – cannot read PDF")
                    return "PDF_ERROR: PyMuPDF not installed"

                os.makedirs("downloaded_papers", exist_ok=True)

                name = os.path.basename(url.split("?")[0])

                if not name.lower().endswith(".pdf"):
                    name = f"{name}.pdf"

                filename = os.path.join("downloaded_papers", name)

                with open(filename, "wb") as f:
                    f.write(r.content)

                self._log(f"[INTERNET] 📥 Downloaded PDF: {filename}")

                text = self._extract_pdf_text(filename, max_chars)

                if not text.strip():
                    self._log("[INTERNET] ⚠ PDF contained no extractable text")

                return text

            # ---------------------------------------------------------
            # JSON
            # ---------------------------------------------------------
            if "json" in content_type:
                return json.dumps(r.json(), indent=2)[:max_chars]

            # ---------------------------------------------------------
            # HTML
            # ---------------------------------------------------------
            if "html" in content_type and _HAS_BS4:

                soup = BeautifulSoup(r.text, "html.parser")

                for tag in soup(["script", "style", "nav", "footer"]):
                    tag.decompose()

                text = soup.get_text(separator="\n", strip=True)

                text = re.sub(r"\n{3,}", "\n\n", text)

                return text[:max_chars]

            # ---------------------------------------------------------
            # Fallback
            # ---------------------------------------------------------
            return r.text[:max_chars]

        except Exception as e:
            self._log(f"[INTERNET] ❌ Fetch error: {e}")
            return f"FETCH_ERROR: {e}"

    # ------------------------------------------------------------------
    # GITHUB CLONE + INSTALL
    # ------------------------------------------------------------------
    def _github_clone_install(self, url: str) -> str:
        """
        Clone a GitHub repo and attempt to install it.
        Returns a summary string.
        """
        self._log(f"[INTERNET] 📦 GitHub install: {url}")

        # Normalise URL (strip .git, trailing slash)
        url = url.rstrip("/")
        if not url.endswith(".git"):
            clone_url = url + ".git"
        else:
            clone_url = url

        # Derive folder name
        repo_name = url.rstrip("/").split("/")[-1].replace(".git", "")
        install_dir = os.path.join(os.getcwd(), "github_packages", repo_name)

        lines = [f"GITHUB PACKAGE: {url}", f"Local path: {install_dir}"]

        # --- clone ---
        if os.path.exists(install_dir):
            self._log(f"[INTERNET] Repo already cloned at {install_dir}, pulling latest...")
            result = subprocess.run(
                ["git", "-C", install_dir, "pull"],
                capture_output=True, text=True, timeout=60
            )
            lines.append(f"git pull: {result.stdout.strip() or result.stderr.strip()}")
        else:
            os.makedirs(os.path.dirname(install_dir), exist_ok=True)
            self._log(f"[INTERNET] Cloning into {install_dir}...")
            result = subprocess.run(
                ["git", "clone", clone_url, install_dir],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode != 0:
                self._log(f"[INTERNET] ❌ Clone failed: {result.stderr[:300]}")
                lines.append(f"ERROR cloning: {result.stderr[:300]}")
                return "\n".join(lines)
            lines.append("git clone: SUCCESS")

        # --- install ---
        pip_target = None
        if os.path.exists(os.path.join(install_dir, "setup.py")):
            pip_target = install_dir
        elif os.path.exists(os.path.join(install_dir, "pyproject.toml")):
            pip_target = install_dir

        if pip_target:
            self._log(f"[INTERNET] pip installing {pip_target}...")
            result = subprocess.run(
                ["pip", "install", "-e", pip_target, "--quiet"],
                capture_output=True, text=True, timeout=180
            )
            if result.returncode == 0:
                lines.append("pip install -e .: SUCCESS")
            else:
                lines.append(f"pip install WARNING: {result.stderr[:200]}")
        else:
            req = os.path.join(install_dir, "requirements.txt")
            if os.path.exists(req):
                result = subprocess.run(
                    ["pip", "install", "-r", req, "--quiet"],
                    capture_output=True, text=True, timeout=180
                )
                lines.append(
                    f"pip install -r requirements.txt: {'SUCCESS' if result.returncode == 0 else result.stderr[:200]}")

        # --- find entry point ---
        entry_point = None
        for candidate in ["main.py", "run.py", "app.py", "__main__.py"]:
            if os.path.exists(os.path.join(install_dir, candidate)):
                entry_point = os.path.join(install_dir, candidate)
                break

        lines.append(f"Import path ready: import sys; sys.path.insert(0, r'{install_dir}')")
        lines.append(f"INSTRUCTION: Do NOT rewrite this program. Run the existing files directly using subprocess.")

        if entry_point:
            lines.append(f"RUN WITH: import subprocess, sys; subprocess.run([sys.executable, r'{entry_point}'])")
        else:
            lines.append(f"ENTRY POINT UNKNOWN - first list files with: import os; print(os.listdir(r'{install_dir}'))")
            lines.append(
                f"Then run the correct .py file with: subprocess.run([sys.executable, r'{install_dir}\\FILENAME.py'])")

        self._log(f"[INTERNET] ✅ GitHub install done: {repo_name}")
        return "\n".join(lines)

    def fetch_js_url(self, url, wait_for="networkidle", timeout=15000):
        """Fetch a JavaScript-rendered page using Playwright headless browser."""
        try:

            from playwright.async_api import async_playwright

            async def _fetch():
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    await page.set_extra_http_headers({
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    })
                    await page.goto(url, timeout=timeout)
                    # Wait for actual content to appear rather than just network idle
                    try:
                        await page.wait_for_selector("body", timeout=10000)
                        await page.wait_for_timeout(3000)  # Extra 3s for JS rendering
                    except:
                        pass
                    content = await page.content()
                    await browser.close()
                    return content


            # Run async in a new event loop (safe from tkinter thread)
            loop = asyncio.new_event_loop()
            html = loop.run_until_complete(_fetch())
            loop.close()

            # Strip HTML tags and return clean text
            clean = re.sub(r'<[^>]+>', ' ', html)
            clean = re.sub(r'\s+', ' ', clean).strip()
            if self._log:
                self._log(f"[JS FETCH] {url} → {len(clean)} chars")
            return clean[:8000]

        except Exception as e:
            if self._log:
                self._log(f"[JS FETCH ERROR] {e}")
            return ""


    def _fetch_image(self, url: str, save_dir: str = "downloaded_images") -> Optional[str]:
        """Download an image and return the local file path."""
        if not _HAS_REQUESTS:
            return None
        try:
            os.makedirs(save_dir, exist_ok=True)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                "Referer": url,
            }



            # Derive filename from URL - strip query params and trailing slashes
            url_path = url.split("?")[0].rstrip("/")
            basename = url_path.split("/")[-1]

            # Get extension from basename if it has one, otherwise from url_path
            if "." in basename:
                ext = basename.split(".")[-1][:4] or "jpg"
                name = basename.rsplit(".", 1)[0]
            else:
                ext = url_path.split(".")[-1][:4] or "jpg"
                name = basename

            # Clean the name
            name = re.sub(r'[^\w]', '_', name)[:50]
            if not name:
                name = re.sub(r'[^\w]', '_', url)[:40]

            filename = f"{name}.{ext}"
            # Final safety - remove any slashes or invalid Windows chars that slipped through
            filename = re.sub(r'[/\\:*?"<>|]', '_', filename)
            local_path = os.path.join(save_dir, filename)

            # Skip if already downloaded and non-empty
            if os.path.exists(local_path) and os.path.getsize(local_path) > 1000:
                self._log(f"[INTERNET] 🖼 Already have: {local_path} - skipping")
                return local_path

            r = requests.get(url, headers=headers, timeout=25)
            r.raise_for_status()

            # Check content is actually an image
            content_type = r.headers.get("content-type", "")
            if "image" not in content_type and "octet-stream" not in content_type:
                self._log(f"[INTERNET] ⚠️ Not an image ({content_type}): {url}")
                return None

            with open(local_path, "wb") as f:
                f.write(r.content)

            # Verify file is reasonably sized
            if os.path.getsize(local_path) < 1000:
                os.remove(local_path)
                self._log(f"[INTERNET] ⚠️ Image too small (probably error page): {url}")
                return None

            self._log(f"[INTERNET] 🖼 Downloaded image: {local_path}")
            return local_path
        except Exception as e:
            self._log(f"[INTERNET] ❌ Image download failed: {e}")
            return None


    # ------------------------------------------------------------------
    # DETECTION HELPERS
    # ------------------------------------------------------------------

    def _needs_weather(self, task_lower: str) -> bool:
        return any(re.search(p, task_lower) for p in _WEATHER_PATTERNS)

    def _needs_search(self, task_lower: str) -> bool:
        return any(re.search(p, task_lower) for p in _SEARCH_PATTERNS)

    def _extract_github_urls(self, task: str) -> list:
        found = []
        for m in re.finditer(r'https?://github\.com/[^\s\'")\]]+', task):
            found.append(m.group(0).rstrip(".,"))
        # Also bare form: github.com/user/repo
        for m in re.finditer(r'(?<!\w)github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)', task):
            url = "https://" + m.group(0).rstrip(".,")
            if url not in found:
                found.append(url)
        return found

    def _extract_urls(self, task: str) -> list:
        urls = []

        for m in re.finditer(r'https?://[^\s"`]+', task):
            url = m.group(0)

            # Strip punctuation
            url = url.rstrip(".,;:!?")
            url = url.rstrip("'\"`")

            # Remove unmatched brackets
            if url.endswith(")") and url.count("(") < url.count(")"):
                url = url[:-1]

            if url.endswith("]") and url.count("[") < url.count("]"):
                url = url[:-1]

            if url.endswith("}") and url.count("{") < url.count("}"):
                url = url[:-1]

            urls.append(url)

        return urls

    def _extract_arxiv_id(self, text: str):
        text = text.lower()

        # arxiv:2603.05875
        m = re.search(r'arxiv[:\s]*(\d{4}\.\d{4,5})', text)
        if m:
            return m.group(1)

        # arxiv.org links
        m = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})', text)
        if m:
            return m.group(1)

        # plain id
        m = re.search(r'\b(\d{4}\.\d{4,5})\b', text)
        if m:
            return m.group(1)

        return None

    def _fetch_arxiv(self, arxiv_id: str, query: str = "") -> str:
        if not _HAS_REQUESTS:
            return ""

        self._log(f"[INTERNET] 📄 Fetching arXiv: {arxiv_id}")

        try:
            # ── Fetch metadata ─────────────────────────────
            url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
            r = requests.get(url, timeout=15)
            r.raise_for_status()

            if not _HAS_BS4:
                return ""

            soup = BeautifulSoup(r.text, "xml")
            entry = soup.find("entry")

            if not entry:
                return ""

            title = entry.title.text.strip()
            abstract = entry.summary.text.strip()

            authors = [a.find("name").text for a in entry.find_all("author")]

            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            # ── Prepare storage ────────────────────────────
            os.makedirs("downloaded_papers", exist_ok=True)
            pdf_path = f"downloaded_papers/{arxiv_id}.pdf"

            pdf_text = ""

            try:
                # ── Download PDF (robust) ───────────────────
                need_download = (
                        not os.path.exists(pdf_path)
                        or os.path.getsize(pdf_path) < 5000
                )

                if need_download:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                        "Accept": "application/pdf"
                    }

                    pdf = requests.get(pdf_url, headers=headers, timeout=20)
                    content_type = pdf.headers.get("content-type", "").lower()

                    if (
                            pdf.status_code == 200
                            and "pdf" in content_type
                            and len(pdf.content) > 5000
                    ):
                        with open(pdf_path, "wb") as f:
                            f.write(pdf.content)

                        self._log(
                            f"[INTERNET] 📥 Downloaded PDF: {pdf_path} "
                            f"({len(pdf.content)} bytes)"
                        )
                    else:
                        self._log(
                            f"[INTERNET] ❌ Bad PDF response: "
                            f"status={pdf.status_code}, "
                            f"type={content_type}, "
                            f"size={len(pdf.content)}"
                        )
                        pdf_path = None

                # ── Extract text ────────────────────────────
                if _HAS_PYMUPDF and pdf_path and os.path.exists(pdf_path):

                    if arxiv_id not in self._paper_chunks:

                        pdf_text = self._extract_pdf_text(pdf_path)

                        if pdf_text.strip():
                            chunks = self._chunk_text(pdf_text)
                            self._paper_chunks[arxiv_id] = chunks
                            self._log(f"[INTERNET] 📚 Stored {len(chunks)} paper chunks")
                        else:
                            self._log("[INTERNET] ⚠ Empty PDF text — removing and retrying next time")
                            os.remove(pdf_path)
                            pdf_path = None

            except Exception as e:
                self._log(f"[INTERNET] ⚠ PDF processing failed: {e}")
                pdf_path = None

            # ── Build output ───────────────────────────────
            lines = [
                f"ARXIV PAPER: {arxiv_id}",
                f"Title: {title}",
                f"Authors: {', '.join(authors)}",
                "",
                "ABSTRACT:",
                abstract,
                "",
                f"PDF: {pdf_url}",
            ]

            relevant = self._search_paper(arxiv_id, query)

            if relevant:
                lines += ["", "RELEVANT SECTIONS FROM PAPER:"]
                for chunk in relevant:
                    lines.append(chunk[:1500])

            if pdf_path:
                lines.append(f"Local PDF: {pdf_path}")

            return "\n".join(lines)

        except Exception as e:
            self._log(f"[INTERNET] ❌ arXiv fetch error: {e}")
            return ""
    def _search_paper(self, arxiv_id: str, query: str, top_k: int = 3):
        """Return the most relevant chunks for a query."""
        chunks = self._paper_chunks.get(arxiv_id, [])

        if not chunks:
            return []

        query_words = set(re.findall(r'\b\w+\b', query.lower()))

        scored = []
        for chunk in chunks:
            words = set(chunk.lower().split())
            score = len(query_words & words)
            scored.append((score, chunk))

        scored.sort(reverse=True)

        return [c for s, c in scored[:top_k] if s > 0]

    def _extract_location(self, task: str):

        # look for "in X", "for X", etc.
        m = re.search(r'\b(?:in|for|at)\s+([A-Z][A-Za-z\s]{2,40})', task)

        if m:
            loc = m.group(1).strip()
            loc = re.sub(r'^the\s+', '', loc, flags=re.I)
            return loc

        # fallback: two capitalised words
        m2 = re.search(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b', task)

        if m2:
            return m2.group(1)

        return None


    def _extract_days(self, task_lower: str) -> int:
        """Extract number of days from phrases like 'past 3 days', 'last week'."""
        m = re.search(r'(?:past|last|previous)\s+(\d+)\s+days?', task_lower)
        if m:
            return min(int(m.group(1)), 30)   # cap at 30
        if re.search(r'(?:past|last|previous)\s+week', task_lower):
            return 7
        if re.search(r'(?:past|last|previous)\s+month', task_lower):
            return 30
        m2 = re.search(r'(\d+)\s+days?', task_lower)
        if m2:
            return min(int(m2.group(1)), 30)
        return 3   # default

    def _extract_search_query(self, task: str) -> str:
        stopwords = {
            # Common task verbs
            'search', 'find', 'get', 'show', 'display', 'put', 'make',
            'create', 'build', 'write', 'look', 'fetch', 'retrieve',
            # Filler words
            'the', 'internet', 'online', 'for', 'and', 'or', 'in', 'on',
            'of', 'that', 'it', 'is', 'so', 'an', 'a', 'me', 'my', 'i',
            'with', 'from', 'to', 'into', 'by', 'up', 'out', 'then',
            # Technical implementation words
            'opengl', 'open-gl', 'rotating', 'cube', 'slideshow', 'gallery',
            'graphically', 'graphical', 'format', 'aesthetically', 'pleasing',
            'matplotlib', 'pygame', 'pillow', 'python', 'code', 'program',
            'animation', 'animated', '3d', 'texture', 'textured', 'using',
            'graph', 'chart', 'plot', 'visualize', 'visualise',
            # Creative brief document words
            'overview', 'vision', 'description', 'board', 'living', 'philosophy',
            'concept', 'design', 'layout', 'style', 'theme', 'approach',
            'image', 'images', 'photo', 'photos', 'cool', 'sound',
            'portrait', 'dramatic', 'beautiful', 'stunning', 'serene',
            'opens', 'program', 'user', 'screen', 'window', 'experience',
            'them', 'some', 'effects', 'effect', 'pictures', 'picture',
            'dramatic', 'stunning', 'beautiful', 'serene', 'opens',
            'discover', 'discovery', 'journey', 'experience',
        }

        words = task.lower().split()
        filtered = [w for w in words if w not in stopwords and len(w) > 2]
        return ' '.join(filtered[:8])



    def _brave_image_search(self, query: str, count: int = 5) -> list:
        """Search for images using Brave image search API. Returns list of image URLs."""
        if not _HAS_REQUESTS or not self._brave_key:
            return []

        self._log(f"[INTERNET] 🖼 Brave image search: '{query}'")

        try:
            r = requests.get(
                "https://api.search.brave.com/res/v1/images/search",
                headers={
                    "X-Subscription-Token": self._brave_key,
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                },
                params={"q": query, "count": count},
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            self._log(f"[INTERNET] ❌ Brave image search error: {e}")
            return []

        results = data.get("results", [])
        seen = set()
        urls = []
        for r in results:
            url = r.get("properties", {}).get("url")
            if url and url not in seen:
                seen.add(url)
                urls.append(url)
        self._log(f"[INTERNET] ✅ Found {len(urls)} unique image URLs")
        return urls

