import requests
import tempfile
import subprocess


def play_audio_from_url(url):

    r = requests.get(url)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:

        f.write(r.content)

        path = f.name

    subprocess.Popen(["start", path], shell=True)

    return f"Playing audio from {url}"

