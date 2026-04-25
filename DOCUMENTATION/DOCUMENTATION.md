# How NOVA Works: A Detailed Technical Explanation

Based on a live self-inspection of NOVA's source code, here is a comprehensive breakdown of every major component and how they interact.

---

## 1. Overall Architecture

NOVA is built around three core pillars:

| Component | Role |
|---|---|
| **TaskPlanner** | Interprets user input and produces a structured execution plan |
| **AgentExecutor** | Executes the plan by routing tasks to the correct agent or tool |
| **Tools** | Specialised modules that perform concrete actions (file access, audio, images, diagrams, etc.) |

These components are wired together through a central `nova` object that acts as the application hub, holding references to:
- `nova.ai` — the AI backend
- `nova.tools` — the tool registry
- `nova.log` — the logger
- `nova.root` — the UI root
- `nova.image_dir` — shared image directory state

---

## 2. The TaskPlanner — Parsing Intent and Building a Plan

### Entry Point: `create_plan(user_input, history_str="")`

When a user submits a request, `TaskPlanner.create_plan()` is the first thing called. Its job is to convert free-form natural language into a structured JSON plan that the executor can act on.

---

### Step 1 — Lightweight Intent Routing (Fast Path)

Before calling the AI at all, the planner performs lightweight keyword matching to handle common patterns instantly:

```python
is_image = any(k in text for k in image_keywords)
is_plot  = any(k in text for k in plot_keywords)
```

- If the user asks for **images** (and not a poster/collage/code task), it immediately returns:
```json
{
  "mode": "parallel",
  "tasks": [{"agent": "search_and_show_image", "task": "<cleaned query>"}]
}
```
- If the user asks for a **plot or graph** (without an explanation keyword like "explain" or "derive"), it immediately returns:
```json
{
  "mode": "parallel",
  "tasks": [{"agent": "code", "task": "<user input>"}]
}
```

This fast-path avoids unnecessary AI calls for simple, unambiguous requests.

---

### Step 2 — AI-Driven Planning

For more complex requests, the planner constructs a detailed prompt that includes:

- **Environment context** — from `env_fn()`, e.g. current date, system state
- **Recent conversation history** — via `history_str`
- **Today's date** — injected via `datetime.now()`
- **A comprehensive set of rules** covering:
  - Which agents are valid
  - When to use sequential vs parallel mode
  - Task decomposition rules (splitting multi-action requests)
  - Music, diagram, and plotting rules
  - Strict JSON-only output format

The AI is called with a reduced token budget (`max_tokens = 512`) to keep responses concise and well-formed.

---

### Step 3 — Response Cleaning and Validation

The raw AI response goes through `_clean_response()`, which:
- Strips markdown code fences (` ```json `)
- Removes leading/trailing whitespace and backticks
- Strips any `json` prefix the model might add

Then several validation checks are applied:
- Must end with `}` (truncation check)
- Must start with `{`
- Must not contain bad patterns like `"Step 1"`, `"First"`, `"PLAN"` (caught by `_is_bad_output()`)
- Must parse as valid JSON
- All agent names must be in the `VALID_AGENTS` set

If any check fails, the planner **retries up to 3 times**.

---

### Step 4 — Task Sanitisation

Each task in the parsed JSON is checked:
- Agent name must be in the whitelist of 18 valid agents
- Task description is trimmed to its first line (no multi-line bleed)
- Empty or malformed tasks are discarded

---

### Output Format

The planner returns a dictionary like:

```json
{
  "mode": "sequential",
  "tasks": [
    {"agent": "research", "task": "find current Bitcoin price"},
    {"agent": "code",     "task": "plot the price trend"}
  ]
}
```

**Mode** is either `"parallel"` (tasks are independent) or `"sequential"` (tasks depend on each other's output).

If all retries fail, the planner falls back to:
```python
[{"agent": "text", "task": user_input}]
```

---

### Valid Agents

The planner recognises exactly these **18 agents**:

```
research, file_explorer, youtube_tools, open_webpage,
play_local_music, play_local_video, play_audio_from_url,
play_sound_from_url, search_and_play_sound,
search_and_show_image, summarise_document_from_source,
download_file, self_inspect, read_source,
code, math, text, diagram
```

---

## 3. The AgentExecutor — Routing and Running Tasks

Once the planner produces a plan, `AgentExecutor` takes over.

---

### Parallel Execution: `run_tasks(tasks, internet_ctx="")`

```python
with ThreadPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(self._run_agent, t, internet_ctx) for t in tasks]
    results = [f.result() for f in futures]
```

Up to **4 tasks run simultaneously** in separate threads. This is used when tasks are independent — for example, fetching two unrelated pieces of information at the same time.

---

### Sequential Execution: `run_tasks_sequential(tasks, internet_ctx="")`

Tasks run one after another, and crucially, **output from earlier tasks is injected into later tasks**. This is how NOVA chains multi-step workflows.

#### Key behaviours in sequential mode:

**1. Self-inspect safety net**

If the last task is `self_inspect`, a `text` agent task is automatically appended:
```python
tasks = list(tasks) + [{
    "agent": "text",
    "task": f"Based on the source code inspection, answer this question: {original_task}"
}]
```
This ensures the inspection result is always interpreted and delivered to the user rather than returned as raw code.

**2. Context accumulation**

When a `self_inspect` or `research` agent produces output, that output is stored in `accumulated_context`. The next `text` or `code` task receives it prepended to its task description:

```
CONTEXT FROM PREVIOUS INSPECTION:
<inspection result>

TASK: <original task>
```

For `code` tasks, the prefix is more forceful:
```
REAL DATA RETRIEVED — YOU MUST USE THESE EXACT VALUES:
<data>
```

**3. Image-to-code handoff**

If a `search_and_show_image` task runs before a `code` task, the executor scans the image directory for recently downloaded files and injects their exact local paths into the code task:
```
USE THESE EXACT LOCAL IMAGE FILES — DO NOT SEARCH FOR NEW ONES:
C:/nova/images/img1.jpg
C:/nova/images/img2.jpg

TASK: arrange them in a poster
```

**4. Auto-play after file_explorer**

If `file_explorer` returns a result containing `.mp3` or `.wav` file paths, the executor automatically appends a `play_local_music` task and executes it immediately — the user does not need to ask twice.

**5. Research failure detection**

If a `research` agent returns a result containing phrases like `"not found"`, `"unable to"`, or `"recommend searching"` — and there are no URLs or media file references in the result — the chain is stopped early:
```python
self.nova.log("[EXECUTOR] Research found nothing actionable — stopping chain")
return results
```

---

### The Core Runner: `_run_agent(task, internet_ctx="")`

This method dispatches a single task to the right handler. Here is the full routing logic:

#### Tool Map (direct tool calls)

```python
tool_map = {
    "play_local_music":      "play_local_music",
    "play_local_video":      "play_local_video",
    "youtube_tools":         "play_youtube_video",
    "file_explorer":         "file_explorer",
    "open_webpage":          "open_webpage",
    "self_inspect":          "self_inspect",
    "search_and_show_image": "search_and_show_image"
}
```

These agents are routed directly to `nova.tools.run(tool_name, ...)`.

**Special handling for `search_and_show_image`:**
- Extracts a numeric count from the query (word or digit form: "three", "5", etc.)
- Strips noise phrases ("find", "pictures of", "for a poster", etc.)
- Truncates the query at instruction words like "put", "arrange", "display"
- Calls the tool with the cleaned query and requested count

**Special handling for `open_webpage`:**
- Passes `internet_tools=nova.ai.internet` as a named argument

---

#### Diagram Agent

```python
result = self.nova.tools.run("diagram", job, self.nova.ai)
if result.startswith("DIAGRAM:"):
    path = result.split(":", 1)[1].strip()
    self.nova.root.after(0, lambda p=path: self.nova.show_graphviz_diagram(p))
    return "[DIAGRAM GENERATED]"
```

The diagram is rendered and displayed in the UI via the main thread (`root.after(0, ...)`).

---

#### Research Agent

The task string is cleaned of any `word:value` tokens before being passed to `nova.ai.react_agent()`, which runs a **multi-step ReAct reasoning loop** (up to 6 steps) with internet access.

---

#### Code Agent

This is the most complex execution path:

1. `nova.ai.generate_code(job)` generates Python code
2. The code is sent to the code window UI via `nova.code_window.set_code(code)`
3. A live preview is updated in the code display widget (on the main thread)
4. The code is executed in a **background thread** via `nova.smart_loop.run(code)`, which handles retries and error correction
5. When execution completes, the result is delivered back to the UI via `nova.root.after(0, lambda: nova._deliver_tool_result(result))`
6. The method immediately returns `"[RUNNING CODE...]"` so the UI stays responsive throughout

---

#### Math and Text Agents

Both call `nova.ai.generate(job)` directly. The difference is semantic — math implies LaTeX/formula output, text implies conversational prose — but the underlying call is identical.

---

#### File Command Normalisation: `_translate_file_command(text)`

Before `file_explorer` receives its task, the text is normalised:
- Noise phrases like `"contents of"`, `"files and folders in"`, `"show contents of"` are stripped
- Drive-letter paths (`C:/...`) are detected and prefixed with `"list "`
- Requests mentioning `"text file"` or `".txt"` are converted to `"find *.txt in C:/Users/OEM/Desktop"`
- Requests mentioning `"desktop"` and `"list"` are mapped to `"list C:/Users/OEM/Desktop"`

---

## 4. The Tools — What NOVA Can Do

### File Explorer (`tools/file_explorer.py`)

A comprehensive local filesystem interface supporting:

| Command | Description |
|---|---|
| `list <path>` | List directory contents with sizes |
| `read <path>` | Read a file (up to 30,000 chars) |
| `find *.ext in <dir>` | Recursive extension search (up to 200 results) |
| `search <keyword> in <dir>` | Search filenames by keyword |
| `tree <path>` | Show directory tree (max depth 3) |
| `copy <src> to <dst>` | Copy a file |
| `move <src> to <dst>` | Move a file |
| `save <path> <content>` | Write text to a file |
| `delete <path>` | Delete a file |
| `open <path>` | Open with default OS application |

It also resolves shortcut names (`desktop`, `documents`, `downloads`, `music`, `videos`, `home`) to their full system paths, and normalises Windows backslashes to forward slashes.

---

### Audio Tools (`tools/audio_tools.py`)

`play_audio_from_url(url)`:
- Downloads audio from a URL into a temporary `.mp3` file
- Launches it with `subprocess.Popen(["start", path], shell=True)` — uses the Windows default media player
- Returns a confirmation string

---

### Diagram Tool (`tools/diagram_tool.py`)

`diagram(description, ai, output_dir="diagrams")`:

1. If the description already contains `->` arrows, it is used directly as an edge list
2. Otherwise, the AI is prompted to convert the description into a `A -> B` edge list
3. `_create_graphviz_diagram(text)` parses the edge list and creates a `graphviz.Digraph` with:
   - Left-to-right layout (`rankdir="LR"`)
   - Orthogonal splines
   - Rounded, light-blue filled box nodes
4. The diagram is rendered to a PNG file in the `diagrams/` directory
5. Returns `"DIAGRAM:<path>"` which the executor intercepts to display in the UI

---

### Document Tools (`tools/document_tools.py`)

`summarise_document_from_source(source)`:
- Accepts a URL (local paths are rejected)
- Automatically converts arXiv abstract URLs (`/abs/`) to PDF URLs (`/pdf/`)
- Downloads the file via `download_file()`
- Reads it with `read_document()` (a separate document reader module)
- Returns the first **20,000 characters** of raw text for the AI to summarise

---

### Download Tools (`tools/download_tools.py`)

`download_file(url, download_dir="downloads")`:
- Validates the URL format
- Infers filename from the URL path
- Fixes missing extensions (defaults to `.pdf` for arXiv and extension-less URLs)
- Downloads in **8 KB chunks** with a **30-second timeout**
- Uses a custom `User-Agent` header (`NovaAssistant/1.0`)
- Returns the local file path on success, or an error string on failure

---

### Image Search Tool

`search_and_show_image(query, internet_tools, image_dir)`:
- Uses internet tools to search for images matching the query
- Downloads results to `image_dir`
- Displays them as a grid in the NOVA UI
- The executor pre-cleans the query and extracts a count before calling this tool

---

### Web Tools

`open_webpage(url, internet_tools)`:
- Opens a URL in the system browser or fetches its content
- Accepts internet tools for cases where content retrieval is needed

---

## 5. End-to-End Data Flow

Here is the complete journey from user input to delivered result:

```
User types a message
        │
        ▼
TaskPlanner.create_plan(user_input, history_str)
  ├── Fast-path keyword check (images, plots)
  │       └── Returns plan immediately if matched
  └── AI prompt → JSON plan (with up to 3 retries)
        │
        ▼
Plan: { "mode": "sequential"|"parallel", "tasks": [...] }
        │
        ▼
AgentExecutor.run_tasks() or run_tasks_sequential()
        │
        ├── [parallel] ThreadPoolExecutor (max 4 workers)
        │       └── Each task → _run_agent()
        │
        └── [sequential] Loop over tasks
                ├── Inject accumulated context into task description
                ├── Inject image paths if previous task was image search
                └── Each task → _run_agent()
                        │
                        ▼
                Agent routing:
                ├── tool_map agents → nova.tools.run(tool_name, ...)
                ├── diagram         → graphviz render → UI display
                ├── research        → nova.ai.react_agent() (ReAct loop, up to 6 steps)
                ├── code            → generate → preview → background execute → deliver
                ├── math / text     → nova.ai.generate()
                └── fallback        → nova.ai.generate()
                        │
                        ▼
                Result string returned
                        │
        ▼
Sequential: result accumulated as context for next task
        │
        ▼
All results collected → delivered to UI
(via nova._deliver_tool_result() or direct UI update)
        │
        ▼
User sees the response
```

---

## 6. Key Design Principles

| Principle | How It's Implemented |
|---|---|
| **Context threading** | Sequential mode actively passes output between steps, enabling multi-step reasoning without the user re-stating context |
| **UI thread safety** | All UI updates are dispatched via `root.after(0, lambda: ...)` to ensure they run on the main Tkinter thread while heavy work runs in background threads |
| **Graceful degradation** | Every agent path has a fallback; the planner falls back to a plain `text` task; the executor wraps every agent call in `try/except` and returns `[AGENT ERROR] agent: error` rather than crashing |
| **Strict agent whitelisting** | The planner only accepts tasks whose agent names appear in `VALID_AGENTS`, preventing hallucinated or invalid agent names from reaching the executor |
| **Self-healing chains** | The executor automatically appends a `text` agent after `self_inspect`, auto-plays detected audio files, and stops research chains early when no actionable result is found — all without user intervention |
| **Fast-path optimisation** | Common unambiguous requests (images, plots) bypass the AI planner entirely via keyword matching, reducing latency |

---

*This explanation was generated from a live inspection of NOVA's source code (41,813 characters inspected) on 24 March 2026.*