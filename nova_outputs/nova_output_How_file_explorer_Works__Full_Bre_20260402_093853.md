# 🔍 How `file_explorer` Works — Full Breakdown

Based on a live self-inspection of Nova's source code, here's a comprehensive breakdown of how `file_explorer` actually works under the hood.

---

## Overview

`file_explorer` is a **single multipurpose function** that handles all file system interactions — listing, reading, searching, copying, moving, saving, deleting, and opening files. Rather than requiring strict command syntax, it uses **natural language parsing** as its primary interface, making it genuinely conversational.

---

## Step 1 — Entry Point & Path Normalisation

```python
query = query.replace("\\", "/").strip()
query = re.sub(r"C:/Users/[^/]+", HOME.replace("\\", "/"), query, flags=re.IGNORECASE)
```

The very first thing it does is **normalise slashes** and **rewrite Windows user paths** to the correct home directory — regardless of what username was typed in. Solid defensive coding that prevents the most common path-related failures.

---

## Step 2 — Natural Language Detection (Media Files)

Before any command parsing occurs, it checks for **natural language media queries**:

### 🎵 MP3 / Music
```python
if "mp3" in query_lower and ("list" in query_lower or "all" in query_lower):
    return _find_files(music_dir, "*.mp3")
```

### 🎬 Video Files
Detects words like `"video"`, `"mp4"`, `"mkv"`, `"videos"` combined with intent words like `"what"`, `"list"`, `"find"`, `"show"`, `"have"`, `"all"`, `"can"`. It then **strips stop words** (do, i, have, show, me, list…) to extract the meaningful search keyword, then calls `_search_files()`.

### 🎶 Music / Songs
Same pattern — strips stop words, extracts keyword, searches the `music_dir`.

This means queries like *"what Star Trek video files do I have?"* work naturally, without any special syntax.

---

## Step 3 — Directory Shortcuts

```python
for name, full_path in sorted(SHORTCUTS.items(), key=lambda x: len(x[0]), reverse=True):
```

It iterates a `SHORTCUTS` dictionary — **sorted longest-match first** to avoid partial word collisions — replacing shorthand names like `"desktop"` or `"nova"` with their full resolved paths. Boundary checks ensure it doesn't accidentally match inside longer words.

---

## Step 4 — Command Dispatch (Prefix Matching)

After natural language checks, it falls through to **explicit command prefixes**:

| Prefix | Action | Helper |
|---|---|---|
| `read ` | Reads and returns file contents | `_read_file()` |
| `list ` | Lists directory contents | `_list_directory()` |
| `find *.ext in path` | Glob-pattern file search | `_find_files()` |
| `search keyword in path` | Filename keyword search | `_search_files()` |
| `tree ` | Directory tree (max depth 3) | `_tree()` |
| `copy src to dst` | Copies a file | `_copy_file()` |
| `save path content` | Writes text to a file | `_save_text()` |
| `delete ` | Deletes a file | `_delete_file()` |
| `move src to dst` | Moves a file | `shutil.move()` directly |
| `open ` | Opens file with OS default app | `os.startfile()` |

The `open` command also includes **fuzzy fallback** — if the exact path isn't found, it attempts a partial filename match before giving up.

---

## Step 5 — Path Resolution

All paths — regardless of how they arrived — pass through `_resolve_path()`, which handles:
- Relative paths
- Shortcut expansion
- Home directory (`~`) expansion

...before any actual file operation is attempted.

---

## Key Design Patterns

| Pattern | Purpose |
|---|---|
| **Natural language first** | Handles conversational queries before strict commands |
| **Longest-match shortcuts** | Prevents partial word collisions in path substitution |
| **Stop word stripping** | Extracts meaningful search terms from natural sentences |
| **Fallback fuzzy matching** | `open` tries partial filename if exact path fails |
| **Unified entry point** | One function for all file ops — clean for tool dispatch |

---

## Summary

`file_explorer` is essentially a **mini command interpreter with NLP preprocessing**. It handles both structured commands (`"find *.py in nova"`) and natural language (`"what Star Trek video files do I have?"`), resolves paths intelligently, and dispatches to focused helper functions for each operation type.

The design philosophy is clear: **work conversationally first, fall back to explicit syntax second**. Whoever wrote it wanted it to feel like talking to a file system, not programming one. 🎯

---

*Sources: Live self-inspection of Nova's source code via `self_inspect` tool. No external URLs.*