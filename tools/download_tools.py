import requests
import os


def download_file(url, download_dir="downloads"):
    """
    Download a file from a URL and save it to the downloads directory.
    """
    import re

    if not re.match(r"https?://", url):
        return "Error: download_file requires a valid URL"

    print("[DOWNLOAD] Directory:", download_dir)

    try:

        os.makedirs(download_dir, exist_ok=True)

        filename = url.split("/")[-1].split("?")[0]

        if not filename:
            filename = "downloaded_file"

        # 🔥 FIX arXiv + missing extensions
        if "arxiv.org/pdf/" in url and not filename.endswith(".pdf"):
            filename += ".pdf"
        elif "." not in filename:
            filename += ".pdf"


        path = os.path.join(download_dir, filename)

        headers = {"User-Agent": "NovaAssistant/1.0"}

        r = requests.get(url, headers=headers, stream=True, timeout=30)
        r.raise_for_status()

        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)

        print(f"[DOWNLOAD] Saved → {path}")

        return path
    except Exception as e:
        return f"Download failed: {e}"