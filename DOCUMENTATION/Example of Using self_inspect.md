# How `play_local_music` Works

Here's a full breakdown of what happens under the hood when you invoke the tool:

---

## 1. 📂 Locate the Music Directory

The tool reads a **`music.json`** config file located one level up from the tool's own directory:

```python
json_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "music.json"))
music_dir = json.load(f).get("music_dir", r"D:\Music")
```

- Extracts the `music_dir` key from that config
- Falls back to `D:\Music` if the file is missing or malformed
- Validates the directory exists — returns an error if it doesn't

---

## 2. 🔍 Index All Audio Files

```python
for root, _, files in os.walk(music_dir):
    if os.path.splitext(f)[1].lower() in AUDIO_EXTS:
```

- **Recursively walks** the entire music directory tree
- Collects every file matching supported audio extensions (`.mp3`, `.wav`, `.flac`, `.ogg`, etc.)
- Builds a flat list of full file paths

---

## 3. 🧠 Search & Score Matching

When a query is provided, it goes through three steps:

**Step 1 — Stop word filtering**
Strips noise words from the query before matching:
```python
stop = {"mp3", "wav", "play", "the", "a", "an", "some", "music", "song", "track", "file"}
terms = [t for t in terms if t not in stop]
```
So *"play me some music"* reduces to an empty list → triggers a random pick.

**Step 2 — Term scoring**
Each filename is scored by how many query terms appear in it:
```python
score = sum(1 for t in terms if t in name)
```
This is substring matching (`in`), not regex or fuzzy distance.

**Step 3 — Top-score selection**
Only files matching the **highest score** are kept as candidates — not just any partial match.

---

## 4. 🎲 Random Selection & Playback

```python
chosen = random.choice(matches)
os.startfile(chosen)
```

- If multiple files tie for top score, one is **chosen at random**
- Uses `os.startfile()` — a Windows-native call that opens the file in whatever the default media player is (VLC, WMP, etc.)
- Returns the chosen filename as a confirmation string

---

## ⚠️ Notable Quirks

| Behaviour | Detail |
|---|---|
| **No query** | Falls back to a random track from the full library |
| **Vague query** | If all terms are stop words, same random-pick result |
| **No match found** | Returns `"No tracks found matching: {query}"` — does **not** fall back to random |
| **Windows-only** | `os.startfile()` is a Windows API — breaks on Linux/Mac |
| **Fuzzy, not exact** | Uses simple substring matching, not edit distance or regex |

---

**Bottom line:** A lightweight, scoring-based fuzzy search over filenames with a random tiebreaker. Simple, effective, and firmly Windows-bound. 🎵