import requests
import os
import re
import pygame


SOUND_LIBRARY = {}



def play_sound_from_url(url, download_dir):
    """Download and play a sound file."""
    try:
        os.makedirs(download_dir, exist_ok=True)

        filename = url.split("/")[-1].split("?")[0]
        if not filename.endswith((".ogg", ".mp3", ".wav")):
            filename += ".ogg"

        path = os.path.join(download_dir, filename)

        headers = {"User-Agent": "NovaAssistant/1.0"}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()

        with open(path, "wb") as f:
            f.write(r.content)

        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        sound = pygame.mixer.Sound(path)
        sound.play()

        print(f"[SOUND] Playing → {path}")
        return f"Playing sound: {filename}"

    except Exception as e:
        return f"Sound playback failed: {e}"

SOUND_SEARCH_SITES = [
    "chosic.com",
    "archive.org",
    "freesound.org",
]

SOUND_SEARCH_SITES = [
    "orangefreesounds.com",
    "archive.org",
]


def _best_audio_match(urls, query):
    """Return the URL whose filename best matches the query keywords."""
    keywords = [w for w in query.lower().split()
                if w not in ("sound", "effect", "of", "a", "the", "free")]
    best_url, best_score = None, -1
    for url in urls:
        filename = url.split("/")[-1].lower()
        score = sum(1 for k in keywords if k in filename)
        if score > best_score:
            best_score = score
            best_url = url
    return best_url or (urls[0] if urls else None)


def _extract_audio_urls(text, base_url=""):
    """Extract all audio URLs from plain text (fetch_url returns markdown/text)."""
    audio_pattern = re.compile(
        r'https?://[^\s\'"<>()]+\.(?:mp3|ogg|wav)', re.IGNORECASE
    )
    urls = [m.group(0).rstrip(".,);:\"'") for m in audio_pattern.finditer(text)]

    # Also look for relative paths like /sounds/file.mp3
    if base_url:
        rel_pattern = re.compile(
            r'(?<!["\w])/[^\s\'"<>()]+\.(?:mp3|ogg|wav)', re.IGNORECASE
        )
        domain = "/".join(base_url.split("/")[:3])
        for m in rel_pattern.finditer(text):
            urls.append(domain + m.group(0).rstrip(".,);:\"'"))

    return urls

def _search_for_sound_url(query, internet_tools):
    try:
        clean = query.replace("sound effect", "").replace("sound of", "").strip()

        # ── orangefreesounds — try progressively simpler slugs ────────────
        # "thunder cracking" → try "thunder-cracking", "thunder", first word
        # In _search_for_sound_url, extend the slugs list:
        words = clean.split()
        slugs = [
            clean.replace(" ", "-"),
            clean.replace(" ", "-") + "-sound",
            words[0],  # thunder, rigging, wood
            words[0] + "-sound",
            words[-1],  # cracking, shrieking, splitting
            words[-1] + "-sound",
        ]
        if len(words) > 1:
            slugs.append("-".join(words[:2]))

        for slug in slugs:
            ofs_url = f"https://orangefreesounds.com/{slug}/"
            try:
                print(f"[SOUND] Trying orangefreesounds: {ofs_url}")
                page = internet_tools.fetch_url(ofs_url)
                urls = _extract_audio_urls(page, ofs_url)
                if urls:
                    url = _best_audio_match(urls, clean)
                    print(f"[SOUND] orangefreesounds: {url}")
                    return url
            except Exception as e:
                if "404" in str(e):
                    continue  # try next slug silently
                print(f"[SOUND] orangefreesounds failed: {e}")

        # ── archive.org ───────────────────────────────────────────────────
        results = internet_tools._brave_search(
            f"{clean} sound effect site:archive.org", count=5
        )
        if results:
            details_pattern = re.compile(
                r'https://archive\.org/details/([^\s\'"<>()]+)', re.IGNORECASE
            )
            for m in details_pattern.finditer(results):
                item_id = m.group(1).rstrip(".,);\"'")
                download_url = f"https://archive.org/download/{item_id}/"
                try:
                    print(f"[SOUND] archive.org listing: {download_url}")
                    page = internet_tools.fetch_url(download_url)
                    urls = _extract_audio_urls(page, download_url)

                    if not urls:
                        # archive.org plain text — look for bare filenames
                        file_pattern = re.compile(
                            r'[\w\-\.]+\.(?:mp3|ogg|wav)', re.IGNORECASE
                        )
                        for fm in file_pattern.finditer(page):
                            fname = fm.group(0)
                            if not fname.startswith("http"):
                                urls.append(download_url + fname)

                    if urls:
                        url = _best_audio_match(urls, clean)
                        print(f"[SOUND] archive.org best: {url}")
                        return url

                except Exception as e:
                    print(f"[SOUND] archive.org failed: {e}")
                    continue

        # ── Last resort — Brave direct search ─────────────────────────────
        results = internet_tools._brave_search(
            f'"{clean}" sound effect mp3 free download', count=10
        )
        if results:
            urls = _extract_audio_urls(results)
            if urls:
                url = _best_audio_match(urls, clean)
                print(f"[SOUND] Brave direct: {url}")
                return url

        return None

    except Exception as e:
        print(f"[SOUND] Search error: {e}")
        return None



def search_and_play_sound(query, download_dir, internet_tools=None):
    """
    1. Check hardcoded library (empty by default)
    2. Fall back to internet search for a direct audio URL
    """
    print(f"[SOUND DEBUG] query={query!r}")
    print(f"[SOUND DEBUG] download_dir={download_dir!r}")
    print(f"[SOUND DEBUG] internet_tools={internet_tools!r}")

    query_lower = query.lower().strip()

    # ── 1. Hardcoded library ──────────────────────────────────────────────
    for key in SOUND_LIBRARY:
        if key in query_lower:
            print(f"[SOUND] Library match: {key}")
            return play_sound_from_url(SOUND_LIBRARY[key], download_dir)

    # ── 2. Internet search fallback ───────────────────────────────────────
    if internet_tools is not None:
        print(f"[SOUND] Searching internet for: {query}")
        url = _search_for_sound_url(query_lower, internet_tools)
        if url:
            return play_sound_from_url(url, download_dir)

    return f"Could not find a sound for: {query}"