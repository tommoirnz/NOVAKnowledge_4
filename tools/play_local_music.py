import os
import json

AUDIO_EXTS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".wma", ".aac"}


def play_local_music(query=None, internet_tools=None):
    """
    Play a music track from the local music directory.
    Use this ONLY when the user wants to PLAY or LISTEN to a track.
    For listing, finding or browsing music files use file_explorer instead.
    """

    json_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "music.json"))
    try:
        with open(json_path, "r") as f:
            music_dir = json.load(f).get("music_dir", r"D:\Music")
    except Exception:
        music_dir = r"D:\Music"

    if not os.path.isdir(music_dir):
        return f"Music directory not found: {music_dir}"

    all_files = []
    for root, _, files in os.walk(music_dir):
        for f in files:
            if os.path.splitext(f)[1].lower() in AUDIO_EXTS:
                all_files.append(os.path.join(root, f))

    if not all_files:
        return f"No audio files found in {music_dir}"

    matches = all_files

    if query:
        terms = query.lower().split()

        stop = {"mp3", "wav", "flac", "ogg", "m4a", "wma", "aac", "play", "the", "a", "an",
                "some", "music", "song", "track", "file", "of", "to", "and", "in", "from",
                "with", "for", "by"}
        terms = [t for t in terms if t not in stop]

        if terms:
            scored = []
            for f in all_files:
                name = os.path.basename(f).lower()
                score = sum(len(t) for t in terms if t in name)
                if score > 0:
                    scored.append((score, f))

            scored.sort(key=lambda x: x[0], reverse=True)

            if scored:
                top_score = scored[0][0]
                matches = [f for s, f in scored if s == top_score]
            else:
                matches = []

    if not matches:
        return f"No tracks found matching: {query}"

    chosen = matches[0]
    print(f"[MUSIC TOOL] Attempting to play: {chosen}")
    print(f"[MUSIC TOOL] File exists: {os.path.isfile(chosen)}")
    try:
        os.startfile(chosen)
    except OSError as e:
        return f"os.startfile failed: {e}"

    msg = f"Playing: {os.path.basename(chosen)}\n[AUDIO:{chosen}]"
    return msg