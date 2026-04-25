import webbrowser
import requests
import re


def play_youtube_video(query):

    url = "https://www.youtube.com/results"

    params = {"search_query": query}

    r = requests.get(url, params=params)

    html = r.text

    match = re.search(r"/watch\?v=(.{11})", html)

    if not match:
        return "No YouTube video found."

    video_id = match.group(1)

    video_url = f"https://www.youtube.com/watch?v={video_id}"

    webbrowser.open(video_url)

    return f"Playing YouTube video: {video_url}"