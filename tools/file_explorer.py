import os
import json

HOME = os.path.expanduser("~")

SHORTCUTS = {
    "desktop":   os.path.join(HOME, "Desktop"),
    "documents": os.path.join(HOME, "Documents"),
    "downloads": os.path.join(HOME, "Downloads"),
    "home":      HOME,
    "music":     os.path.join(HOME, "Music"),
    "videos":    os.path.join(HOME, "Videos"),
}


def _resolve_path(path):
    """Resolve a path case-insensitively on case-sensitive systems."""
    if os.path.exists(path):
        return path
    parts = path.replace("\\", "/").split("/")
    current = parts[0] + "/"  # drive or root
    for part in parts[1:]:
        if not os.path.isdir(current):
            return path
        entries = os.listdir(current)
        match = next((e for e in entries if e.lower() == part.lower()), None)
        if match is None:
            return path
        current = os.path.join(current, match)
    return current


def _get_media_dirs():
    """Read music_dir and video_dir from music.json."""
    json_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "music.json"))
    try:
        with open(json_path) as f:
            data = json.load(f)
            return data.get("music_dir", r"D:\Music"), data.get("video_dir", r"D:\Videos")
    except Exception:
        return r"D:\Music", r"D:\Videos"


def _extract_search_keyword(query, media_type="video"):
    """Use a small AI call to extract the actual search keyword from a natural language query."""
    try:
        import urllib.request
        import json as _json

        api_key = os.environ.get("OPENROUTER_KEY", "")
        if not api_key:
            return None

        prompt = (
            f"Extract only the specific search keyword from this {media_type} file query. "
            f"Return ONLY the keyword (e.g. 'star trek', 'dad army', 'abba') or the single word 'ALL' "
            f"if the user wants all files with no filter. No explanation, no punctuation, just the keyword.\n\n"
            f"Query: {query}"
        )

        payload = _json.dumps({
            "model": "qwen/qwen3.5-122b-a10b",
            "max_tokens": 20,
            "messages": [{"role": "user", "content": prompt}]
        }).encode()

        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = _json.loads(resp.read())
            keyword = result["choices"][0]["message"]["content"].strip().lower()
            if keyword == "all":
                return ""
            return keyword
    except Exception:
        return None


def file_explorer(query, path=None):
    """
    Explore files and directories on the local PC.
    Can list contents, read files, search for files by name or extension,
    copy, move, save and delete files.

    Query examples:
    - "list desktop"
    - "find *.py in nova"
    - "read C:/Projects/myfile.py"
    - "search utils in projects"
    - "copy C:/file.txt to C:/backup/"
    - "move C:/file.txt to C:/dest/"
    - "save C:/notes.txt content here"
    - "delete C:/file.txt"
    - "tree C:/Projects"
    - "open C:/Users/OEM/Desktop/photo.png"
    - "what star trek video files do I have?"
    """
    import re

    # NORMALISE SLASHES FIRST
    query = query.replace("\\", "/").strip()

    # Fix wrong Windows user paths
    query = re.sub(r"C:/Users/[^/]+", HOME.replace("\\", "/"), query, flags=re.IGNORECASE)

    query_lower = query.lower()

    music_dir, video_dir = _get_media_dirs()

    # ── Natural language MP3 / music listing ─────────────────────────────────
    if "mp3" in query_lower and ("list" in query_lower or "all" in query_lower):
        return _find_files(music_dir, "*.mp3")

    # ── Natural language video search ─────────────────────────────────────────
    if any(w in query_lower for w in ["video", "mp4", "mkv", "videos"]) and \
            any(w in query_lower for w in
                ["what", "list", "find", "show", "have", "all", "can", "count", "how", "many", "total", "number"]):
        keyword = _extract_search_keyword(query, "video")
        if keyword is None:
            keyword = ""  # fallback — list all
        if keyword:
            return _search_files(video_dir, keyword)
        else:
            result = _find_files(video_dir, "*.mp4")
            result += "\n" + _find_files(video_dir, "*.mkv")
            return result

    # ── Natural language music search ─────────────────────────────────────────
    if any(w in query_lower for w in ["music", "song", "songs", "track", "tracks"]) and \
            any(w in query_lower for w in ["what", "list", "find", "show", "have", "all", "can"]):
        keyword = _extract_search_keyword(query, "music")
        if keyword is None:
            keyword = ""  # fallback — list all
        if keyword:
            return _search_files(music_dir, keyword)
        else:
            return _find_files(music_dir, "*.mp3")

    # ── Directory shortcuts ───────────────────────────────────────────────────
    for name, full_path in sorted(SHORTCUTS.items(), key=lambda x: len(x[0]), reverse=True):
        idx = query_lower.find(name)
        if idx != -1:
            before = query_lower[idx - 1] if idx > 0 else " "
            after = query_lower[idx + len(name)] if idx + len(name) < len(query_lower) else " "
            if not before.isalnum() and not after.isalnum() and before not in ":/\\" and after not in ":/\\":
                query = query[:idx] + full_path + query[idx + len(name):]
                query_lower = query.lower()
                break

    # ── Handle current directory ──────────────────────────────────────────────
    if "current" in query_lower and "director" in query_lower:
        return _list_directory(os.getcwd())

    # ── Handle home directory ─────────────────────────────────────────────────
    if "home" in query_lower and "director" in query_lower:
        return _list_directory(os.path.expanduser("~"))

    # ── READ a specific file ──────────────────────────────────────────────────
    if query_lower.startswith("read "):
        file_path = _resolve_path(query[5:].strip())
        return _read_file(file_path)

    # ── LIST directory contents ───────────────────────────────────────────────
    if query_lower.startswith("list "):
        dir_path = _resolve_path(query[5:].strip())
        return _list_directory(dir_path)

    # ── FIND files by extension ───────────────────────────────────────────────
    if query_lower.startswith("find "):
        parts = query[5:].split(" in ", 1)
        if len(parts) == 2:
            pattern = parts[0].strip()
            search_dir = _resolve_path(parts[1].strip())
            return _find_files(search_dir, pattern)
        else:
            return "Usage: find *.ext in C:/path/to/dir"

    # ── SEARCH for filename containing keyword ────────────────────────────────
    if query_lower.startswith("search "):
        parts = query[7:].split(" in ", 1)
        if len(parts) == 2:
            keyword = parts[0].strip()
            search_dir = _resolve_path(parts[1].strip())
            return _search_files(search_dir, keyword)
        else:
            # No path given — default to home directory
            return _search_files(HOME, parts[0].strip())

    # ── TREE — show directory structure ──────────────────────────────────────
    if query_lower.startswith("tree "):
        dir_path = _resolve_path(query[5:].strip())
        return _tree(dir_path, max_depth=3)

    # ── COPY a file ───────────────────────────────────────────────────────────
    if query_lower.startswith("copy "):
        parts = query[5:].split(" to ", 1)
        if len(parts) == 2:
            return _copy_file(_resolve_path(parts[0].strip()), parts[1].strip())
        else:
            return "Usage: copy C:/source.txt to C:/destination/"

    # ── SAVE text to a file ───────────────────────────────────────────────────
    if query_lower.startswith("save "):
        parts = query[5:].split(" ", 1)
        if len(parts) == 2:
            return _save_text(parts[0].strip(), parts[1].strip())
        else:
            return "Usage: save C:/path/file.txt content to write"

    # ── DELETE a file ─────────────────────────────────────────────────────────
    if query_lower.startswith("delete "):
        file_path = _resolve_path(query[7:].strip())
        return _delete_file(file_path)

    # ── MOVE a file ───────────────────────────────────────────────────────────
    if query_lower.startswith("move "):
        parts = query[5:].split(" to ", 1)
        if len(parts) == 2:
            import shutil
            src = _resolve_path(parts[0].strip())
            dst = parts[1].strip()
            if not os.path.exists(src):
                return f"Source not found: {src}"
            try:
                shutil.move(src, dst)
                return f"Moved: {src}\n   to: {dst}"
            except Exception as e:
                return f"Move failed: {e}"
        else:
            return "Usage: move C:/source.txt to C:/destination/"

    # ── OPEN a file with default application ─────────────────────────────────
    if query_lower.startswith("open "):
        file_path = _resolve_path(query[5:].strip())
        if not os.path.exists(file_path):
            parent = os.path.dirname(file_path)
            name = os.path.basename(file_path).lower()
            if os.path.isdir(parent):
                for f in os.listdir(parent):
                    if f.lower().startswith(name) or name in f.lower():
                        file_path = os.path.join(parent, f)
                        break
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"
        try:
            os.startfile(file_path)
            return f"Opened: {file_path}"
        except Exception as e:
            return f"Could not open {file_path}: {e}"

    # ── Default — treat as path to list or read ───────────────────────────────
    resolved = _resolve_path(query)
    if os.path.isdir(resolved):
        return _list_directory(resolved)
    if os.path.isfile(resolved):
        return _read_file(resolved)

    # ── Glob pattern fallback (e.g. C:/Users/OEM/Desktop/*.pdf) ──────────────
    if '*' in query or '?' in query:
        parent = os.path.dirname(resolved)
        pattern = os.path.basename(resolved)
        if os.path.isdir(parent):
            return _find_files(parent, pattern)

    return f"Unknown command. Use: list, read, find, search, tree, copy, move, save, delete, open. Got: {query}"

def _read_file(file_path, raw=False):
    if not os.path.exists(file_path):
        return f"File not found: {file_path}"

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if raw:
        return content

    if len(content) > 30000:
        content = content[:30000] + f"\n\n... [truncated — {len(content):,} chars total]"

    return f"FILE: {file_path}\n{'='*60}\n{content}"


def _list_directory(dir_path):
    """List contents of a directory."""
    if not os.path.exists(dir_path):
        return f"Directory not found: {dir_path}"
    if not os.path.isdir(dir_path):
        return f"Not a directory: {dir_path}"

    try:
        entries = sorted(os.listdir(dir_path))
        dirs = []
        files = []

        for entry in entries:
            full = os.path.join(dir_path, entry)
            if os.path.isdir(full):
                dirs.append(f"  [DIR]  {entry}/")
            else:
                size = os.path.getsize(full)
                files.append(f"  [FILE] {entry}  ({_fmt_size(size)})")

        result = f"DIRECTORY: {dir_path}\n{'='*60}\n"
        result += f"  {len(dirs)} folders, {len(files)} files\n\n"

        if dirs:
            result += "FOLDERS:\n"
            result += "\n".join(dirs) + "\n\n"
        if files:
            result += "FILES:\n"
            result += "\n".join(files)

        return result

    except PermissionError:
        return f"Permission denied: {dir_path}"
    except Exception as e:
        return f"Could not list {dir_path}: {e}"


def _find_files(search_dir, pattern):
    """Find files matching a pattern (e.g. *.py) recursively."""
    import fnmatch

    # If no wildcard, treat as substring search
    if '*' not in pattern and '?' not in pattern:
        return _search_files(search_dir, pattern)

    if not os.path.exists(search_dir):
        return f"Directory not found: {search_dir}"

    matches = []
    try:
        for root, dirs, files in os.walk(search_dir):
            dirs[:] = [d for d in dirs
                       if not d.startswith('.') and d not in
                       ('__pycache__', 'node_modules', '.git', '.venv', 'venv')]
            for fname in files:
                if fnmatch.fnmatch(fname.lower(), pattern.lower()):
                    full = os.path.join(root, fname)
                    size = os.path.getsize(full)
                    matches.append(f"  {full}  ({_fmt_size(size)})")
            if len(matches) > 100000:
                matches.append("  ... [stopped at 100000 results]")
                break
    except PermissionError:
        pass

    if not matches:
        return f"No files matching '{pattern}' found in {search_dir}"

    MAX_OUTPUT_CHARS = 20_000
    result = f"FIND: {pattern} in {search_dir}\n{'='*60}\n"
    result += f"  {len(matches)} result(s)\n\n"
    listing = "\n".join(matches)
    if len(listing) > MAX_OUTPUT_CHARS:
        listing = listing[:MAX_OUTPUT_CHARS]
        listing += f"\n\n  ... [truncated — showing first results of {len(matches)} total]"
    result += listing
    return result



def _search_files(search_dir, keyword):
    """Search for files whose names contain a keyword."""
    if not os.path.exists(search_dir):
        return f"Directory not found: {search_dir}"

    matches = []
    try:
        for root, dirs, files in os.walk(search_dir):
            dirs[:] = [d for d in dirs
                       if not d.startswith('.') and d not in
                       ('__pycache__', 'node_modules', '.git', '.venv', 'venv')]
            for fname in files:
                if keyword.lower() in fname.lower():
                    full = os.path.join(root, fname)
                    size = os.path.getsize(full)
                    matches.append(f"  {full}  ({_fmt_size(size)})")
            if len(matches) > 200:
                matches.append("  ... [stopped at 200 results]")
                break
    except PermissionError:
        pass

    if not matches:
        return f"No files containing '{keyword}' found in {search_dir}"

    result = f"SEARCH: '{keyword}' in {search_dir}\n{'='*60}\n"
    result += f"  {len(matches)} result(s)\n\n"
    result += "\n".join(matches)
    return result


def _tree(dir_path, max_depth=3, _depth=0, _prefix=""):
    """Show directory tree structure."""
    if not os.path.exists(dir_path):
        return f"Directory not found: {dir_path}"

    if _depth == 0:
        result = f"TREE: {dir_path}\n{'='*60}\n"
    else:
        result = ""

    if _depth >= max_depth:
        return result + f"{_prefix}    ...\n"

    try:
        entries = sorted(os.listdir(dir_path))
        entries = [e for e in entries
                   if not e.startswith('.') and e not in
                   ('__pycache__', 'node_modules', '.git', '.venv', 'venv')]

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            extension = "    " if is_last else "│   "
            full = os.path.join(dir_path, entry)

            if os.path.isdir(full):
                result += f"{_prefix}{connector}{entry}/\n"
                result += _tree(full, max_depth, _depth + 1, _prefix + extension)
            else:
                size = os.path.getsize(full)
                result += f"{_prefix}{connector}{entry}  ({_fmt_size(size)})\n"

    except PermissionError:
        result += f"{_prefix}  [Permission denied]\n"

    return result


def _copy_file(src, dst):
    """Copy a file from src to dst."""
    import shutil

    if not os.path.exists(src):
        return f"Source file not found: {src}"

    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))

    try:
        shutil.copy2(src, dst)
        return f"Copied: {src}\n    to: {dst}"
    except PermissionError:
        return f"Permission denied copying to: {dst}"
    except Exception as e:
        return f"Copy failed: {e}"


def _save_text(file_path, content):
    """Save text content to a file."""
    try:
        parent = os.path.dirname(file_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Saved: {file_path}  ({len(content):,} chars)"
    except PermissionError:
        return f"Permission denied: {file_path}"
    except Exception as e:
        return f"Save failed: {e}"


def _delete_file(file_path):
    """Delete a file."""
    if not os.path.exists(file_path):
        return f"File not found: {file_path}"
    try:
        os.remove(file_path)
        return f"Deleted: {file_path}"
    except PermissionError:
        return f"Permission denied: {file_path}"
    except Exception as e:
        return f"Delete failed: {e}"


def _fmt_size(size):
    """Format file size human-readable."""
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size/1024:.1f}KB"
    else:
        return f"{size/1024/1024:.1f}MB"