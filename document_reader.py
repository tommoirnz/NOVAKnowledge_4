import os
import requests
from bs4 import BeautifulSoup

# ------------------------------------------------
# FILE READER
# ------------------------------------------------

def read_document(path):

    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        return read_pdf(path)

    elif ext in [".txt", ".md"]:
        return read_text(path)

    else:
        raise ValueError(f"Unsupported file type: {ext}")


# ------------------------------------------------
# PDF
# ------------------------------------------------

def read_pdf(path):

    import fitz

    doc = fitz.open(path)

    text = ""

    for page in doc:
        text += page.get_text()

    doc.close()

    return text


# ------------------------------------------------
# TEXT
# ------------------------------------------------

def read_text(path):

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


# ------------------------------------------------
# URL
# ------------------------------------------------

def read_url(url):

    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers, timeout=15)

    soup = BeautifulSoup(r.text, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    lines = [line.strip() for line in text.splitlines()]

    return "\n".join(line for line in lines if line)