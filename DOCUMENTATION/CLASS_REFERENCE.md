# Nova Assistant — Complete Class Reference

Here's the full breakdown of every class in Nova's source code, based on direct self-inspection of 63,844 characters of source.

---

## 🏗️ Core Application

### `NovaAssistant(NovaTTS, NovaSelfImproveUI, NovaRouter)`
The **main application class** — the beating heart of the whole system. Inherits from three mixins. Responsibilities:
- Builds the entire Tkinter UI (header, left panel, right panel, input, buttons)
- Initialises the AI backend (`WorkingAI`), tools, planner, executor, and manager
- Manages application state (`nova_state.json`) — load/save across sessions
- Handles window dragging, minimise, maximise
- Routes user input through tools → AI → planner pipeline
- Owns the conversation history display and code panel

---

## 🤖 AI & Routing

### `WorkingAI`
The **AI engine wrapper**. Handles:
- Generating responses via local Ollama models or cloud APIs
- Switching between local/cloud transparently
- Running the ReAct agent loop (reason → act → observe)
- Code generation with error context
- PDF text extraction
- Disk-based caching for error search results
- Token tracking and callbacks

### `NovaRouter`
The **input routing mixin** — decides *what to do* with each user message:
- Classifies intent (text, math, code, story, PDF Q&A)
- Dispatches to the appropriate handler
- Manages internet search (blocking and non-blocking)
- Builds history context for prompts
- Handles ReAct trigger detection
- Plays contextual sounds after responses

### `ManagerAgent`
A **supervisor agent** that:
- Analyses multi-step plans before execution
- Supervises task results for quality
- Coordinates between planner and executor
- Acts as a meta-layer over the agent executor

---

## 🧠 Planning & Execution

### `TaskPlanner`
Turns a user request into a **structured execution plan**:
- Detects follow-up questions vs new topics
- Extracts relevant conversation context
- Handles topic tracking across exchanges
- Cleans and validates AI-generated plans

### `AgentExecutor`
**Runs the planned tasks** one by one (or in parallel):
- Executes each agent step
- Handles file command translation
- Formats history for agent context
- Manages code preview and execution callbacks

### `CodeExecutionLoop`
The **smart code generation and repair loop**:
- Iteratively generates, runs, and fixes code
- Detects error loops and duplicate code
- Scores output quality
- Fetches documentation context for libraries
- Uses cached solutions for known error patterns
- Manages plot cleanup between runs

---

## 🛠️ Self-Improvement

### `NovaSelfImproveUI`
The **UI mixin for Nova's self-improvement tools**:
- Evolution worker — adds new features to Nova's own source
- Debug worker — diagnoses symptoms in the codebase
- Diagnostic worker — analyses source files for issues
- Documentation worker — generates docstrings automatically
- Shows results in the code window for review

### `SelfImprover`
The **actual self-modification engine**:
- Reads, patches, and writes Nova's own Python source files
- Manages versioned backups before any change
- Validates new code before writing
- Decomposes feature requests into atomic steps
- Runs multi-step feature addition cycles
- Generates and fixes docstrings
- Runs diagnostic analysis and parses issues

### `MistakeMemory`
Nova's **long-term error learning system**:
- Saves failed code attempts with context
- Classifies tasks and extracts library names
- Generates lessons from mistakes
- Prevents duplicate mistake entries
- Returns relevant warnings before new code attempts
- Exports lessons as readable summaries

---

## 🎙️ Speech & Audio

### `NovaTTS`
The **text-to-speech mixin**:
- Manages a background TTS worker thread (COM-safe)
- Supports multiple TTS engines including Edge TTS (async)
- Plays chime sounds
- Builds the TTS UI panel with voice/rate controls
- Handles math-mode speech (reads equations differently)

### `WhisperHandler`
The **speech-to-text handler**:
- Loads Whisper ASR models (GPU/CPU)
- Records audio from microphone
- Transcribes recordings and inserts text into the input box
- Tracks recording duration

### `ASR`
A **thin wrapper around faster-whisper**:
- Loads model with configurable device and compute type
- Exposes a single `transcribe(audio, sample_rate)` method

---

## 🖥️ UI Components

### `CodeWindow(tk.Toplevel)`
A **full code editor and execution sandbox**:
- Displays and edits Python code with syntax highlighting
- Manages a sandboxed virtual environment
- Installs missing packages automatically
- Runs code in a subprocess with stdout/stderr capture
- Handles plotting (intercepts `plt.show()`, saves PNGs)
- Sends output back to the AI for analysis

### `CodeDisplay`
A **read-only code viewer widget**:
- Syntax highlighting for Python
- Line numbers
- Mouse wheel scrolling
- Copy to clipboard (with or without line numbers)
- Context menu

### `LatexWindow(tk.Toplevel)`
A **LaTeX rendering panel**:
- Splits text into prose and math blocks
- Renders math expressions as PNG images via matplotlib
- Supports zoom, font size controls, and copy raw LaTeX
- Appends or replaces document content

### `_CanvasTooltip`
A **lightweight tooltip** for canvas widgets — shows on hover, hides on leave. Small but quietly essential.

---

## 🌐 Internet & Tools

### `InternetTools`
Nova's **internet access layer**:
- Brave Search API integration
- Weather fetching via Open-Meteo (geocoded)
- ArXiv paper fetching and chunked search
- GitHub README fetching
- URL fetching with HTML cleaning
- Image search and download
- PDF text extraction
- Smart query extraction from natural language

---

## 📄 Paper Analysis

### `PaperToolsWindow(tk.Toplevel)`
A **dedicated research paper analysis window**:
- Summarises papers
- Extracts algorithms and examples
- Implements algorithms as runnable code
- Runs custom AI queries against loaded paper text
- Plays a chime when done

---

## 🎨 Theming

### `ThemeManager`
Applies **colour themes** across the entire UI:
- Recursively recolours all widgets
- Adjusts foreground based on luminance
- Supports named theme presets

### `ThemePicker(tk.Toplevel)`
A **visual theme selection dialog** with colour swatches.

---

## Summary Table

| Class | Role |
|---|---|
| `NovaAssistant` | Main app — UI orchestrator and session manager |
| `WorkingAI` | AI engine (local Ollama + cloud APIs) |
| `NovaRouter` | Input routing & intent classification |
| `ManagerAgent` | Multi-step task supervisor |
| `TaskPlanner` | Converts requests into structured plans |
| `AgentExecutor` | Executes planned tasks step by step |
| `CodeExecutionLoop` | Smart code generation, repair, and scoring |
| `NovaSelfImproveUI` | Self-improvement UI mixin |
| `SelfImprover` | Live source code modification engine |
| `MistakeMemory` | Long-term error learning & warnings |
| `NovaTTS` | Text-to-speech (multi-engine, COM-safe) |
| `WhisperHandler` | Microphone recording & transcription |
| `ASR` | faster-whisper transcription wrapper |
| `CodeWindow` | Code editor, sandbox, and plot capture |
| `CodeDisplay` | Read-only syntax-highlighted code viewer |
| `LatexWindow` | LaTeX/math expression renderer |
| `_CanvasTooltip` | Hover tooltips for canvas widgets |
| `InternetTools` | Web search, weather, ArXiv, PDF, images |
| `PaperToolsWindow` | Research paper analysis & code extraction |
| `ThemeManager` | Recursive UI colour theming |
| `ThemePicker` | Visual theme selection dialog |

**21 classes** in total — ranging from the top-level orchestrator down to a tooltip. Quite the ensemble cast.