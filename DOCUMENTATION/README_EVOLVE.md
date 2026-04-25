# Nova Assistant — Self-Evolution System and Debug 

## Overview

Nova Assistant includes a self-evolution system that allows the AI to modify its own source code at runtime. It can add new features, fix weaknesses, and patch any file in the project — all without stopping the running application. Changes are versioned, backed up, and logged automatically.
Use at own risk!
This is not a toy demo. It operates on a real multi-file Python application with voice I/O, internet search, LaTeX rendering, and a code execution sandbox.

---

## How It Works

### The Core Idea

Instead of regenerating entire files (slow, error-prone, loses context), the system works at the **function level**:

1. Read the current source of every file in the project
2. Send signatures + full source to the AI with the feature request
3. AI returns only the functions that need to change
4. Each function is validated, routed to the correct file, and patched in place
5. External files are backed up before writing, nova_assistant gets a new version number

### Key Files

| File | Role |
|------|------|
| `self_improver.py` | The evolution engine — reads, patches, versions, backs up |
| `nova_assistant_v1.py` | Entry point — versioned on each evolution |
| `code_window.py` | Patched in place with backup |
| `self_improvement_log.json` | History of every evolution |

---

## File Versioning Strategy

### Main Program (nova_assistant)
Each evolution creates a new numbered copy:
```
nova_assistant_v1.py  ← you run this
nova_assistant_v2.py  ← after first evolution
nova_assistant_v3.py  ← after second evolution
```
The system reads whichever version is currently **running** (via `sys.argv[0]`) and writes one version higher. It never overwrites an existing version — if v2 already exists it skips to v3.

If you run an older version (e.g. v1 when v3 exists), it warns you in the log and branches from v1, saving as v4 to avoid overwriting v2 or v3.

### External Files (code_window, Internet_Tools, etc.)
These are patched **in place** with numbered backups:
```
code_window_b1.py  ← original backup
code_window_b2.py  ← backup before second change
code_window.py     ← always the current live version
```
Imports never need to change because the filename stays the same. Only files that were actually modified get backed up — untouched files are left alone.

---

## Rolling Back

To roll back any file to a previous state:

**External file (e.g. code_window):**
```
Copy code_window_b1.py → code_window.py
Restart Nova
```

**Main program:**
```
Run nova_assistant_v1.py instead of v2
```

**Full rollback to original state:**
```
Copy all _b1.py files back to their originals
Run nova_assistant_v1.py
```

---

## Using the Evolution System

### From the Nova UI

Click the **EVOLVE** button in the left panel. A dialog appears with two options:

**Add a feature** — type a description:
```
add autosave for conversation history
make the internet search faster  
change code_window background to dark blue
add a word count display to the conversation panel
improve the ReAct agent prompt
```

**Fix a weakness** — leave the text box empty. Nova will analyse its own code and apply one small safe improvement automatically.

### What It Can Do

- Add new methods to any file
- Modify existing methods in any file
- Change UI colours, layouts, and behaviour
- Improve prompts and AI logic
- Add new features that span multiple files
- Improve its own evolution machinery in `self_improver.py`

### What It Cannot Do (Yet)

- Create brand new `.py` files from scratch
- Hot-reload changes without a restart (changes take effect on next run)

---

## The Self-Improver Architecture

### `SelfImprover.__init__`
Sets up the list of files it can read and modify (`base_names`), loads evolution history, and records which version of nova is currently running.

### `run_feature_cycle(feature_request)`
The main evolution method:
1. Reads full source of nova_assistant and all external files
2. Extracts method signatures from all files
3. Sends everything to the AI with the feature request
4. Parses the returned code block into individual functions
5. Validates each function (skips bad ones, keeps good ones)
6. Routes each function to its owner file
7. Patches each file
8. Backs up and writes external files in place
9. Returns patched nova source for versioning

### `run_improvement_cycle()`
Auto-improvement — no feature request needed. Sends signatures + mistake history to the AI and asks it to pick one small safe improvement. Uses evolution history to avoid repeating previous improvements.

### `_find_owner_file(fn_name)`
Searches all known files to find which one contains a given function. This is how the system knows to patch `_create_ui` in `code_window.py` rather than `nova_assistant.py`.

### `_split_into_functions(code)`
Parses the AI's returned code block into individual named functions. Each function is normalised to consistent indentation before patching.

### `_backup_file(base_name)`
Creates `filename_b1.py`, `_b2.py` etc. — only called immediately before writing a changed file.

---

## Adding New Files to the System

When you manually add a new `.py` file to the project, add it to the `source_files` list in `_init_backend` in `nova_assistant.py`:

```python
self.self_improver = SelfImprover(
    self.ai,
    self.log,
    source_files=[
        "nova_assistant",
        "code_execution_loop",
        "latex_window",
        "theme_manager",
        "code_window",
        "mistake_memory",
        "Internet_Tools",
        "math_speech",
        "planner",
        "agent_executor",
        "my_new_file",    # ← add here
    ],
    running_file=os.path.abspath(sys.argv[0])
)
```

The system will automatically read its full source, include its signatures in the AI prompt, and be able to patch it on the next evolution.

---

## Evolution History

Every evolution is recorded in `self_improvement_log.json`:

```json
{
  "timestamp": "2026-03-17T06:27:08",
  "file": "nova_assistant",
  "version_created": "nova_assistant_v2.py",
  "feature_request": "add autosave for conversation history",
  "changes_made": "Added _autosave_path, _save_conversation_history...",
  "how_to_use": "Run nova_assistant_v2.py to use this version."
}
```

View the history inside Nova by clicking the **HISTORY** button, or open the JSON file directly. The last 5 history entries are injected into the auto-improvement prompt so the AI knows what it has already done and does not repeat itself.

---

## Design Principles

**Surgical not wholesale** — only changed functions are written, never entire files. This preserves context and reduces the chance of the AI introducing regressions.

**Always recoverable** — every change has a backup. The worst case is a manual file copy.

**Transparent** — every patch is logged in the system console and in the history file. Nothing happens silently.

**Sandboxed testing** — the evolved code is shown in the code window and run under the main venv before you commit to using it.

**Version aware** — the system knows which version is running and always writes one step forward from there, never backwards.

---

## Limitations and Future Directions

- Changes require a restart to take effect (Python loads modules once at startup)
- The AI can only patch functions it can see — deeply nested lambdas and closures may be missed
- Very large files may approach token limits — signatures help but full source is expensive
- File creation is not yet supported — the AI can only modify existing files
- True autonomous improvement would require a self-evaluation loop to judge whether changes actually helped

---

Multi-Step Evolution
For complex feature requests, Nova automatically decomposes the request into 3–6 atomic steps and executes them sequentially. Each step builds on the source produced by the previous step — no disk writes happen between steps, only at the end when the final version is saved.
The decomposition threshold is triggered when the request contains more than 15 words, or includes connective words like "and", "also", "with", "plus", "including", or "as well".
Each step is import-checked using py_compile and optionally pyflakes after patching. If a step fails the import check, it is retried once with the error injected back into the prompt. If step 1 fails outright, or if two consecutive steps fail, the whole cycle is aborted and no version is written.
Progress is shown in the conversation panel as each step completes.
*Nova Assistant Self-Evolution System

Debugging with the DEBUG Button
The DEBUG button opens a symptom dialog. Describe what is broken or not behaving as expected in plain English — the more specific the better. Include the method name or area of the UI if you know it.
Nova sends the full source plus the symptom description to the AI, which diagnoses the root cause and returns a targeted patch. The patch goes through the same pipeline as EVOLVE — import checked, versioned, and shown in the code window.
Good symptom descriptions:

"The tooltip on the LOAD PDF button does not appear when hovering"
"Clicking EVOLVE does nothing — no popup appears"
"The character counter always shows 0 even when text is typed"

The DEBUG button is intended to be used immediately after EVOLVE produces a broken version — describe what you see, let Nova fix it, restart on the new version.


— Dr Tom Moir*
