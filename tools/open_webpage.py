import webbrowser

def open_webpage(url, internet_tools=None):
    if not url.startswith("http"):
        url = "https://" + url

    webbrowser.open(url)
    return f"Opened webpage: {url}"