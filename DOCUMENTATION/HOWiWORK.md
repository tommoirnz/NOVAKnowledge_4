# Nova Assistant — How I Work: Complete Architecture & Self-Inspection

*Self-inspection performed: Monday 23 March 2026, 18:45 NZST — Auckland, New Zealand*

---

## Overview

Nova is a sophisticated AI desktop assistant built with **Python and Tkinter**. It follows a **multi-layered architecture** combining:

- Local LLM inference via **Ollama**
- Cloud model routing via **OpenRouter**
- A **ReAct agent loop** for agentic reasoning
- A **multi-agent pipeline** via `ManagerAgent`
- **Voice I/O** via Whisper + PyAudio
- **Sandboxed code execution** with error learning
- **Self-improvement** capabilities (Nova can modify its own source code)
- A custom dark-themed, frameless **Tkinter GUI**

---

## 1. Core Architectural Layers

```
┌─────────────────────────────────────────────────────────┐
│                    NOVA GUI (Tkinter)                    │
│         NovaAssistant — root orchestrator class          │
├──────────────┬──────────────┬───────────────────────────┤
│  WorkingAI   │ ManagerAgent │    WhisperHandler          │
│  (LLM core)  │ (multi-agent)│    (voice input)           │
├──────────────┴──────────────┴───────────────────────────┤
│         Tool Layer  (ToolRegistry + InternetTools)       │
├─────────────────────────────────────────────────────────┤
│   Code Execution   │  MistakeMemory  │  SelfImprover     │
├─────────────────────────────────────────────────────────┤
│  Ollama (local)    │  OpenRouter (cloud)  │  TTS/ASR     │
└─────────────────────────────────────────────────────────┘
```

---

## 2. `WorkingAI` — The LLM Engine

This is the **central inference engine**, handling all text generation with a two-stage planning architecture.

### 2.1 Model Routing

```python
def _is_cloud_model(self, name):
    return name in self.cloud_model_ids or
           name.startswith("☁") or
           name.startswith("cloud:")
```

Every generation call routes to one of two backends:

- **`_generate_ollama()`** — local HTTP POST to `localhost:11434`
- **`_generate_cloud()`** — OpenRouter-compatible REST API

The model is selected at runtime from the UI combo box. Cloud models are prefixed with `☁` in the UI.

---

### 2.2 Two-Stage Planning (`generate()`)

```
User Prompt
    │
    ▼
[Skip planning?] ── yes ──► Direct generation
    │ no
    ▼
Planning prompt → LLM → numbered plan (≤5 steps)
    │
    ▼
Answer prompt (plan + original request) → LLM → final answer
```

**Planning is skipped when:**
- The prompt contains code-generation keywords
- The prompt is shorter than **120 characters**
- `use_planning=False` is explicitly passed

This avoids unnecessary token overhead for simple or mechanical tasks like code fixes.

---

### 2.3 Code Generation (`generate_code()`)

Three distinct prompt templates are selected based on context:

| Condition | Template Used |
|-----------|--------------|
| Has `PREVIOUS CONTEXT:` | Memory-aware continuation prompt |
| Has `error_context` + `error_type` | Error-fix prompt |
| Fresh task | Full task prompt with matplotlib rules |

Matplotlib-specific rules are injected **only when mathtext patterns are detected** in the task string, avoiding unnecessary token usage.

---

### 2.4 ReAct Agent Loop (`react_agent()`)

Implements the **Reasoning + Acting** pattern across a maximum of **6 steps**:

```
for step in range(max_steps=6):
    │
    ▼
  Build prompt (history + internet_ctx + task)
    │
    ▼
  LLM generates: Thought + Action OR Final
    │
    ├── "Final:" found → return answer
    │
    └── "Action:" found → parse tool call
              │
              ├── search(query)    → Brave search
              ├── read_url(url)    → fetch webpage
              └── read_pdf(url)   → download + extract PDF
              │
              ▼
         Observation appended to history
         Loop continues
```

**Loop detection** prevents infinite cycles:
```python
action_key = f"{tool}:{arg[:80]}"
if action_key in recent_actions:
    return "I was unable to find the information..."
```

**PDF handling** is special — after `read_pdf`, title and authors are extracted **in Python** (not by the LLM) to prevent hallucination:
```python
for line in observation.splitlines():
    if l.lower().startswith("title:") and not extracted_title:
        extracted_title = l.split(":", 1)[1].strip()
```

---

## 3. `NovaAssistant` — The Root Orchestrator

This is the **root class** that owns and coordinates all subsystems.

### 3.1 Intent Classification Pipeline

```
User input (_process_input)
    │
    ▼
_classify_intent()
    │
    ├── PDF Q&A          → _handle_pdf_qa()
    ├── Diagram request  → _handle_diagram_intent()
    ├── Story request    → _handle_story_intent()
    ├── Math intent      → _handle_math_intent()
    ├── Code intent      → _handle_code_intent()
    ├── ReAct trigger    → _handle_react()
    ├── Internet search  → _handle_internet_search()
    └── Text/general     → _handle_text_intent()
```

Each handler runs as a **separate background worker thread** to keep the UI responsive.

---

### 3.2 Tool Selection (Two Layers)

Nova uses two layers of tool selection:

1. **Rule-based** (`try_tool`) — fast keyword/pattern matching
2. **AI-based** (`ai_choose_tool` / `try_ai_tool`) — LLM scores candidate tools against the user input

```python
def score(p):
    # LLM scores each tool profile against the user input
```

---

### 3.3 Conversation Management

Nova maintains conversation state across multiple layers:

- **In-memory history** — `_build_history_context()`, `build_recent_history(n=8)`
- **JSON persistence** — `save_state()` / `load_state()`
- **Detachable conversation panel** — `_toggle_detach_conv()` / `_detach_conv()`

Messages are rendered with:
- Code block detection and syntax highlighting (`_display_with_code_blocks`)
- Markdown cleaning (`_clean_markdown`)
- Clickable link detection (`_make_links_clickable`)
- LaTeX rendering via browser (`_render_latex_in_browser`)

---

## 4. `ManagerAgent` — Multi-Agent Pipeline

```
User input
    │
    ▼
analyse(plan)           ← breaks task into sub-tasks
    │
    ▼
execute(plan, executor) ← runs each sub-task via WorkingAI/tools
    │
    ▼
supervise(results)      ← reviews outputs, checks quality
    │
    ▼
supervise_plan(plan)    ← validates the plan itself
```

This enables **complex multi-step queries**, for example:

> *"Get the NZD/USD rate and calculate $10,000 NZD alongside EUR and GBP, then plot it"*

The manager decomposes this into sub-tasks, executes each step independently, and synthesises the results into a final answer.

---

## 5. `WhisperHandler` — Voice Input

```
_start_rec()
    │
    ▼
_record()              ← PyAudio capture in background thread
    │
    ▼
stop_recording()
    │
    ▼
_proc()                ← Whisper model inference
    │
    ▼
_insert(text)          ← injects transcription into input box
```

Key features:
- Uses **Whisper** (via `asr_whisper.ASR`) with configurable model size
- Supports **CUDA acceleration**
- **Push-to-talk** mode via spacebar (`_space_press` / `_space_release`)
- Animated recording ring with timer display

---

## 6. Code Execution System

### Execution Flow

```
_handle_code_intent()
    │
    ▼
_ask_code_permission()    ← user confirms execution
    │
    ▼
_run_autocoder()
    │
    ▼
CodeExecutionLoop         ← sandboxed execution with error retry
    │
    ├── Success → _on_sandbox_output()
    └── Error   → _on_goof() → _review_mistake()
                                    │
                                    ▼
                              MistakeMemory.save()
```

### Error Learning

```python
def _review_mistake(self, task, error_type, code, output):
    # User can save or discard the lesson
    # Saved lessons feed back into future generate_code() calls
```

`MistakeMemory` persists error patterns to disk as a JSON cache. On future similar tasks, the cached fix is injected into the prompt via `_get_cached_error_search()`, allowing Nova to avoid repeating the same mistakes.

---

## 7. Self-Improvement (`SelfImprover`)

Nova can **evolve its own source code**:

```
_run_evolution()
    │
    ▼
_evolution_worker()
    │
    ▼
SelfImprover.improve()    ← reads own source, generates patch
    │
    ▼
_show_evolution_history() ← diff view of changes
```

Similarly, `_run_debug()` → `_debug_worker()` analyses reported symptoms against the current source code and proposes targeted fixes. Both systems operate on the live source file.

---

## 8. Diagram Generation

Two backends are tried in order:

```
_handle_diagram_intent()
    │
    ├── try_generate_diagram()      ← parse "draw: A -> B -> C"
    │
    ├── create_graphviz_diagram()   ← Graphviz/DOT (PNG output)
    │       └── show_graphviz_diagram()  ← zoomable/pannable canvas
    │
    └── create_tikz_block_diagram() → compile_tikz() → pdflatex
            └── show_diagram()          ← PDF viewer
```

Graphviz diagrams support:
- **Mouse wheel zoom**
- **Click-and-drag pan**
- **Fit-to-window**

---

## 9. Ollama Lifecycle Management

```python
check_ollama_running()        # polls /api/tags
    │ not running
    ▼
start_ollama()                # launches ollama.exe hidden
    │
    ▼
wait_for_ollama(timeout=15)   # polls every 1 second
```

A background thread (`_background_ollama_poller`) continuously monitors Ollama availability and updates the model list via `_refresh_models()`.

---

## 10. UI Architecture

The UI is a **frameless Tkinter window** with custom chrome:

```
Root Window (BG_ROOT #0D0F14)
├── Header bar (drag-to-move, minimize, maximize)
├── Left panel (BG_LEFT)
│   ├── Model selector panel
│   ├── Whisper/voice panel
│   ├── History row
│   └── Debug console (system log)
├── Right panel (BG_RIGHT)
│   ├── Conversation panel (scrollable canvas)
│   │   └── Message frames (user/assistant)
│   ├── Code panel
│   ├── TTS panel
│   └── Input panel
│       ├── Text input with placeholder
│       └── Action buttons (send, document, diagnose, etc.)
└── Resize handle (bottom-right)
```

**Key UI features:**
- **Detachable panels** — conversation and system log can be undocked to separate windows
- **Canvas tooltips** (`_CanvasTooltip`) — custom hover tooltips on canvas buttons
- **Animated elements** — recording ring, nova flash, search bar, cursor blink, thinking dots
- **Theme system** — `ThemeManager` / `ThemePicker` / `THEMES`
- **Custom fonts** — Orbitron, Rajdhani, Consolas, Courier New

---

## 11. TTS (Text-to-Speech)

Two engines are supported:

| Engine | Method |
|--------|--------|
| System TTS (pyttsx3) | `_init_tts_engine()` → `speak_text()` |
| Edge TTS (Microsoft) | `_speak_edge()` → async `asyncio` runner |

Math-aware speech is provided via `MathSpeechConverter`, which converts LaTeX expressions into speakable natural language form before synthesis.

---

## 12. PDF & Document Handling

```
_handle_pdf_button()
    │
    ├── Local file  → _load_local_pdf()
    └── URL         → resolve_pdf_url() → download_pdf()
                            │
                            ▼
                    extract_pdf_text() (PyMuPDF/fitz)
                            │
                            ▼
                    _run_doc_summary() or _handle_pdf_qa()
```

`resolve_pdf_url()` handles:
- arXiv `/abs/` → `/pdf/` URL conversion
- DOI → Springer PDF URL resolution
- Direct `.pdf` URLs

---

## Complete Component Summary

| Component | Role | Key Technology |
|-----------|------|---------------|
| `WorkingAI` | LLM inference + two-stage planning | Ollama / OpenRouter |
| `NovaAssistant` | UI + intent routing + orchestration | Tkinter |
| `ManagerAgent` | Multi-step task decomposition + supervision | Prompt chaining |
| `WhisperHandler` | Voice input + push-to-talk | OpenAI Whisper + PyAudio |
| `CodeExecutionLoop` | Sandboxed code runner with retry | subprocess |
| `MistakeMemory` | Error pattern learning + caching | JSON cache |
| `SelfImprover` | Source code evolution + debugging | LLM + diff |
| `ToolRegistry` | Tool dispatch | Plugin pattern |
| `InternetTools` | Web search + page fetch | Brave API + requests |
| `ReAct loop` | Agentic reasoning (max 6 steps) | ReAct pattern |
| `MathSpeechConverter` | LaTeX → speakable text | Custom parser |
| `ThemeManager` | UI theming | Tkinter + THEMES dict |

---

*Self-inspection processed 41,305 characters of internal source context to produce this explanation.*

---

**Sources:** *(No external URLs were referenced — this explanation is derived entirely from Nova's own internal source code inspection.)*