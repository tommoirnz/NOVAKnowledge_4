import os
import json

VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".wmv", ".flv", ".m4v", ".webm"}


def play_local_video(query=None, internet_tools=None):
    """
    Play a video file from the local video directory.
    Use this ONLY when the user wants to PLAY or WATCH a video.
    For listing, finding or browsing video files use file_explorer instead.
    """

    json_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "music.json"))
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
            video_dir = data.get("video_dir", r"D:\Videos")
    except Exception:
        video_dir = r"D:\Videos"

    if not os.path.isdir(video_dir):
        return f"Video directory not found: {video_dir}"

    all_files = []
    for root, _, files in os.walk(video_dir):
        for f in files:
            if os.path.splitext(f)[1].lower() in VIDEO_EXTS:
                all_files.append(os.path.join(root, f))

    if not all_files:
        return f"No video files found in {video_dir}"

    matches = all_files

    if query:
        terms = query.lower().split()

        stop = {"mp4", "mkv", "mov", "play", "the", "a", "an", "some",
                "video", "film", "movie", "clip", "watch",
                "of", "to", "and", "in", "from", "with", "for"}
        terms = [t for t in terms if t not in stop]

        # Expand known aliases so shorthand maps to folder names
        alias_map = {
            "tng":         ["tng"],
            "next":        ["tng"],
            "generation":  ["tng"],
            "ds9":         ["deep", "space"],
            "deep":        ["ds9"],
            "space":       ["ds9"],
            "tos":         ["original"],
            "original":    ["tos"],
            "voyager":     ["voyager", "voy"],
            "voy":         ["voyager"],
            "enterprise":  ["enterprise"],
            "continues":   ["continues"],
        }
        expanded = list(terms)
        for term in terms:
            if term in alias_map:
                for extra in alias_map[term]:
                    if extra not in expanded:
                        expanded.append(extra)
        terms = expanded

        if terms:
            scored = []
            for f in all_files:
                # Score against full path, not just filename
                full_lower = f.lower().replace("\\", " ").replace("/", " ")
                score = sum(1 for t in terms if t in full_lower)

                # Strong boost if query implies TNG and file is in the TNG folder
                tng_terms = {"tng", "next", "generation"}
                if any(t in tng_terms for t in terms):
                    if "\\tng\\" in f.lower() or "/tng/" in f.lower():
                        score += 5

                # Strong boost if query implies DS9 and file is in DS9 folder
                ds9_terms = {"ds9", "deep", "space"}
                if any(t in ds9_terms for t in terms):
                    if "deep space" in f.lower():
                        score += 5

                # Strong boost for Voyager folder
                if "voyager" in terms:
                    if "voyager" in f.lower():
                        score += 5

                # Strong boost for Enterprise folder
                if "enterprise" in terms:
                    if "enterprise" in f.lower():
                        score += 5

                if score > 0:
                    scored.append((score, f))

            scored.sort(key=lambda x: x[0], reverse=True)

            if scored:
                top_score = scored[0][0]
                matches = [f for s, f in scored if s == top_score]
            else:
                matches = []

    if not matches:
        return f"No video found matching: {query}"

    chosen = matches[0]
    os.startfile(chosen)
    msg = f"Playing: {os.path.basename(chosen)}\n[VIDEO:{chosen}]"

    if len(matches) > 1:
        others = "\n".join(os.path.basename(m) for m in matches[1:4])
        msg += f"\n\nOther close matches:\n{others}"

    return msg