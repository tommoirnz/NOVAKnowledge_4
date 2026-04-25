import webbrowser


def open_webpage(query, internet_tools):
    """
    Search Brave for a webpage and open the first result.
    Uses Nova's InternetTools._brave_search().
    """

    try:
        # 🔍 Use your EXISTING internet system
        results = internet_tools._brave_search(query)

        if not results:
            return "No search results found."

        url = None

        # ── Case 1: results is STRING (your current format) ──
        if isinstance(results, str):
            for line in results.split("\n"):
                if "URL:" in line:
                    url = line.split("URL:")[1].strip()
                    break

        # ── Case 2: results is LIST (future-proof) ──
        elif isinstance(results, list):
            if results and isinstance(results[0], dict):
                url = results[0].get("url")

        if not url:
            return "No URL found in search results."

        # 🌐 Open in browser
        webbrowser.open(url)

        print(f"[WEB] Opening → {url}")

        return f"Opening webpage: {url}"

    except Exception as e:
        return f"Webpage open failed: {e}"