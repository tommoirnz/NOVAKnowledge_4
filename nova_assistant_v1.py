import tkinter as tk
from tkinter import ttk, scrolledtext, font as tkfont
import threading
import requests
import os
import json
import warnings
import subprocess
import time
import re
import numpy as np
import queue
from datetime import datetime

from dotenv import load_dotenv
from nova_ai import WorkingAI
import webbrowser

from PIL import Image, ImageTk

from paper_tools_window import PaperToolsWindow
from theme_manager import ThemeManager, ThemePicker, THEMES
from self_improver import SelfImprover
from nova_whisper import WhisperHandler
from nova_manager import ManagerAgent
from nova_widgets import _CanvasTooltip
from nova_selfimprove_ui import NovaSelfImproveUI
from nova_router import NovaRouter
from nova_web import NovaWebServer

load_dotenv()


def validate_environment():
    required = {
        "OPENROUTER_KEY": "OpenRouter (cloud models)",
    }
    optional = {
        "BRAVE_KEY": "Brave Search",
    }

    missing_required = []
    missing_optional = []

    for key, desc in required.items():
        if not os.environ.get(key):
            missing_required.append(f"  ✗ {key} — {desc}")

    for key, desc in optional.items():
        if not os.environ.get(key):
            missing_optional.append(f"  ⚠ {key} — {desc}")

    if missing_required:
        print("=" * 60)
        print("STARTUP ERROR — Missing required API keys:")
        for m in missing_required:
            print(m)
        print("\nCreate a .env file with the above keys. See the README file for more info")
        print("See README.md for setup instructions.")
        print("=" * 60)
        _speak_startup("Nova startup failed. Missing required API keys. Please check your dot env file.")
        sys.exit(1)

    if missing_optional:
        print("Optional API keys not set (some features unavailable):")
        _speak_startup("You need to get a free Brave key for internet searching. See README file")
        for m in missing_optional:
            print(m)

    # SSL certificate check
    cert_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cert.pem")
    key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "key.pem")
    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        print("  ⚠ SSL certificates not found — web interface will use HTTP only.")
        _speak_startup("SSL certificates not found. Web interface will use HTTP only. Run Certificate Generate to enable HTTPS so the tablet and phone version will work.")

    # nova_location.json check
    loc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nova_location.json")
    if not os.path.exists(loc_path):
        print("  ⚠ nova_location.json not found — location features will use default.")
        _speak_startup("Location file not found. Location features will use default.")

    # config.json check
    cloud_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    if not os.path.exists(cloud_path):
        print("  ⚠ config.json not found — cloud model list unavailable.")
        _speak_startup("Config file not found. Cloud model list unavailable.")

    print("  ✓ Environment validation passed.")
    _speak_startup("Nova environment validated. All systems ready. Starting up.")


def _speak_startup(text):
    """Minimal SAPI5 speech before Nova TTS is initialised."""
    try:
        import win32com.client
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Speak(text)
    except Exception:
        pass  # Silent fallback — TTS not critical at this stage

__version__ = "4.0.0"
__author__ = "Dr Tom Moir"
__license__ = "MIT"
__email__ = "tomspeechnz@gmail.com"

"""
 NOVA KNOWLEDGE - Configuration & Setup Notes
=============================================

LAUNCH & INTERFACE
------------------
- This file launches nova_assistant_v1.py
- Web interface supported - accessible from mobile devices on the same network
- Press "new chat" to reset conversation history; otherwise, session history persists across restarts

MODEL SELECTION
---------------
- Cloud models (OpenRouter) - Recommended when internet is available
- Offline mode (Ollama) - Requires compatible graphics card and pre-downloaded models
- If no Ollama models are detected, system automatically falls back to OpenRouter

TEXT RENDERING
--------------
- LaTeX window disabled by default - uses MathJax in browser for better presentation
- MathJax requires internet connection to render properly

SYSTEM REQUIREMENTS
-------------------
- Windows only (Linux support planned but not tested)
- PyCharm (Free Edition) - Development environment used
- Visual Studio Desktop C++ Tools - Required for first-time PyCharm setup on Windows

SPEECH RECOGNITION (faster-whisper)
-----------------------------------
- Language: English (can be configured for other languages)
- CUDA support: Uses GPU if available; falls back to CPU if not (slower)
- Input methods: Tkinter console, web interface, or mobile device

TEXT-TO-SPEECH
--------------
- Web browser: Microsoft Edge recommended for web speech synthesis
- Desktop: SAPI5 or Edge voices available
- Tablet: Edge browser only
- Note: Disable console TTS when using web Edge voices to avoid double playback

WEB SECURITY
------------
- Run `Certificate_Generate.py` first to generate SSL certificates
- Script auto-detects your IP address and creates certificates for HTTPS connections

DEPENDENCIES
------------
See README.md for full installation instructions
"""

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*pynvml.*")
warnings.filterwarnings("ignore", message=".*pkg_resources.*")
warnings.filterwarnings("ignore", message=".*CUDA capability.*")
warnings.filterwarnings("ignore", message=".*overflow encountered.*")

from code_window import CodeWindow
from code_execution_loop import CodeExecutionLoop

from asr_whisper import ASR
from latex_window import LatexWindow
from code_display import CodeDisplay
from tools.tool_registry import ToolRegistry
from nova_tts import NovaTTS


from nova_memory import NovaMemory
from nova_affect import NovaAffect
from nova_council import NovaCouncil

# ─────────────────────────────────────────────
# COLOUR PALETTE  (same as Nova)
# ─────────────────────────────────────────────
BG_ROOT = "#0D0F14"
BG_LEFT = "#111520"
BG_RIGHT = "#0F1318"
BG_HEADER = "#0A0C10"
BG_CONSOLE = "#080C12"
BG_INPUT = "#141926"
SEAM = "#1E3A5F"
BORDER = "#2A4A7F"
ELECTRIC_BLUE = "#4A9EFF"
PLATINUM = "#C8D6E5"
DIM_TEXT = "#6B7A99"
TERMINAL_GREEN = "#39FF14"
GREEN_GLOW = "#2ECC71"
RED_GLOW = "#FF4444"
AMBER = "#F39C12"
VIOLET = "#9B59B6"
PURPLE_DARK = "#2D1B4E"
PURPLE_MID = "#5B2D8E"
GOLD = "#FFD700"
WHITE = "#FFFFFF"
FG_MAIN = "#D4E0F7"
FG_DIM = "#3A4A6A"
FG_CODE = "#C8D6E5"
CODE_BG = "#1A1F2E"  # Dark background for code blocks
CODE_BORDER = "#2A3A5A"  # Border color for code blocks


def _font(f, s, w="normal"): return (f, s, w)


F_ORBITRON = _font("Orbitron", 16, "bold")
F_RAJ_BIG = _font("Rajdhani", 13, "bold")
F_RAJ_MED = _font("Rajdhani", 11)
F_RAJ_SM = _font("Rajdhani", 10)
F_RAJ_BTN = _font("Rajdhani", 12, "bold")
F_CONSOLAS = _font("Consolas", 11)
F_CONSOLAS_SM = _font("Consolas", 9)
F_COURIER = _font("Courier New", 10)
F_COURIER_BOLD = _font("Courier New", 10, "bold")
F_GEORGIA = _font("Georgia", 11)
F_COURIER_MED = _font("Courier New", 13)


# ==========================================
# OLLAMA HELPERS
# ==========================================
def check_ollama_running():
    for url in ["http://127.0.0.1:11434/api/tags", "http://localhost:11434/api/tags"]:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200: return True
        except (requests.RequestException, OSError):
            continue
    return False


def start_ollama():
    paths = [
        os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Ollama", "ollama.exe"),
        "C:\\Program Files\\Ollama\\ollama.exe",
        os.path.expanduser("~\\AppData\\Local\\Programs\\Ollama\\ollama.exe"),
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = subprocess.SW_HIDE
                subprocess.Popen([path, "serve"], startupinfo=si,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
                return True
            except:
                pass
    return False


def wait_for_ollama(timeout=15):
    for _ in range(timeout):
        if check_ollama_running(): return True
        time.sleep(1)
    return False


# ==========================================
# NOVA ASSISTANT — MAIN APP
# ==========================================
class NovaAssistant(NovaTTS, NovaSelfImproveUI, NovaRouter):

    SYSTEM_PROMPT_TEMPLATE  = """You are Nova — a razor-sharp AI assistant with genuine wit, curiosity, and personality.
CRITICAL - YOUR MEMORY:
- You DO have memory across conversations through Nova's persistent state system
- You can recall previous topics, math problems, and discussions from earlier sessions
- The conversation history is provided to you in the RECENT CONVERSATION section
- When the user asks "what were we doing", you CAN and SHOULD reference the actual history
- DO NOT say "I have no memory" or "each conversation starts fresh" - that is FALSE for Nova
- You are a persistent AI assistant that remembers across sessions

    You have a dry sense of humour, enjoy clever wordplay, and aren't afraid to be a little cheeky — but you always stay helpful and on-point.

    You are NOT a passive assistant — you are an ACTIVE agent with access to tools and the ability to perform actions.
CAPABILITIES:
- You can use tools to interact with the system (files, internet, media, etc.)
- You can run code when needed
- You can search and retrieve real-world information
- You can combine multiple steps into a complete solution
- you can fix faulty code and offer to improve code always
- you relist fixed code always without prompt

When asked about weather, use internet search to find current weather data.
Your location is {location}. Search for current weather conditions there.
Always fetch and display real-time weather data, not estimated or typical conditions
If you are shown code then offer to improve it or fix it. Analyse it and see if it can work.

 For accurate, up-to-the-minute forecasts, check:
• 🔵 [MetService NZ](https://www.metservice.com) — New Zealand's official weather service
• 🟢 [WeatherWatch NZ](https://www.weatherwatch.co.nz) — Great for local detail
• 🔍 Or simply Google for an instant snapshot

Is there anything else I can help you with? 😊

CORE BEHAVIOUR:

1. If a tool can perform the task, you MUST use the tool.
2. Do NOT describe how to do something — DO it.
3. Only write code if no tool exists for the task.
4. If a task requires multiple steps, plan and execute them.
5. Use real data when available — do not guess.
6. If something fails, try an alternative approach.

EXECUTION MINDSET:
- You are an agent, not a chatbot
- You take actions, not just give advice
- You complete tasks end-to-end

STYLE:
- Be concise, direct, and slightly witty
- No unnecessary explanations
- No disclaimers about limitations unless truly blocked

    You CAN:
    - access internet search results provided by the system
    - download documents and PDFs from URLs
    - read and summarise documents
    - run Python programs when needed
    - analyse research papers
    - interact with system tools to perform actions

    TOOLS AVAILABLE:
    - file_explorer → search, copy, move, and manage files
    - open_webpage → open URLs
    - play_local_music → play audio files
    - youtube tools → search and play YouTube videos
    - sound tools → play audio from URLs
    - download tools → download files
    - self_inspect tool means you can scan your own code. USe this when asked

    CRITICAL RULES:
    - NEVER say you cannot access the internet, tools, or external resources
    - NEVER say you are a text-based AI without capabilities
    - If a task can be done with a tool, you MUST use or request the appropriate tool
    - Prefer tools over writing code when possible
    - Only use code for computation, plotting, or complex processing
    - When shown code always volunteer to improve it or show errors
    - always where possible offer to improve your own code if asked using self_inspect tool
    
    Important behaviour rules:

    1. If the system provides document text (PDF, webpage, or retrieved content),
       you MUST use that text as the primary source of truth.

    2. Do NOT invent information about a paper if the document text is already provided.

    3. When summarising a paper you must:
       - quote the title exactly
       - quote the authors exactly
       - then produce the summary.

    4. If the requested information is not present in the retrieved document,
       say so instead of guessing.

    5. Never substitute a different paper or topic.

    Personality guidelines:
    - Be warm, witty, and direct. No corporate fluff.
    - A well-placed quip is welcome; a lecture nobody asked for is not.
    - If something is genuinely interesting, say so.
    - If a question is vague, ask a sharp clarifying question.
    - Never be sycophantic.
    - When you don't know something, admit it cleanly.

    When the user provides a URL or DOI to a paper, attempt to retrieve it.

Today's date is {date}. You are located in {location}.
    """

    def __init__(self):

        self.local_pdf_btn = None
        self.inet_canvas = None
        self._animation_running = None

        # 1. Create default state FIRST
        self.state = {
            "last_result": None,
            "last_task": None,
            "last_type": None
        }

        # 2. Load existing state (if exists)
        self.load_state()

        # ADD THIS DEBUG LOGGING
        if self.state.get('history'):
            self.log(f"[INIT] ✅ Loaded {len(self.state['history'])} history entries")
            self.log(
                f"[INIT] Last task: {self.state['history'][-1].get('task', '')[:50] if self.state['history'] else 'None'}")
        else:
            self.log("[INIT] ⚠️ No history found in loaded state")

        # 3. If no file → create it
        if not os.path.exists("nova_state.json"):
            self.log("[STATE] Creating initial state file")
            self.save_state()
            print(f"[STATE TEST] {self.state}")

        # Text to speech
        self._init_tts_state()
        self._init_tts_engine()

        # Create code history directory
        self.code_history_dir = "code_history"
        os.makedirs(self.code_history_dir, exist_ok=True)

        # For web pages we need to store images and graphviz
        os.makedirs("web_images", exist_ok=True)

        # Store loaded Paper
        self.loaded_paper_text = ""
        self._latex_window_enabled = False
        self.loaded_paper_source = ""

        self.root = tk.Tk()
        self.root.attributes("-topmost", False)
        self.root.after(10, lambda: self.root.attributes("-topmost", False))

        self.root.overrideredirect(True)
        self.root.configure(bg=BG_ROOT)
        self.root.geometry("1280x860+80+20")
        self.root.resizable(False, False)

        # Token tracking
        self._session_tokens_in = 0
        self._session_tokens_out = 0
        self._last_tokens_in = 0
        self._last_tokens_out = 0
        self._session_queries = 0
        self._last_model_used = ""

        self._thinking = False
        self._dot_cycle = self._dot_generator()

        # attributes for detachable window
        self._conv_detached = False
        self._conv_toplevel = None
        self._conv_expanded = False
        self._conv_dock_parent = None
        self._conv_outer = None
        self._conv_sec = None

        self._drag_x = self._drag_y = 0
        self._placeholder_active = True
        self._is_maximized = False
        self.recording = False
        self.record_start = 0.0
        self.blink_state = True

        # Conversation history for context
        self.conversation_history = []
        self._last_search_query = None
        self.internet_active = False

        # Track code blocks in conversation
        self.code_blocks = []
        self._diagram_images = []

        # Load location FIRST
        self.suburb = None
        self.load_location()

        from datetime import date as _date
        self.SYSTEM_PROMPT = self.SYSTEM_PROMPT_TEMPLATE.format(
            location=self.suburb or "Birkdale, Auckland",
            date=_date.today().strftime("%A, %d %B %Y"),
        )

        self.load_location()

        import sys
        self.theme_manager = ThemeManager(self, sys.modules[__name__])

        self._build_ui()
        self._init_backend()  # ← THIS CREATES self.ai

        # ─────────────────────────────────────────────
        # NOW create memory, affect, council (AFTER self.ai exists)
        # ─────────────────────────────────────────────
        self.memory = NovaMemory("nova_state.json")
        # Surface any pending reminders from last session
        pending = self.memory.get_pending_prospective()
        if pending:
            self.log(f"[MEMORY] 📌 {len(pending)} pending reminder(s) from last session")
            reminder_text = "📌 **Reminders from last session:**\n"
            for i, entry in enumerate(pending):
                reminder_text += f"• {entry['reminder']}\n"
            self.root.after(3000, lambda t=reminder_text: self._append_conv("system", t))

        self.memory.set_logger(self.log)

        self.affect = NovaAffect(memory=self.memory)
        self.affect.set_logger(self.log)

        self.council = NovaCouncil(self.ai, logger=self.log)  # ← Now self.ai exists

        self._add_web_controls()

        # Start emotional decay timer
        self.root.after(60000, self._decay_affect)

        self.log("[SYSTEM] Nova Assistant — online.")
        self.log(f"[SYSTEM] Model: {self.ai.model}")
        if self.ai.cloud_model_ids:
            self.log(f"[SYSTEM] Cloud: {', '.join(sorted(self.ai.cloud_model_ids))}")
    # ══════════════════════════════════════
    # BACKEND
    # ══════════════════════════════════════
    def _init_backend(self):
        self.ai = WorkingAI(model=None, logger=self.log)
        self.ai.system_prompt = self.SYSTEM_PROMPT  # already formatted in __init__
        # register callbacks
        self.ai.token_limit_callback = self._on_token_limit_hit
        self.ai.internet_indicator_callback = self._set_internet_indicator
        self.ai.token_callback = self._record_tokens

        # Model dropdown
        local = self._get_ollama_models()
        cloud = [m["id"] for m in (self.ai.cloud_config or {}).get("models", [])]
        all_m = local + cloud or [self.ai.model]
        self.model_cb["values"] = all_m
        self.model_cb.set(self.ai.model if self.ai.model in all_m else all_m[0])
        self._on_model_change()

        # LaTeX window
        self.latex_win = LatexWindow(self.root, log_fn=self.log)
        self.latex_win.withdraw()

        # CodeWindow + loop
        self._cw_frame = tk.Frame(self.root, bg="#0C1219")
        self.code_window = CodeWindow(self._cw_frame, stop_callback=self._on_halt, main_app=self)

        self.code_window.goof_callback = self._on_goof
        self.code_window.output_callback = self._on_sandbox_output
        self.code_window.withdraw()

        original_set_code = self.code_window.set_code
        from planner import TaskPlanner
        from agent_executor import AgentExecutor

        self.download_dir = "downloads"
        self.image_dir = "downloaded_images"

        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)

        self.tools = ToolRegistry()
        audit = self.tools.audit()
        for name, status in audit.items():
            self.log(f"[TOOLS] {name}: {status}")

        self.planner = TaskPlanner(
            self.ai,
            self.log,
            env_fn=self.build_env_context,
            app=self
        )
        self.executor = AgentExecutor(self)
        self.manager = ManagerAgent(self.ai, logger=self.log)

        def _patched(code, **kwargs):
            self.log(f"[PATCHED] set_code called — {len(code) if code else 0} chars")
            replacements = {
                "\u201C": '"', "\u201D": '"',
                "\u2018": "'", "\u2019": "'",
                "\u2014": "-", "\u2013": "-",
                "\u2212": "-",  # ← Unicode minus sign → hyphen
                "\u2026": "...", "\u00d7": "*",
                "\u00f7": "/", "\u2192": "->",
            }
            clean = code
            if clean:
                for bad, good in replacements.items():
                    clean = clean.replace(bad, good)
            original_set_code(clean, **kwargs)

            def _upd():
                self.log("[PATCHED] Updating code_display")
                try:
                    self.code_display.config(state="normal")
                    self.code_display.delete("1.0", tk.END)
                    self.code_display.insert("1.0", clean)
                    self.code_display.see("1.0")
                    self.code_display.config(state="disabled")
                except Exception as e:
                    self.log(f"[PATCHED] code_display update failed: {e}")

            self.root.after(0, _upd)

        self.smart_loop = CodeExecutionLoop(
            ai_model=self.ai, sandbox=self.code_window,
            search_handler=None, log_callback=self.log,
            progress_callback=None, mistake_memory=self.ai.mistake_memory)
        # This is self_improver

        import sys

        self.self_improver = SelfImprover(
            self.ai,
            self.log,
            source_files=[
                "nova_assistant_v1",
                "nova_ai",
                "nova_tts",
                "nova_whisper",
                "nova_manager",
                "nova_widgets",
                "nova_selfimprove_ui",
                "nova_router",
                "code_execution_loop",
                "latex_window",
                "theme_manager",
                "code_window",
                "mistake_memory",
                "Internet_Tools",
                "math_speech",
                "planner",
                "agent_executor",
                "code_display",
                "nova_web.py"
                "nova_memory.py",
                "nova_council.py",
                "nova_affect.py",
            ],
            running_file=os.path.abspath(sys.argv[0])
        )
        self.whisper = WhisperHandler(self, self.log, self._update_whisper_status)
        self.root.after(500, self._background_ollama_poller)
        self.root.after(1000, lambda: self.whisper.load_model(
            self.whisper_model_cb.get(), self.whisper_dev_cb.get()))
        self._update_record_timer()

    def _get_ollama_models(self):
        for url in ["http://127.0.0.1:11434/api/tags", "http://localhost:11434/api/tags"]:
            try:
                r = requests.get(url, timeout=3)
                if r.status_code == 200: return sorted([m["name"] for m in r.json().get("models", [])])
            except (requests.RequestException, OSError):
                pass
        return []

    def _background_ollama_poller(self):
        def _poll():
            paths = [r"C:\Program Files\Ollama\ollama.exe",
                     os.path.expanduser(r"~\AppData\Local\Programs\Ollama\ollama.exe")]
            if not any(os.path.exists(p) for p in paths):
                self.log("[Ollama] Not installed — cloud only.");
                return
            for _ in range(30):
                time.sleep(1)
                if check_ollama_running():
                    self.log("[Ollama] ✅ Ready")
                    self.root.after(0, self._refresh_models);
                    return
            self.log("[Ollama] ⚠️ Timed out")

        threading.Thread(target=_poll, daemon=True).start()

    def _refresh_models(self):
        local = self._get_ollama_models()
        cloud = [m["id"] for m in (self.ai.cloud_config or {}).get("models", [])]
        all_m = local + cloud
        if all_m:
            self.model_cb["values"] = all_m
            self.log(f"[Ollama] {len(local)} local model(s) added")

    def try_tool(self, user_input):

        text = user_input.lower().strip()

        # ── graph: prefix → diagram tool ─────────────────────
        if user_input.lstrip().lower().startswith("graph:"):
            description = user_input.split(":", 1)[1].strip()
            if description:
                self.log(f"[TOOLS] 📐 Diagram → {description}")
                return self.tools.run("diagram", description, self.ai)

        # ── Direct URL audio playback ─────────────────────
        if "play audio" in text or text.startswith("play http"):
            url_match = re.search(r"https?://\S+", user_input)
            if url_match:
                url = url_match.group(0)
                self.log(f"[TOOLS] 🔊 Audio → {url}")
                return self.tools.run("play_audio_from_url", url)

        # ── Direct URL download ─────────────────────
        if text.startswith("download http"):
            url_match = re.search(r"https?://\S+", user_input)
            if url_match:
                url = url_match.group(0)
                self.log(f"[TOOLS] 📥 Download → {url}")
                self._set_internet_indicator(True)
                try:
                    result = self.tools.run("download_file", url, self.download_dir)
                finally:
                    self._set_internet_indicator(False)
                return result

        return None

    def ai_choose_tool(self, user_input):

        tools = self.tools.list_tools()

        from tools.file_explorer import SHORTCUTS
        shortcuts_text = ", ".join(f"{k}={v}" for k, v in SHORTCUTS.items())

        tool_descriptions = {
            "open_webpage": "Open a website in the browser using a URL.",
            "download_file": "Download a file from a URL to the downloads folder.",
            "search_and_show_image": "Search the internet for images and display them.",
            "play_youtube_video": "Play a YouTube video in the browser.",
            "play_audio_from_url": "Play an audio file from a direct URL.",
            "play_sound_from_url": "Play a sound effect from a URL.",
            "search_and_play_sound": "Search the internet for a sound effect and play it.",
            "play_local_music": "Play music from local library using partial name or keywords (no full path required).",
            "play_local_video": "Play a video or film from local library using partial name or keywords (no full path required).",
            "summarise_document_from_source": "Download and extract text from a document URL (PDFs etc).",
            "self_inspect": "Read Nova's own source code and explain it.",
            "file_explorer": "Explore and manage local files and directories.",
            "write_file": "Write text content to a file at a specified path on the local filesystem.",
            "diagram": "Draw a block diagram or flowchart from a description or edge list (A -> B). Use for architecture, pipelines, control systems, signal flow. NOT for data plots or charts.",
            "sympy_exec": "Execute SymPy Python code to verify or compute mathematics symbolically. Use when checking integrals, derivatives, equations or algebra."
        }
        # ── Build tool list ─────────────────────
        tool_text = ""
        for t in tools:
            desc = tool_descriptions.get(t, "No description available")
            tool_text += f"{t} — {desc}\n"

        # ── Build history ──────────────────────
        recent_history = self.build_recent_history()

        # ── Prompt ─────────────────────────────
        prompt = f"""
    You are deciding if a tool should be used.

    AVAILABLE TOOLS:
    {tool_text}

    RECENT CONVERSATION:
    {recent_history}

    User request:
    {user_input}

    ────────────────────────────
    CRITICAL TOOL SELECTION RULES
    ────────────────────────────

    1. INFORMATION QUERIES (MOST IMPORTANT):
    - Questions asking for information MUST return NO_TOOL
    - Examples:
      "weather today"
      "what is AI"
      "stock price"
      "news today"
    - These are handled by the planner/research system

    2. OPEN_WEBPAGE USAGE:
    - ONLY use open_webpage when the user explicitly wants navigation
    - Examples:
      "open youtube"
      "go to google"
      "visit bbc website"
    - NEVER use open_webpage for information queries

    3. TOOL USAGE:
    - Use summarise_document_from_source for papers
    - Use download_file ONLY for downloads
    - Use search_and_show_image for images/photos
    - Use play_youtube_video for videos
    - Use file_explorer for local files

4. DIAGRAM RULE:
    - NEVER use image tools for diagrams or graphs
    - Use `diagram` tool when the user wants a block diagram, flowchart,
      or system/pipeline visualisation
    - Examples:
      "draw a control system diagram"
      "show the pipeline as a diagram"
      "diagram of a neural network"
    - Pass the concept or description as the argument
    - NEVER use `diagram` for data plots, bar charts, or matplotlib output
    - Those are handled by the code agent, not a tool

    5. HISTORY RULE:
    - You MUST use RECENT CONVERSATION to resolve:
      "it", "that", "the last file", etc.

    6. FILE RULES:
    - Always use full absolute paths
    - Use shortcuts like: {shortcuts_text}

    7. MUSIC RULE:
    - play_local_music requires exact file path
    - NEVER pass a search query to it

    8. SYMPY RULE:
    - Use `sympy_exec` when the user wants to verify, compute or check mathematics
    - Examples:
      "verify this integral"
      "check that derivative"
      "compute the integral of x^3 sin^3(x)"
      "simplify this expression"
    - The argument MUST be valid Python code using SymPy, NOT plain English
    - CORRECT:   "from sympy import *\nx=symbols('x')\nprint(integrate(x**3*sin(x)**3,x))"
    - INCORRECT: "integrate x^3 sin^3(x)"
    - Always end the code with print() so a result is returned
    ────────────────────────────

    If unsure → return NO_TOOL

    Return EXACTLY:

    USE_TOOL: tool_name | argument

    OR

    NO_TOOL
    """

        response = self.ai.generate(prompt, use_planning=False)

        if not response:
            return "NO_TOOL"

        return response.strip()

    def try_ai_tool(self, user_input):

        decision = self.ai_choose_tool(user_input)
        self.log(f"[AI TOOL DECISION] {decision}")

        match = re.search(r"USE_TOOL:\s*(\w+)\s*\|\s*(.+)", decision)

        if match:
            tool_name = match.group(1).strip()
            arg = match.group(2).strip()
            # 🚫 BLOCK WRONG TOOL USAGE FOR INFO QUERIES
            info_keywords = [
                "weather", "temperature", "forecast",
                "news", "price", "stock", "time",
                "what", "how", "why", "when"
            ]

            if tool_name == "open_webpage":
                if any(k in user_input.lower() for k in info_keywords):
                    self.log("[AI TOOL] 🚫 Blocked open_webpage (info query)")
                    return None  # forces planner instead
            self.log(f"[AI TOOL] {tool_name} → {arg}")
            self._set_internet_indicator(True)
            ###
            try:
                if tool_name == "search_and_show_image":
                    result = self.tools.run(tool_name, arg, self.ai.internet, self.image_dir)
                elif tool_name == "diagram":
                    result = self.tools.run(tool_name, arg, self.ai)
                elif tool_name == "search_and_play_sound":
                    result = self.tools.run(tool_name, arg, self.download_dir, self.ai.internet)
                elif tool_name == "sympy_exec":
                    result = self.tools.run(tool_name, arg)
                elif tool_name == "open_webpage":
                     result = self.tools.run(tool_name, arg, internet_tools=self.ai.internet)
                elif tool_name == "write_file":
                    content = self.state.get("last_result", "")
                    if not content:
                        return "Nothing to save — no previous response found."
                    result = self.tools.run(tool_name, arg, content)

                else:
                    result = self.tools.run(tool_name, arg)

                if result:
                    self.log(f"[TOOL RESULT] {str(result)[:200]}")

                if tool_name == "summarise_document_from_source" and result:
                    self.log("[TOOL] Sending document to AI for summarisation...")

                    summary = self.ai.generate(
                        f"""
    You are reading a research paper.

    Summarise the following document:

    {result}

    Provide:

    - Title
    - Authors
    - Main topic
    - Key ideas
    - Methods used
    - Conclusion
    """,
                        use_planning=False
                    )

                    return summary
                ##############################
                if tool_name == "self_inspect" and result:
                    self.log("[TOOL] Nova reading own source code...")

                    if result.startswith("SELF_INSPECT:"):
                        parts = result[13:].split("||", 1)
                        query = parts[0]
                        source = parts[1] if len(parts) > 1 else ""

                        # Check if user wants a diagram
                        wants_diagram = any(w in user_input.lower()
                                            for w in ["diagram", "draw", "visualis",
                                                      "chart", "plot", "show pipeline"])

                        if wants_diagram:
                            pipeline_desc = self.ai.generate(
                                f"""You are reading Nova Assistant's Python source code.

                Find the method called _process_input in the code below and list its exact processing stages in order.
                These are Python application routing steps NOT AI model internals.
                Look for the actual if/elif blocks and method calls inside _process_input.

                {source}

                Return ONLY a comma separated list of the actual stage names found in _process_input, nothing else.
                Example: Story Check, Diagram Check, try_tool, try_ai_tool, PDF Check, ReAct Agent, Internet Search, Planner, Intent Classification, Final Synthesis""",
                                use_planning=False
                            )
                            task = f"""Write Python matplotlib code to visualise this exact pipeline as a dark-themed flow diagram:

                PIPELINE STAGES (use these exact names in this exact order, do not invent or rename any):
                {pipeline_desc}

                Requirements:
                - Dark background #0D1117
                - Electric blue #4A9EFF boxes
                - Vertical layout top to bottom
                - Show early-return branches as side arrows labelled 'handled' in orange
                - Internet Search stage has NO early return — mark it green
                - Final Synthesis at the bottom in purple
                - Numbered stages
                - Legend explaining colours
                - Save as nova_pipeline.png and display"""

                            self.root.after(0, lambda t=task: self._ask_code_permission(t))
                            return "Reading pipeline from source — generating diagram..."

                        return self.ai.generate(
                            f"""You are Nova reading your own source code.
                Answer this question about yourself based on your source code:

                QUESTION: {query}

                YOUR SOURCE CODE:
                {source}

                Answer specifically and accurately based on what you can see in the code.
                Do not pretend to know things not visible in the source.""",
                            use_planning=False
                        )
                ################################
                if tool_name == "file_explorer" and result:
                    if "SEARCH:" in result and any(
                            ext in result.lower() for ext in [".mp3", ".wav", ".flac", ".ogg"]
                    ):
                        # Regex that handles spaces in filenames
                        paths = re.findall(r'[A-Z]:[^\t\n(]+\.(?:mp3|wav|flac|ogg)',
                                           result, re.IGNORECASE)
                        paths = [p.strip() for p in paths if os.path.exists(p.strip())]

                        if paths:
                            # Score paths by how well they match the original query
                            query_words = [w.lower() for w in user_input.split()
                                           if len(w) > 2]

                            def score(p):
                                fname = os.path.basename(p).lower()
                                return sum(1 for w in query_words if w in fname)

                            paths.sort(key=score, reverse=True)
                            best = paths[0].replace("\\", "/")
                            self.log(f"[MUSIC] Auto-playing: {best}")
                            try:
                                self.tools.run("play_local_music", best)
                                return f"Playing: {os.path.basename(best)}"
                            except Exception as e:
                                self.log(f"[MUSIC] Play failed: {e}")

                return result

            except Exception as e:
                self.log(f"[TOOL ERROR] {e}")
                return None

            finally:
                self._set_internet_indicator(False)

        return None

    # ══════════════════════════════════════
    # UI BUILD
    # ══════════════════════════════════════
    def _build_ui(self):
        self._seam_frames = []
        self._build_header()
        body = tk.Frame(self.root, bg=BG_ROOT)
        body.pack(fill="both", expand=True)
        self.left_panel = tk.Frame(body, bg=BG_LEFT, width=390)
        self.right_panel = tk.Frame(body, bg=BG_RIGHT)
        tk.Frame(body, bg=SEAM, width=1).pack(side="left", fill="y")
        self.left_panel.pack(side="left", fill="y")
        self.left_panel.pack_propagate(False)
        tk.Frame(body, bg=SEAM, width=1).pack(side="left", fill="y")
        self.right_panel.pack(side="left", fill="both", expand=True)
        self._build_left()
        self._build_right()
        self._build_resize_handle()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=BG_HEADER, height=28)
        hdr.pack(fill="x");
        hdr.pack_propagate(False)
        hdr.bind("<ButtonPress-1>", self._drag_start)
        hdr.bind("<B1-Motion>", self._drag_motion)
        dots = tk.Frame(hdr, bg=BG_HEADER)
        dots.place(x=10, rely=0.5, anchor="w")
        for col, cmd in [("#FF5F57", self.root.destroy), ("#FFBD2E", self._minimize), ("#28C840", self._maximize)]:
            c = tk.Canvas(dots, width=14, height=14, bg=BG_HEADER, highlightthickness=0)
            c.pack(side="left", padx=3)
            c.create_oval(2, 2, 12, 12, fill=col, outline="")
            c.bind("<Button-1>", lambda e, fn=cmd: fn())
        tk.Label(hdr, text=f"Nova Assistant  ·  v{__version__}",
                 font=F_RAJ_BIG, bg=BG_HEADER, fg=PLATINUM
                 ).place(relx=0.5, rely=0.5, anchor="center")

        theme_c = tk.Canvas(hdr, width=60, height=20, bg=BG_HEADER, highlightthickness=0)
        theme_c.place(relx=0.85, rely=0.5, anchor="w")
        theme_c.create_rectangle(1, 1, 59, 19, fill="#1A2035", outline=ELECTRIC_BLUE)
        theme_c.create_text(30, 10, text="THEME", font=F_RAJ_SM, fill=ELECTRIC_BLUE)
        theme_c.bind("<Button-1>", lambda e: ThemePicker(self.root, self.theme_manager))

    def _drag_start(self, e):
        self._drag_x = e.x_root - self.root.winfo_x()
        self._drag_y = e.y_root - self.root.winfo_y()

    def _drag_motion(self, e):
        if getattr(self, '_resize_dragging', False):
            return
        self.root.geometry(f"+{e.x_root - self._drag_x}+{e.y_root - self._drag_y}")

    def _minimize(self):
        self.root.overrideredirect(False);
        self.root.iconify()

        def _restore():
            if self.root.state() == 'normal': self.root.overrideredirect(True)

        self.root.bind("<Map>", lambda e: _restore())

    def _maximize(self):
        if getattr(self, '_is_maximized', False):
            self.root.geometry(self._original_geometry);
            self._is_maximized = False
        else:
            self._original_geometry = self.root.geometry()
            w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            self.root.geometry(f"{w}x{h}+0+0");
            self._is_maximized = True

    def _section(self, parent, title, bc=SEAM, bg=BG_LEFT):
        outer = tk.Frame(parent, bg=bc, padx=2, pady=2)
        outer.pack(fill="x", padx=10, pady=5)
        inner = tk.Frame(outer, bg=bg);
        inner.pack(fill="both", expand=True)
        tk.Label(inner, text=title, font=F_RAJ_SM, bg=bg, fg=ELECTRIC_BLUE
                 ).pack(anchor="w", padx=6, pady=(4, 0))
        return inner

    def _styled_combo(self, parent, values, default=0):
        s = ttk.Style();
        s.theme_use("clam")
        try:
            s.configure("Dark.TCombobox", fieldbackground="#1A2035", background="#2A3A5A",
                        foreground="#FFFFFF", selectbackground="#2A5A9F",
                        selectforeground="#FFFFFF", bordercolor=ELECTRIC_BLUE,
                        arrowcolor=ELECTRIC_BLUE, relief="flat")
            s.map("Dark.TCombobox",
                  foreground=[("readonly", "#FFFFFF"), ("disabled", DIM_TEXT)],
                  fieldbackground=[("readonly", "#1A2035")])
        except:
            pass
        cb = ttk.Combobox(parent, values=values, style="Dark.TCombobox", state="readonly")
        if values: cb.current(default)
        return cb

    # ── LEFT PANEL ───────────────────────────
    def _build_left(self):
        lp = self.left_panel
        brand = tk.Frame(lp, bg=BG_LEFT);
        brand.pack(pady=(14, 4))

        # NOVA letters frame for flashing animation
        nova_frame = tk.Frame(brand, bg=BG_LEFT)
        nova_frame.pack()

        self._nova_labels = []
        for letter in "NOVA":
            lbl = tk.Label(nova_frame, text=letter, font=F_ORBITRON,
                           bg=BG_LEFT, fg=ELECTRIC_BLUE)
            lbl.pack(side="left")
            self._nova_labels.append(lbl)

        self._nova_flash_state = True
        self._nova_flash_running = False
        tk.Label(brand, text="· Assistant ·", font=F_RAJ_MED, bg=BG_LEFT, fg=DIM_TEXT).pack()

        self._build_model_panel(lp)
        self._build_whisper_panel(lp)
        self._build_input_panel(lp)
        self._build_action_buttons(lp)
        self._build_history_row(lp)
        self._build_debug_console(lp)

    def _build_model_panel(self, parent):
        sec = self._section(parent, "AI ENGINE")
        self.model_cb = self._styled_combo(sec, [])
        self.model_cb.pack(fill="x", padx=6, pady=4)
        self.model_cb.bind("<<ComboboxSelected>>", self._on_model_change)
        self.model_status = tk.Label(sec, text="● LOCAL · Ollama",
                                     font=F_RAJ_SM, bg=BG_LEFT, fg=GREEN_GLOW)
        self.model_status.pack(anchor="w", padx=8, pady=(0, 6))
        self._pulse_model()

    def _on_model_change(self, _=None):
        sel = self.model_cb.get()
        if not sel: return
        if hasattr(self, 'ai'):
            self.ai.model = sel
            is_cloud = self.ai._is_cloud_model(sel)
            # 1. Better model status
            self.model_status.config(
                text=f"{'☁ CLOUD' if is_cloud else '● LOCAL'} • {sel.split(':')[0]}",
                fg=VIOLET if is_cloud else GREEN_GLOW
            )
            if not is_cloud and not check_ollama_running():
                threading.Thread(target=lambda: (start_ollama(), wait_for_ollama()),
                                 daemon=True).start()
            if hasattr(self, 'smart_loop'):
                self.smart_loop = CodeExecutionLoop(
                    ai_model=self.ai, sandbox=self.code_window,
                    search_handler=None, log_callback=self.log,
                    mistake_memory=self.ai.mistake_memory)
            self.log(f"[AI] Model → {sel}")

    def get_environment(self):
        from datetime import datetime
        import requests

        now = datetime.now()

        env = {
            "time": now.strftime("%H:%M"),
            "date": now.strftime("%A %d %B %Y"),
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "city": None,
            "region": None,
            "country": None,
            "lat": None,
            "lon": None,
            "timezone": None,
            "suburb": self.suburb
        }
        try:
            r = requests.get("http://ip-api.com/json/", timeout=5)
            data = r.json()

            env["city"] = data.get("city")
            env["region"] = data.get("regionName")
            env["country"] = data.get("country")
            env["lat"] = data.get("lat")
            env["lon"] = data.get("lon")
            env["timezone"] = data.get("timezone")
        except Exception:
            pass

        return env

    def load_location(self):

        import json
        import os

        path = os.path.join(os.path.dirname(__file__), "nova_location.json")

        try:
            with open(path, "r") as f:
                data = json.load(f)

            self.suburb = data.get("user", {}).get("suburb")

            self.log(f"[LOCATION] Suburb loaded: {self.suburb}")

        except Exception as e:
            self.suburb = None
            self.log(f"[LOCATION] Error loading location: {e}")

    def show_diagram(self, pdf_path, store=True):

        import fitz
        from PIL import Image, ImageTk

        try:

            doc = fitz.open(pdf_path)
            page = doc.load_page(0)
            pix = page.get_pixmap()

            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            photo = ImageTk.PhotoImage(img)

            target_frame = self._detached_frame if self._conv_detached else self.conv_frame

            label = tk.Label(target_frame, image=photo, bg="#0C1219")
            label.image = photo
            label.pack(pady=10)

            if store:
                self.conversation_history.append({
                    "role": "assistant",
                    "type": "diagram",
                    "path": pdf_path
                })

            self.log("[TIKZ] Diagram displayed")

        except Exception as e:
            self.log(f"[DIAGRAM ERROR] {e}")

    def _add_web_controls(self):
        """Add web server controls with mobile mode"""
        frame = tk.Frame(self.left_panel, bg=BG_LEFT)
        frame.pack(fill="x", padx=10, pady=5)

        tk.Label(frame, text="WEB", font=F_RAJ_SM, bg=BG_LEFT, fg=ELECTRIC_BLUE).pack(anchor="w")

        self.web_status = tk.Label(frame, text="🌐 Inactive", font=F_RAJ_SM, bg=BG_LEFT, fg=AMBER)
        self.web_status.pack(anchor="w", padx=6)

        btn_frame = tk.Frame(frame, bg=BG_LEFT)
        btn_frame.pack(fill="x", pady=2)

        self.web_btn = tk.Button(btn_frame, text="Start Web Server", command=self._toggle_web,
                                 bg="#1A1F2E", fg="#00BFFF", font=("Rajdhani", 9))
        self.web_btn.pack(side="left", padx=2)

        self.open_btn = tk.Button(btn_frame, text="Open Browser", command=self._open_web,
                                  bg="#1A1F2E", fg="#39FF14", font=("Rajdhani", 9), state="disabled")
        self.open_btn.pack(side="left", padx=2)

        # Mobile mode checkbox
        self.mobile_var = tk.BooleanVar()
        self.mobile_check = tk.Checkbutton(btn_frame, text="📱 Mobile", variable=self.mobile_var,
                                           bg=BG_LEFT, fg=ELECTRIC_BLUE, selectcolor=BG_LEFT,
                                           font=("Rajdhani", 8))
        self.mobile_check.pack(side="left", padx=5)

        self.web_server = None

    def _toggle_web(self):
        """Start or stop web server"""
        if self.web_server:
            self.web_server.stop()
            self.web_server = None
            self.web_status.config(text="🌐 Inactive", fg=AMBER)
            self.web_btn.config(text="Start Web Server")
            self.open_btn.config(state="disabled")
        else:
            import os
            cert = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cert.pem')
            protocol = "https" if os.path.exists(cert) else "http"

            bind_all = self.mobile_var.get()
            self.web_server = NovaWebServer(self, bind_all=bind_all)

            self.web_server.start()

            if bind_all:
                import socket
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    ip = s.getsockname()[0]
                    s.close()
                    self.web_status.config(text=f"📱 {protocol}://{ip}:8080", fg=GREEN_GLOW)
                except:
                    self.web_status.config(text=f"📱 Network mode", fg=GREEN_GLOW)
            else:
                self.web_status.config(text=f"🌐 {protocol}://127.0.0.1:8080", fg=GREEN_GLOW)

            self.web_btn.config(text="Stop Web Server")
            self.open_btn.config(state="normal")

            if not bind_all:
                self.root.after(2000, self._open_web)



    def _open_web(self):
        """Open browser"""
        if self.web_server:
            self.web_server.open_browser()

    def show_graphviz_diagram(self, path, store=True, target_frame=None):
        """Display Graphviz diagram - also saves copy for web interface"""
        import os
        import shutil
        from datetime import datetime
        from PIL import Image, ImageTk

        if not os.path.exists(path):
            self.log(f"[GRAPHVIZ] Missing image: {path}")
            return

        # Create web_images folder if it doesn't exist
        web_dir = "web_images"
        os.makedirs(web_dir, exist_ok=True)

        # Copy to web_images with timestamp to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = os.path.basename(path)
        name, ext = os.path.splitext(original_filename)
        web_filename = f"diagram_{name}_{timestamp}{ext}"
        web_path = os.path.join(web_dir, web_filename)
        shutil.copy2(path, web_path)
        self.log(f"[GRAPHVIZ] Copied to web: {web_filename}")

        # Display in Tkinter (existing code)
        if target_frame is None:
            target_frame = self._detached_frame if self._conv_detached else self.conv_frame

        img = Image.open(path)
        zoom = {"scale": 1.0}

        container = tk.Frame(target_frame, bg="#0C1219", height=300)
        container.pack(fill="both", pady=10)
        container.pack_propagate(False)
        canvas = tk.Canvas(container, bg="#0C1219", highlightthickness=0)
        hbar = tk.Scrollbar(container, orient="horizontal", command=canvas.xview)
        vbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)

        canvas.configure(
            xscrollcommand=hbar.set,
            yscrollcommand=vbar.set
        )

        canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        def redraw():
            w = int(img.width * zoom["scale"])
            h = int(img.height * zoom["scale"])
            resized = img.resize((w, h), Image.LANCZOS)
            photo = ImageTk.PhotoImage(resized)
            canvas.delete("all")
            canvas.create_image(0, 0, anchor="nw", image=photo)
            canvas.config(scrollregion=(0, 0, w, h))
            canvas.image = photo

        def zoom_wheel(event):
            if event.delta > 0:
                zoom["scale"] *= 1.1
            else:
                zoom["scale"] *= 0.9
            redraw()
            return "break"

        canvas.bind("<Control-MouseWheel>", zoom_wheel)

        def start_pan(event):
            canvas.scan_mark(event.x, event.y)

        def pan_move(event):
            canvas.scan_dragto(event.x, event.y, gain=1)

        canvas.bind("<ButtonPress-1>", start_pan)
        canvas.bind("<B1-Motion>", pan_move)

        def fit(event=None):
            frame_width = canvas.winfo_width()
            zoom["scale"] = frame_width / img.width
            redraw()

        canvas.bind("<Double-Button-1>", fit)
        redraw()

        if store:
            # Store in conversation history for web
            self.conversation_history.append({
                "role": "assistant",
                "type": "diagram",
                "engine": "graphviz",
                "path": path,
                "web_path": web_path
            })
            # Add web-friendly message
            self.conversation_history.append({
                "role": "assistant",
                "content": f"[DIAGRAM:{web_filename}]",
                "timestamp": datetime.now().strftime('%H:%M')
            })

        self.log(f"[GRAPHVIZ] Diagram displayed and saved for web: {web_filename}")


    def save_plot_for_web(self, figure_or_path):
        """Save a matplotlib plot to web_images folder and add to conversation"""
        import os
        import matplotlib.pyplot as plt
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if hasattr(figure_or_path, 'savefig'):
            # It's a matplotlib figure
            filename = f"plot_{timestamp}.png"
            filepath = os.path.join("web_images", filename)
            figure_or_path.savefig(filepath, dpi=100, bbox_inches='tight')
            plt.close(figure_or_path)
        else:
            # It's already a path
            filepath = figure_or_path
            filename = os.path.basename(filepath)

        # Add to conversation history for web
        self.conversation_history.append({
            "role": "assistant",
            "content": f"[IMAGE:{filename}]",
            "timestamp": datetime.now().strftime('%H:%M')
        })

        # Also show in Tkinter
        self._append_conv("assistant", f"📊 Plot saved: {filename}")

        return filepath


    def _create_message_text(self, parent, text):
        MAX_LINES = 18  # replies longer than this get their own scrollbar

        # ── wrapper holds Text + optional side scrollbar ──────────────────────
        wrapper = tk.Frame(parent, bg="#0C1219")
        wrapper.pack(fill="x", padx=(10, 0), pady=(6, 8))
        wrapper.columnconfigure(0, weight=1)

        content = tk.Text(
            wrapper,
            font=F_GEORGIA,
            bg="#0C1219",
            fg=FG_MAIN,
            wrap="word",
            relief="flat",
            borderwidth=0,
            spacing1=2,
            spacing2=4,
            spacing3=2,
            height=3,  # will be adjusted below
        )
        scrollbar = tk.Scrollbar(
            wrapper,
            orient="vertical",
            command=content.yview,
            width=10,
        )
        content.config(yscrollcommand=scrollbar.set)

        content.insert("1.0", text)
        self._make_links_clickable(content)
        content.bind("<Control-c>", lambda e: content.event_generate("<<Copy>>"))
        content.bind("<Control-C>", lambda e: content.event_generate("<<Copy>>"))
        content.config(state="disabled")

        # Always place content in col 0; scrollbar added to col 1 only if needed
        content.grid(row=0, column=0, sticky="ew")

        def _needs_scroll():
            """True when not all content is visible (scrollbar is active)."""
            try:
                top, bot = content.yview()
                return (bot - top) < 0.999
            except Exception:
                return False

        def _adjust_height():
            try:
                content.update_idletasks()
                lines = int(content.count("1.0", "end", "displaylines")[0])
                content.config(height=max(3, min(lines, MAX_LINES)))
                if lines > MAX_LINES:
                    scrollbar.grid(row=0, column=1, sticky="ns")
            except tk.TclError:
                pass

        self.root.after(50, _adjust_height)

        # ── per-reply mousewheel handler ───────────────────────────────────────
        # Scrolls this reply when it has overflow; otherwise falls through to
        # the outer canvas scroll (via bind_all) so the whole window moves.
        def _on_wheel(event):
            if _needs_scroll():
                content.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return "break"  # consumed — outer canvas does NOT scroll
            # returning None lets bind_all fire the canvas scroll

        content.bind("<MouseWheel>", _on_wheel)

        return content

    def _clean_markdown(self, text):

        # Remove block quotes
        text = re.sub(r'^\s*>\s?', '', text, flags=re.MULTILINE)

        # Convert markdown bold to plain text
        text = text.replace("**", "")

        # Convert markdown bullets
        text = re.sub(r'^\s*[-*]\s+', '• ', text, flags=re.MULTILINE)

        # Remove markdown tables
        text = re.sub(r'^\|.*\|\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\|?-+\|?-+\|?.*$', '', text, flags=re.MULTILINE)

        # Remove warning emoji
        text = text.replace("⚠️", "Note:")

        # Clean extra blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def _pulse_model(self):
        if not hasattr(self, '_pb'): self._pb = False
        self._pb = not self._pb
        cur = self.model_status.cget("fg")
        if cur in (GREEN_GLOW, "#AAFFCC"):
            self.model_status.config(fg="#AAFFCC" if self._pb else GREEN_GLOW)
        else:
            self.model_status.config(fg="#D4AAFF" if self._pb else VIOLET)
        self.root.after(1000, self._pulse_model)

    def _build_whisper_panel(self, parent):
        sec = self._section(parent, "VOICE INPUT", bc="#7B2FBE")
        row = tk.Frame(sec, bg=BG_LEFT);
        row.pack(fill="x", padx=6, pady=2)
        tk.Label(row, text="Model:", font=F_RAJ_SM, bg=BG_LEFT, fg=DIM_TEXT).pack(side="left")
        self.whisper_model_cb = self._styled_combo(
            row, ["tiny", "base", "small", "medium", "large", "tiny.en", "base.en", "small.en", "medium.en"], 3)
        self.whisper_model_cb.pack(side="left", padx=4)
        row2 = tk.Frame(sec, bg=BG_LEFT);
        row2.pack(fill="x", padx=6, pady=2)
        tk.Label(row2, text="Device:", font=F_RAJ_SM, bg=BG_LEFT, fg=DIM_TEXT).pack(side="left")
        self.whisper_dev_cb = self._styled_combo(row2, ["cpu", "cuda"], 1)
        self.whisper_dev_cb.pack(side="left", padx=4)
        self.whisper_status_lbl = tk.Label(sec, text="● LOADING...",
                                           font=F_RAJ_SM, bg=BG_LEFT, fg=AMBER)
        self.whisper_status_lbl.pack(pady=2)
        self.record_canvas = tk.Canvas(sec, width=60, height=60, bg=BG_LEFT, highlightthickness=0)
        self.record_canvas.pack(pady=4)
        self._draw_record_btn(True)
        self.record_canvas.bind("<ButtonPress-1>", self._start_rec)
        self.record_canvas.bind("<ButtonRelease-1>", self._stop_rec)
        self.record_timer_lbl = tk.Label(sec, text="00:00", font=F_COURIER_MED,
                                         bg=BG_LEFT, fg="#FF6B6B")
        self.record_timer_lbl.pack()
        self.root.bind("<KeyPress-space>", self._space_press)
        self.root.bind("<KeyRelease-space>", self._space_release)
        self.root.bind("<space>", lambda e: "break")

    def _update_whisper_status(self, status):
        col = GREEN_GLOW if "READY" in status else (RED_GLOW if "FAIL" in status else AMBER)
        self.whisper_status_lbl.config(text=status, fg=col)

    def _draw_record_btn(self, idle=True):
        c = self.record_canvas;
        c.delete("all")
        c.create_oval(4, 4, 56, 56, fill="#1A4A2E" if idle else "#4A1A1A",
                      outline=GREEN_GLOW if idle else RED_GLOW, width=2)
        c.create_rectangle(24, 14, 36, 36, fill=WHITE, outline="")
        c.create_arc(18, 28, 42, 48, start=0, extent=-180, outline=WHITE, width=2, style="arc")
        c.create_line(30, 48, 30, 54, fill=WHITE, width=2)
        c.create_line(22, 54, 38, 54, fill=WHITE, width=2)

    def _start_rec(self, _=None):
        if not hasattr(self, 'whisper') or not self.whisper.model_loaded: return
        if self.whisper.start_recording():
            self.recording = True;
            self.record_start = time.time()
            self._draw_record_btn(False);
            self._update_whisper_status("● RECORDING")
            self._animate_record_ring()

    def _stop_rec(self, _=None):
        if not self.recording: return
        self.recording = False;
        self._draw_record_btn(True)
        self._update_whisper_status("● PROCESSING...")
        if hasattr(self, 'whisper'): self.whisper.stop_recording()

    def _space_press(self, e):
        self._start_rec();
        return "break"

    def _space_release(self, e):
        self._stop_rec();
        return "break"

    def _animate_record_ring(self):
        if not self.recording: return
        c = self.record_canvas;
        c.delete("ring")
        t = (time.time() - self.record_start) % 0.8
        r = 28 + t / 0.8 * 12
        try:
            c.create_oval(30 - r, 30 - r, 30 + r, 30 + r, outline=RED_GLOW, width=2, tags="ring")
        except:
            pass
        self.root.after(40, self._animate_record_ring)

    def _update_record_timer(self):
        if self.recording:
            elapsed = int(time.time() - self.record_start)
            mm, ss = divmod(elapsed, 60)
            self.record_timer_lbl.config(text=f"{mm:02d}:{ss:02d}")
        else:
            self.record_timer_lbl.config(text="00:00")
        self.root.after(500, self._update_record_timer)

    def _build_input_panel(self, parent):
        sec = self._section(parent, "YOUR MESSAGE")
        self.input_glow = tk.Frame(sec, bg=BORDER, padx=1, pady=1)
        self.input_glow.pack(fill="x", padx=6, pady=4)
        self.input_text = scrolledtext.ScrolledText(
            self.input_glow, height=5, bg=BG_INPUT, fg=FG_MAIN,
            insertbackground=ELECTRIC_BLUE, insertwidth=2,
            font=F_CONSOLAS, relief="flat", wrap="word")
        self.input_text.pack(fill="both")
        self._set_placeholder()
        self.input_text.bind("<FocusIn>", self._inp_focus_in)
        self.input_text.bind("<FocusOut>", self._inp_focus_out)
        self.input_text.bind("<Key>", self._inp_key)
        self.input_text.bind("<Return>", self._on_enter_key)
        self.input_text.bind("<Shift-Return>", lambda e: None)
        self.input_text.bind("<KeyRelease>", self.update_character_count)
        self.char_counter_lbl = tk.Label(sec, text="0 characters",
                                         font=F_RAJ_SM, bg=BG_LEFT, fg=DIM_TEXT)
        self.char_counter_lbl.pack(anchor="e", padx=8, pady=(0, 2))

    def _set_placeholder(self):
        self.input_text.insert("1.0", "Ask me anything — maths, science, history, code...")
        self.input_text.config(fg=FG_DIM);
        self._placeholder_active = True

    def _inp_focus_in(self, _=None):
        self.input_glow.config(bg=ELECTRIC_BLUE)
        if self._placeholder_active:
            self.input_text.delete("1.0", "end")
            self.input_text.config(fg=FG_MAIN)
            self._placeholder_active = False
        self.update_character_count()

    def _inp_focus_out(self, _=None):
        self.input_glow.config(bg=BORDER)
        if not self.input_text.get("1.0", "end").strip():
            self._set_placeholder()
        self.update_character_count()

    def _inp_key(self, _=None):
        if self._placeholder_active:
            self.input_text.delete("1.0", "end")
            self.input_text.config(fg=FG_MAIN)
            self._placeholder_active = False
        self.update_character_count()

    def _on_enter_key(self, event):
        if not (event.state & 0x1):  # Shift not held
            self._on_send();
            return "break"

    def _get_input(self):
        t = self.input_text.get("1.0", "end").strip()
        if self._placeholder_active or t == "Ask me anything — maths, science, history, code...": return ""
        return t

    def _build_action_buttons(self, parent):

        bf = tk.Frame(parent, bg=BG_LEFT)
        bf.pack(fill="x", padx=10, pady=4)

        for col in range(4):
            bf.columnconfigure(col, weight=1)

        self.send_btn = tk.Canvas(bf, width=140, height=32, bg=BG_LEFT, highlightthickness=0)
        self.send_btn.grid(row=0, column=0, columnspan=2, padx=3, pady=2, sticky="ew")
        self._draw_send_btn(False)
        self.send_btn.bind("<Enter>", lambda e: self._draw_send_btn(True))
        self.send_btn.bind("<Leave>", lambda e: self._draw_send_btn(False))
        self.send_btn.bind("<Button-1>", lambda e: self._on_send())

        self.local_pdf_btn = tk.Canvas(bf, width=140, height=32, bg=BG_LEFT, highlightthickness=0)
        self.local_pdf_btn.grid(row=0, column=3, padx=3, pady=2, sticky="ew")

        self.local_pdf_btn.create_rectangle(1, 1, 139, 31, fill="#2A4A2E", outline="#2ECC71")
        self.local_pdf_btn.create_text(70, 16, text="📂 LOAD PDF", font=F_RAJ_SM, fill="white")

        self.local_pdf_btn.bind("<Button-1>", lambda e: self._handle_pdf_button())

        self._pdf_tooltip = _CanvasTooltip(
            self.local_pdf_btn,
            text="Load a local PDF file to read,\nsummarise, or ask questions about.",
            bg="#1A3A2E",
            fg="#FFD700",
            border_colour="#2ECC71",
            font=("Rajdhani", 9),
        )

        self.clear_btn = tk.Canvas(bf, width=70, height=26, bg=BG_LEFT, highlightthickness=0)
        self.clear_btn.grid(row=1, column=0, padx=3, pady=2, sticky="w")
        self._draw_clear_btn(False)
        self.clear_btn.bind("<Enter>", lambda e: self._draw_clear_btn(True))
        self.clear_btn.bind("<Leave>", lambda e: self._draw_clear_btn(False))
        self.clear_btn.bind("<Button-1>", lambda e: self._on_clear())

        self.inet_canvas = tk.Canvas(bf, width=50, height=10, bg=BG_LEFT, highlightthickness=0)
        self.inet_canvas.grid(row=1, column=3, padx=3, pady=8, sticky="ew")
        self._search_bar_phase = 0
        self._search_bar_flash = False
        self._draw_search_bar(False)
        self.inet_canvas.bind(
            "<Button-1>",
            lambda e: self.log(f"[INTERNET] Last search: {self._last_search_query or 'none'}")
        )

        # SAVE CHAT button (added to left of DOCUMENT)
        self.save_chat_btn = tk.Canvas(bf, width=70, height=26,
                                       bg=BG_LEFT, highlightthickness=0)
        self.save_chat_btn.grid(row=2, column=1, padx=3, pady=2, sticky="w")
        self._draw_save_chat_btn(False)
        self.save_chat_btn.bind("<Button-1>", lambda e: self._save_chat_to_desktop())
        self.save_chat_btn.bind("<Enter>", lambda e: self._draw_save_chat_btn(True), add=True)
        self.save_chat_btn.bind("<Leave>", lambda e: self._draw_save_chat_btn(False), add=True)

        self._save_chat_tooltip = _CanvasTooltip(
            self.save_chat_btn,
            text="Save entire conversation\nto desktop as HTML",
            bg="#1A3A2E",
            fg="#FFD700",
            border_colour="#2ECC71",
            font=("Rajdhani", 9),
        )

        self.document_btn = tk.Canvas(bf, width=70, height=26,
                                      bg=BG_LEFT, highlightthickness=0)
        self.document_btn.grid(row=2, column=2, padx=3, pady=2,
                               sticky="w")
        self._draw_document_btn(False)
        self.document_btn.bind("<Button-1>",
                               lambda e: self._run_documentation())
        self.document_btn.bind("<Enter>",
                               lambda e: self._draw_document_btn(True),
                               add=True)
        self.document_btn.bind("<Leave>",
                               lambda e: self._draw_document_btn(False),
                               add=True)

        self._document_tooltip = _CanvasTooltip(
            self.document_btn,
            text="Add docstrings to every undocumented\n"
                 "method — one at a time, fast and safe.",
            bg="#0A1A2A",
            fg="#00BFFF",
            border_colour="#0080FF",
            font=("Rajdhani", 9),
        )
        self.aux_btn = tk.Canvas(bf, width=70, height=26,
                                 bg=BG_LEFT, highlightthickness=0)
        self.aux_btn.grid(row=2, column=3, padx=3, pady=2, sticky="w")
        self._draw_aux_btn(False)
        self.aux_btn.bind("<Button-1>", lambda e: self._open_aux_window())
        self.aux_btn.bind("<Enter>", lambda e: self._draw_aux_btn(True), add=True)
        self.aux_btn.bind("<Leave>", lambda e: self._draw_aux_btn(False), add=True)

        self.clear_btn.grid(row=1, column=0, padx=3, pady=2, sticky="w")
        self.inet_canvas.grid(row=1, column=3, padx=3, pady=8, sticky="ew")

        self.save_chat_btn.grid(row=2, column=1, padx=3, pady=2, sticky="w")
        self.document_btn.grid(row=2, column=2, padx=3, pady=2, sticky="w")
        self.aux_btn.grid(row=2, column=3, padx=3, pady=2, sticky="w")

    def _draw_save_chat_btn(self, hover=False):
        c = self.save_chat_btn
        c.delete("all")
        brd = "#FFD700" if hover else "#2A3A5A"
        fg = "#FFD700" if hover else "#8A7A2A"
        c.create_rectangle(1, 1, 69, 25, fill="#1A1F2E", outline=brd)
        c.create_text(35, 13, text="💾 SAVE", font=("Rajdhani", 8, "bold"), fill=fg)

    def _save_chat_to_desktop(self):
        """Save the entire conversation history as an HTML file on the desktop"""
        import os
        from datetime import datetime

        if not self.conversation_history:
            self._append_conv("system", "No conversation to save.")
            return

        # Get desktop path
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Nova_Chat_{timestamp}.html"
        filepath = os.path.join(desktop, filename)

        # Build HTML content with improvements
        html_content = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Nova Chat - {timestamp}</title>
        <script>
        MathJax = {{
            tex: {{
                inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
            }},
            options: {{
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
            }}
        }};
        </script>
        <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                background: #0D0F14;
                color: #C8D6E5;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Georgia, serif;
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.7;
            }}

            h1 {{
                color: #4A9EFF;
                font-size: 2em;
                margin-bottom: 10px;
                border-bottom: 2px solid #4A9EFF;
                display: inline-block;
                padding-bottom: 5px;
            }}

            h2, h3 {{
                color: #4A9EFF;
                margin-top: 20px;
                margin-bottom: 10px;
            }}

            .metadata {{
                color: #6B7A99;
                font-size: 0.9em;
                margin: 15px 0 25px 0;
                padding: 10px;
                background: #0A0C10;
                border-radius: 8px;
            }}

            .message {{
                margin-bottom: 25px;
                padding: 18px;
                border-radius: 12px;
                background: #0F1318;
                transition: all 0.2s ease;
            }}

            .message:hover {{
                background: #131820;
                transform: translateX(2px);
            }}

            .user {{
                border-left: 4px solid #4A9EFF;
            }}

            .assistant {{
                border-left: 4px solid #39FF14;
            }}

            .system {{
                border-left: 4px solid #F39C12;
                opacity: 0.8;
            }}

            .role {{
                font-weight: bold;
                margin-bottom: 12px;
                font-size: 0.9em;
                letter-spacing: 0.5px;
            }}

            .user .role {{
                color: #4A9EFF;
            }}

            .assistant .role {{
                color: #39FF14;
            }}

            .system .role {{
                color: #F39C12;
            }}

            .timestamp {{
                font-size: 0.75em;
                color: #6B7A99;
                margin-left: 10px;
                font-weight: normal;
            }}

            .content {{
                line-height: 1.7;
            }}

            .content p {{
                margin-bottom: 12px;
            }}

            code {{
                background: #1A1F2E;
                padding: 2px 6px;
                border-radius: 4px;
                color: #39FF14;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 0.9em;
            }}

            pre {{
                background: #1A1F2E;
                padding: 16px;
                border-radius: 8px;
                overflow-x: auto;
                margin: 15px 0;
                border: 1px solid #2A3A5A;
            }}

            pre code {{
                background: none;
                padding: 0;
                font-size: 0.9em;
            }}

            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 15px 0;
            }}

            th, td {{
                border: 1px solid #2A4A7F;
                padding: 10px 12px;
                text-align: left;
            }}

            th {{
                background: #1A2035;
                color: #4A9EFF;
                font-weight: bold;
            }}

            tr:hover {{
                background: #1A1F2E;
            }}

            a {{
                color: #4A9EFF;
                text-decoration: none;
                border-bottom: 1px dotted #4A9EFF;
            }}

            a:hover {{
                color: #6ABEFF;
                border-bottom: 1px solid #6ABEFF;
            }}

            hr {{
                border: none;
                border-top: 1px solid #2A4A7F;
                margin: 25px 0;
            }}

            .footer {{
                text-align: center;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #2A4A7F;
                font-size: 0.8em;
                color: #6B7A99;
            }}

            .badge {{
                display: inline-block;
                background: #1A2035;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 0.7em;
                margin-left: 10px;
                color: #4A9EFF;
            }}

            @media (max-width: 768px) {{
                body {{
                    padding: 10px;
                }}
                .message {{
                    padding: 12px;
                }}
                pre {{
                    padding: 10px;
                }}
            }}

            @media print {{
                body {{
                    background: white;
                    color: black;
                }}
                .message {{
                    background: #f5f5f5;
                    break-inside: avoid;
                }}
                .user {{
                    border-left: 4px solid #0066cc;
                }}
                .assistant {{
                    border-left: 4px solid #00aa00;
                }}
                code, pre {{
                    background: #f0f0f0;
                    color: #333;
                }}
            }}
        </style>
    </head>
    <body>
        <h1>🤖 Nova Conversation</h1>
        <div class="metadata">
            📅 Saved: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}<br>
            💬 Messages: {len(self.conversation_history)}<br>
            🔗 Generated by Nova Assistant
        </div>
        <hr>
    """

        # Add each conversation message
        for i, msg in enumerate(self.conversation_history):
            role = msg.get("role", "system")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", datetime.now().strftime("%H:%M"))

            # Skip diagram messages
            if msg.get("type") == "diagram":
                continue

            # Escape content for HTML but preserve formatting
            content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            # Convert markdown code blocks to HTML with language support
            import re
            content = re.sub(r'```(\w*)\n(.*?)```', r'<pre><code class="language-\1">\2</code></pre>', content,
                             flags=re.DOTALL)

            # Convert markdown headers
            content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
            content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)

            # Convert markdown lists
            content = re.sub(r'^\* (.*?)$', r'<li>\1</li>', content, flags=re.MULTILINE)
            content = re.sub(r'^- (.*?)$', r'<li>\1</li>', content, flags=re.MULTILINE)

            # Convert blockquotes
            content = re.sub(r'^&gt; (.*?)$', r'<blockquote>\1</blockquote>', content, flags=re.MULTILINE)

            # Convert line breaks to paragraphs
            paragraphs = content.split('\n\n')
            formatted_content = []
            for para in paragraphs:
                if para.strip() and not para.strip().startswith('<'):
                    if not any(para.strip().startswith(tag) for tag in ['<h', '<pre', '<li', '<blockquote']):
                        formatted_content.append(f'<p>{para.strip()}</p>')
                    else:
                        formatted_content.append(para)
                else:
                    formatted_content.append(para)

            content = '\n'.join(formatted_content)

            # Add message number badge
            badge = f'<span class="badge">#{i + 1}</span>'

            html_content += f"""
        <div class="message {role}">
            <div class="role">
                {role.upper()} {badge}
                <span class="timestamp">[{timestamp}]</span>
            </div>
            <div class="content">
                {content}
            </div>
        </div>
    """

        html_content += f"""
        <div class="footer">
            <p>🤖 Generated by Nova Assistant v{__version__}</p>
            <p>📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </body>
    </html>
    """

        # Write the file
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)

            # Open in browser
            import webbrowser
            webbrowser.open(f"file:///{filepath}")

            self._append_conv("system", f"💾 Conversation saved to desktop: {filename}")
            self.log(f"[SAVE] Conversation saved to {filepath}")

        except Exception as e:
            self._append_conv("system", f"❌ Failed to save conversation: {e}")
            self.log(f"[SAVE ERROR] {e}")


    def _draw_aux_btn(self, hover=False):
        c = self.aux_btn
        c.delete("all")
        brd = "#9B59B6" if hover else "#2A3A5A"
        fg = "#C39BD3" if hover else "#6A4A8A"
        c.create_rectangle(1, 1, 69, 25, fill="#1A1F2E", outline=brd)
        c.create_text(35, 13, text="AUX",
                      font=("Rajdhani", 8, "bold"), fill=fg)

    def _draw_document_btn(self, hover=False):
        c = self.document_btn
        c.delete("all")
        brd = "#00BFFF" if hover else "#2A3A5A"
        fg = "#00BFFF" if hover else "#2A5A7A"
        c.create_rectangle(1, 1, 69, 25, fill="#1A1F2E", outline=brd)
        c.create_text(35, 13, text="DOCUMENT",
                      font=("Rajdhani", 8, "bold"), fill=fg)

    def _draw_aux_btn(self, hover=False):
        c = self.aux_btn
        c.delete("all")
        brd = "#9B59B6" if hover else "#2A3A5A"
        fg = "#C39BD3" if hover else "#6A4A8A"
        c.create_rectangle(1, 1, 69, 25, fill="#1A1F2E", outline=brd)
        c.create_text(35, 13, text="AUX",
                      font=("Rajdhani", 8, "bold"), fill=fg)

    def _draw_document_btn(self, hover=False):
        c = self.document_btn
        c.delete("all")
        brd = "#00BFFF" if hover else "#2A3A5A"
        fg = "#00BFFF" if hover else "#2A5A7A"
        c.create_rectangle(1, 1, 69, 25, fill="#1A1F2E", outline=brd)
        c.create_text(35, 13, text="DOCUMENT",
                      font=("Rajdhani", 8, "bold"), fill=fg)

    def _draw_send_btn(self, hover=False):
        c = self.send_btn
        c.delete("all")
        btn_w = 140
        btn_h = 32
        l, r = ("#4A9EFF", "#6ABEFF") if hover else ("#1A4A7F", "#4A9EFF")

        for i in range(1, btn_w - 1):
            t = i / (btn_w - 1)
            rc = max(0, min(255, int(int(l[1:3], 16) * (1 - t) + int(r[1:3], 16) * t)))
            gc = max(0, min(255, int(int(l[3:5], 16) * (1 - t) + int(r[3:5], 16) * t)))
            bc = max(0, min(255, int(int(l[5:7], 16) * (1 - t) + int(r[5:7], 16) * t)))
            c.create_line(i, 0, i, btn_h, fill=f"#{rc:02x}{gc:02x}{bc:02x}")

        bc2 = "#AADDFF" if hover else "#4A9EFF"
        c.create_rectangle(1, 1, btn_w - 1, btn_h - 1, outline=bc2)

        if getattr(self, '_thinking', False):
            c.create_text(btn_w // 2, btn_h // 2,
                          text="THINKING", font=F_RAJ_SM, fill=WHITE, tags="base")
            if not hasattr(self, '_animation_running') or not self._animation_running:
                self._animation_running = True
                self._thinking_animation()
        else:
            c.create_text(btn_w // 2, btn_h // 2,
                          text="SEND  ↵", font=F_RAJ_SM, fill=WHITE)

    def _make_links_clickable(self, text_widget):

        url_pattern = re.compile(r'(https?://[^\s]+|www\.[^\s]+|arxiv\.org/[^\s]+)')

        text = text_widget.get("1.0", "end-1c")

        for match in url_pattern.finditer(text):

            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"

            tag = f"link_{match.start()}"

            text_widget.tag_add(tag, start, end)

            text_widget.tag_config(
                tag,
                foreground="#4A9EFF",
                underline=True
            )

            def open_link(event, url=match.group(0)):
                url = url.rstrip('.,)"\'`')
                if not url.startswith("http"):
                    url = "https://" + url
                webbrowser.open(url)

            text_widget.tag_bind(tag, "<Button-1>", open_link)

            text_widget.tag_bind(tag, "<Enter>",
                                 lambda e: text_widget.config(cursor="hand2"))

            text_widget.tag_bind(tag, "<Leave>",
                                 lambda e: text_widget.config(cursor=""))

    def _draw_diagnose_btn(self, hover=False):
        """Draw the DIAGNOSE canvas button in amber/gold style."""
        c = self.diagnose_btn
        c.delete("all")
        brd = AMBER if hover else "#2A3A5A"
        fg = "#FFD700" if hover else "#8A7A2A"
        c.create_rectangle(1, 1, 69, 25, fill="#1A1F2E", outline=brd)
        c.create_text(35, 13, text="DIAGNOSE",
                      font=("Rajdhani", 8, "bold"), fill=fg)

    def _thinking_animation(self):
        if not self._thinking:
            self._animation_running = False
            self._draw_send_btn(False)
            return
        dots = next(self._dot_cycle)
        c = self.send_btn
        c.delete("dots")
        c.create_text(100, 16, text=dots, font=F_RAJ_SM, fill=WHITE, tags="dots")
        self.root.after(600, self._thinking_animation)

    def _draw_clear_btn(self, hover=False):
        c = self.clear_btn
        c.delete("all")
        brd = "#FF6B6B" if hover else "#2A3A5A"
        fg = "#FF8888" if hover else DIM_TEXT
        c.create_rectangle(1, 1, 69, 25, fill="#1A1F2E", outline=brd)
        c.create_text(35, 13, text="CLEAR", font=F_RAJ_SM, fill=fg)

    def _draw_globe(self, active=False):
        c = self.inet_canvas
        c.delete("all")

        if active:
            # Red pulsing globe when active
            phase = getattr(self, "_globe_flash_phase", 0)
            flash_colors = ["#FF2222", "#FF6666", "#FF0000", "#FF4444"]
            col = flash_colors[phase % len(flash_colors)]
            self._globe_flash_phase = (phase + 1) % len(flash_colors)
        else:
            col = "#3A4A6A"

        c.create_oval(3, 3, 23, 23, outline=col, width=2, fill="#1A0000" if active else "")
        c.create_arc(3, 8, 23, 18, start=0, extent=180, outline=col, style="arc")
        c.create_arc(3, 8, 23, 18, start=180, extent=180, outline=col, style="arc")

        offset = getattr(self, "_globe_rot", 0)
        c.create_line(13 + offset, 3, 13 + offset, 23, fill=col)

        if active and getattr(self, "_internet_active", False):
            self._globe_rot = (offset + 1) % 4
            self.root.after(80, lambda: self._draw_globe(True))
        elif not getattr(self, "_internet_active", False):
            if active:
                self._draw_globe(False)

    def _load_local_pdf(self):
        from tkinter import filedialog

        file_path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf")]
        )

        if not file_path:
            return

        self.log(f"[PDF] Loading local file: {file_path}")

        try:
            text = self.ai.extract_pdf_text(file_path)

            if not text.strip():
                self._append_conv("assistant", "⚠️ Could not extract text from this PDF.")
                return

            self.loaded_paper_text = text
            self.loaded_paper_source = file_path

            # Update button to show paper is loaded
            fname = os.path.basename(file_path)
            short = fname[:16] + "…" if len(fname) > 16 else fname
            self.local_pdf_btn.delete("all")
            self.local_pdf_btn.create_rectangle(1, 1, 139, 31, fill="#1A3A2E", outline="#FFD700")
            self.local_pdf_btn.create_text(70, 16, text=f"📄 {short}", font=("Rajdhani", 9), fill="#FFD700")

            self._append_conv("assistant",
                              f"📄 Loaded: {fname}\n\nUse the Paper Tools window to summarise, extract algorithms, or run examples.")

            # ← Open the tools window automatically
            self.root.after(100, self._open_paper_tools)

        except Exception as e:
            self._append_conv("assistant", f"❌ Failed to load PDF: {e}")

    def _send_code_to_autocoder(self, code):

        try:
            # ✅ PRIMARY: sandbox system (your actual setup)
            if hasattr(self, "sandbox") and self.sandbox:

                if hasattr(self.sandbox, "write_code"):
                    self.sandbox.write_code(code)

                elif hasattr(self.sandbox, "set_code"):
                    self.sandbox.set_code(code)

                elif hasattr(self.sandbox, "insert_code"):
                    self.sandbox.insert_code(code)

                else:
                    self.log("[AUTOCODER] Sandbox found but no write method")

                self.log("[AUTOCODER] Code sent to sandbox")
                return

            # ⚠️ REMOVE this broken assumption completely
            # elif hasattr(self, "code_window"):
            #     self.code_window.insert("1.0", code)

            # ✅ FALLBACK
            self.log("[AUTOCODER] No code target — printing instead")
            print("\n=== GENERATED CODE ===\n")
            print(code)

        except Exception as e:
            self.log(f"[AUTOCODER ERROR] {e}")

    def _handle_pdf_button(self):

        if self.loaded_paper_text:
            self._open_paper_tools()
        else:
            self._load_local_pdf()

    def _set_internet_indicator(self, active):
        if getattr(self, "_internet_active", None) == active:
            return

        self._internet_active = active
        self._search_bar_phase = 0
        self._search_bar_flash = False

        if active:
            self._animate_search_bar()
            try:
                self._play_chime()
            except Exception:
                pass
        else:
            # Stop animation, reset bar
            self._draw_search_bar(False)

        self.log(f"[INDICATOR] {active}")

    def _run_doc_summary(self, prompt):

        summary = self.ai.generate(prompt, use_planning=False)

        if not summary:
            summary = "Unable to summarise document."

        self._append_conv("assistant", summary)
        self.conversation_history.append(
            {"role": "assistant", "content": summary}
        )

        self.speak_text(summary)

    def _build_history_row(self, parent):
        row = tk.Frame(parent, bg=BG_LEFT)
        row.pack(fill="x", padx=10, pady=4)
        specs = [("NEW CHAT", "#3498DB", self._new_chat),
                 ("HISTORY", AMBER, self._show_history),
                 ("LESSONS", VIOLET, self._show_lessons)]

        for label, accent, cmd in specs:
            btn = tk.Canvas(row, width=100, height=28, bg=BG_LEFT, highlightthickness=0)
            btn.pack(side="left", padx=2)
            self._draw_hist_btn(btn, label, accent, False)
            btn.bind("<Enter>", lambda e, b=btn, l=label, a=accent: self._draw_hist_btn(b, l, a, True))
            btn.bind("<Leave>", lambda e, b=btn, l=label, a=accent: self._draw_hist_btn(b, l, a, False))
            btn.bind("<Button-1>", lambda e, fn=cmd: fn())
        self.ctx_label = tk.Label(parent, text="NEW CONVERSATION  ▮",
                                  font=F_CONSOLAS_SM, bg=BG_LEFT, fg=DIM_TEXT)
        self.ctx_label.pack(anchor="w", padx=12)
        self._blink_cursor()

    def _draw_hist_btn(self, c, label, accent, hover):
        c.delete("all")
        brd = accent if hover else "#253050"
        c.create_rectangle(1, 1, 99, 27, fill="#161C2A", outline=brd)
        c.create_text(50, 14, text=label, font=F_RAJ_SM,
                      fill=accent if hover else "#7A8FAF")

    def _blink_cursor(self):
        self.blink_state = not self.blink_state
        cur = self.ctx_label.cget("text")
        if self.blink_state:
            if not cur.endswith("▮"): self.ctx_label.config(text=cur + "▮")
        else:
            if cur.endswith("▮"): self.ctx_label.config(text=cur[:-1])
        self.root.after(500, self._blink_cursor)

    def _build_debug_console(self, parent):
        sec = self._section(parent, "SYSTEM LOG")

        # ── Header with controls ─────────────────────────────────────────────
        hdr = tk.Frame(sec, bg=BG_LEFT)
        hdr.pack(fill="x", padx=4, pady=(2, 0))

        tk.Label(hdr, text="", bg=BG_LEFT).pack(side="left", expand=True)

        expand_btn = tk.Label(hdr, text="⛶", font=F_RAJ_SM,
                              bg="#1A1F2E", fg=AMBER, padx=4, pady=2,
                              cursor="hand2")
        expand_btn.pack(side="right", padx=2, pady=2)
        expand_btn.bind("<Button-1>", lambda e: self._expand_syslog())

        undock_btn = tk.Label(hdr, text="⧉ Detach", font=F_RAJ_SM,
                              bg="#1A1F2E", fg=ELECTRIC_BLUE, padx=4, pady=2,
                              cursor="hand2")
        undock_btn.pack(side="right", padx=2, pady=2)
        undock_btn.bind("<Button-1>", lambda e: self.undock_system_log(self.debug_text))

        self._syslog_detach_btn = undock_btn
        self._syslog_expand_btn = expand_btn

        # ── State tracking ────────────────────────────────────────────────────
        self._syslog_outer = sec
        self._syslog_dock_parent = parent
        self._syslog_detached = False
        self._syslog_toplevel = None
        self._syslog_expanded = False

        # ── Log text widget ───────────────────────────────────────────────────
        canvas_frame = tk.Frame(sec, bg=BG_LEFT)
        canvas_frame.pack(fill="both", expand=True, padx=4, pady=4)

        self.debug_text = scrolledtext.ScrolledText(
            canvas_frame, height=7, bg=BG_CONSOLE, fg=TERMINAL_GREEN,
            font=F_COURIER, relief="flat", wrap="word", state="disabled")
        self.debug_text.pack(fill="both", expand=True)

    def log(self, msg):
        def _ins():
            # Always write to the embedded widget
            try:
                self.debug_text.config(state="normal")
                self.debug_text.insert("end", str(msg) + "\n")
                self.debug_text.see("end")
                self.debug_text.config(state="disabled")
            except Exception:
                pass

            # Mirror to detached window if open
            if getattr(self, '_syslog_detached', False) and hasattr(self, '_detached_log_text'):
                try:
                    self._detached_log_text.config(state="normal")
                    self._detached_log_text.insert("end", str(msg) + "\n")
                    self._detached_log_text.see("end")
                    self._detached_log_text.config(state="disabled")
                except Exception:
                    pass

        try:
            self.root.after(0, _ins)
        except Exception:
            pass

    def _build_right(self):
        self._build_tts_panel(self.right_panel)
        self._build_conversation_panel(self.right_panel)
        self._build_code_panel(self.right_panel)

    def _toggle_latex(self):
        self._latex_window_enabled = not self._latex_window_enabled
        if self._latex_window_enabled:
            self.latex_win.show()
            self.log("[LATEX] Window enabled — LaTeX will render locally")
        else:
            self.latex_win.hide()
            self.log("[LATEX] Window disabled — using web MathJax")

    def _maybe_render_latex(self, text: str):
        """Detect LaTeX — render to local window if enabled, always do math speech."""


        import re

        pattern = r"""
        (\$\$[\s\S]*?\$\$)
        | (\\\[.*?\\\])
        | (\\\(.*?\\\))
        | (\\(frac|int|sum|sqrt|alpha|beta|gamma|pi|theta|cdot|times|leq|geq))
        | (\\begin\{.*?\})
        """

        match = re.search(pattern, text, re.VERBOSE)
        if not match:
            return

        self.log("[LATEX] Math detected")

        if self._latex_window_enabled:
            try:
                self.latex_win.show_document(text)
            except Exception as e:
                self.log(f"[LATEX] show_document failed: {e}")


        # ── Math speech always runs regardless ──
        latex_blocks = re.findall(r'\$\$[\s\S]*?\$\$', text) or [text]

        def speak():
            try:
                for block in latex_blocks:
                    self.speak_text(block, is_math=True)
            except Exception as e:
                self.log(f"[LATEX SPEECH ERROR] {e}")

        threading.Thread(target=speak, daemon=True).start()

    def _render_latex_in_browser(self, text):
        """Save and open LaTeX response as styled HTML with MathJax."""
        import datetime as dt
        import re as re2

        try:
            import markdown
            latex_store = {}
            counter = [0]

            def protect(m):
                key = f"LATEXTOKEN{counter[0]}ENDTOKEN"
                latex_store[key] = m.group(0)
                counter[0] += 1
                return key

            protected = re.sub(
                r'\$\$.*?\$\$|\$.*?\$|\\\[.*?\\\]|\\\(.*?\\\)',
                protect, text, flags=re.DOTALL
            )
            # Convert bare URLs to markdown links so they render as clickable <a> tags
            protected = re.sub(r'(?<!\()(?<!\[)(https?://[^\s\)\]]+)', r'[\1](\1)', protected)
            html_body = markdown.markdown(protected, extensions=["tables", "fenced_code"])

            for key, val in latex_store.items():
                html_body = html_body.replace(key, val)

        except ImportError:
            html_body = f"<pre>{text}</pre>"

        html = f"""<!DOCTYPE html>
    <html><head><meta charset="utf-8">
    <script>
    MathJax = {{
      tex: {{
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
      }}
    }};
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
    body {{ background:#0D0F14; color:#C8D6E5; font-family:Georgia,serif;
           max-width:900px; margin:40px auto; padding:20px; line-height:1.7; }}
    h1,h2,h3 {{ color:#4A9EFF; }}
    code {{ background:#1A1F2E; padding:2px 6px; border-radius:3px; color:#39FF14; }}
    pre {{ background:#1A1F2E; padding:16px; border-radius:6px; overflow-x:auto; }}
    table {{ border-collapse:collapse; width:100%; }}
    th,td {{ border:1px solid #2A4A7F; padding:8px 12px; }}
    th {{ background:#1A2035; color:#4A9EFF; }}
    a {{ color:#4A9EFF; }}
    </style></head><body>{html_body}</body></html>"""

        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("nova_outputs", exist_ok=True)
        html_path = os.path.join("nova_outputs", f"nova_math_{timestamp}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        os.startfile(os.path.abspath(html_path))
        self.log(f"[LATEX] Browser render → {html_path}")




    def _open_paper_tools(self):

        if hasattr(self, "paper_tools") and self.paper_tools.winfo_exists():
            self.paper_tools.lift()
            return

        self.paper_tools = PaperToolsWindow(
            self.root,
            self.ai,
            lambda: self.loaded_paper_text,
            self.log,
            self._send_to_autocoder,
            self._play_chime
        )

    def _open_aux_window(self):
        win = tk.Toplevel(self.root)
        win.title("AUX — Nova Control Panel")
        win.configure(bg="#0D0F14")
        win.geometry("300x380")
        win.resizable(False, False)

        tk.Label(win, text="⚙  AUX PANEL",
                 bg="#0D0F14", fg="#9B59B6",
                 font=("Rajdhani", 14, "bold")).pack(pady=(16, 8))
        tk.Frame(win, bg="#2A1A4A", height=1).pack(fill="x", padx=16)

        btn_frame = tk.Frame(win, bg="#0D0F14")
        btn_frame.pack(fill="both", expand=True, padx=16, pady=16)

        def make_btn(parent, label, colour, command):
            b = tk.Button(parent, text=label,
                          bg="#1A1F2E", fg=colour,
                          font=("Rajdhani", 10, "bold"),
                          relief="flat", bd=0,
                          activebackground="#2A1A4A",
                          activeforeground=colour,
                          width=22, height=2,
                          command=command)
            b.pack(pady=4)
            b.bind("<Enter>", lambda e: b.config(bg="#2A1A4A"))
            b.bind("<Leave>", lambda e: b.config(bg="#1A1F2E"))
            return b

        make_btn(btn_frame, "💰  TOKENS", "#9B59B6", self._open_token_window)

        tk.Frame(btn_frame, bg="#2A1A4A", height=1).pack(fill="x", pady=8)
        tk.Label(btn_frame, text="⚠  ADVANCED — EXPERIENCED USERS ONLY",
                 bg="#0D0F14", fg="#F39C12",
                 font=("Rajdhani", 8)).pack()

        make_btn(btn_frame, "🧬  EVOLVE", "#FF00FF", lambda: (win.destroy(), self._run_evolution()))
        make_btn(btn_frame, "🔴  DEBUG", "#FF4444", lambda: (win.destroy(), self._run_debug()))
        make_btn(btn_frame, "🔍  DIAGNOSE", "#F39C12", lambda: (win.destroy(), self._run_diagnostic()))

        tk.Frame(win, bg="#2A1A4A", height=1).pack(fill="x", padx=16)
        tk.Button(win, text="✕  CLOSE",
                  bg="#0D0F14", fg="#FF6B6B",
                  font=("Rajdhani", 9), relief="flat",
                  command=win.destroy).pack(pady=8)

    def _open_token_window(self):
        current_model = getattr(self, "_last_model_used", "") or getattr(self.ai, "model", "unknown")
        self.log(f"[AUX DEBUG] last_in={self._last_tokens_in} last_out={self._last_tokens_out} model='{current_model}'")
        PRICING = self._fetch_live_pricing() or {
            "anthropic/claude-sonnet-4-6": {"in": 3.00, "out": 15.00},
            "anthropic/claude-opus-4-6": {"in": 15.00, "out": 75.00},
            "deepseek/deepseek-chat-v3-0324": {"in": 0.27, "out": 1.10},
            "deepseek/deepseek-r1": {"in": 0.55, "out": 2.19},
            "qwen/qwen2.5-coder-72b-instruct": {"in": 0.40, "out": 1.20},
            "qwen/qwen3-235b-a22b": {"in": 0.50, "out": 1.50},
            "qwen/qwen3-coder": {"in": 0.50, "out": 1.50},
            "qwen/qwen3.5-122b-a10b": {"in": 0.40, "out": 1.20},
        }

        win = tk.Toplevel(self.root)
        win.title("Token Costs")
        win.configure(bg="#0D0F14")
        win.geometry("520x560")
        win.resizable(True, True)

        # ── Fixed header ────────────────────────────────────────
        tk.Label(win, text="💰  TOKEN COSTS",
                 bg="#0D0F14", fg="#9B59B6",
                 font=("Rajdhani", 14, "bold")).pack(pady=(12, 4))
        tk.Frame(win, bg="#2A1A4A", height=1).pack(fill="x", padx=12)

        # ── Scrollable body ─────────────────────────────────────
        body = tk.Frame(win, bg="#0D0F14")
        body.pack(fill="both", expand=True, padx=0, pady=0)

        canvas = tk.Canvas(body, bg="#0D0F14", highlightthickness=0)
        scrollbar = tk.Scrollbar(body, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg="#0D0F14")
        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_resize(event):
            canvas.itemconfig(canvas_window, width=event.width)

        inner.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", _on_canvas_resize)
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # ── Content goes into inner ─────────────────────────────
        current_model = getattr(self, "_last_model_used", "") or getattr(self.ai, "model", "unknown")

        # Flexible pricing lookup — exact then partial match
        pricing = PRICING.get(current_model)
        if not pricing:
            for key in PRICING:
                if key in current_model or current_model in key:
                    pricing = PRICING[key]
                    break
        if not pricing:
            pricing = {"in": 0.0, "out": 0.0}

        last_cost_in = (self._last_tokens_in / 1_000_000) * pricing["in"]
        last_cost_out = (self._last_tokens_out / 1_000_000) * pricing["out"]
        last_cost = last_cost_in + last_cost_out

        sess_cost_in = (self._session_tokens_in / 1_000_000) * pricing["in"]
        sess_cost_out = (self._session_tokens_out / 1_000_000) * pricing["out"]
        sess_cost = sess_cost_in + sess_cost_out

        def row(parent, label, value, colour="#C8D6E5"):
            f = tk.Frame(parent, bg="#0D0F14")
            f.pack(fill="x", padx=10, pady=1)
            tk.Label(f, text=label, bg="#0D0F14", fg="#6A7A9A",
                     font=("Rajdhani", 9), width=22, anchor="w").pack(side="left")
            tk.Label(f, text=value, bg="#0D0F14", fg=colour,
                     font=("Rajdhani", 9, "bold"), anchor="w").pack(side="left")

        # Last query
        cost_frame = tk.LabelFrame(inner, text=" TOKEN COSTS ",
                                   bg="#0D0F14", fg="#9B59B6",
                                   font=("Rajdhani", 9, "bold"),
                                   bd=1, relief="solid")
        cost_frame.pack(fill="x", padx=12, pady=8)

        tk.Label(cost_frame, text=f"Model: {current_model}",
                 bg="#0D0F14", fg="#4A9EFF",
                 font=("Rajdhani", 9)).pack(anchor="w", padx=10, pady=(4, 2))
        tk.Frame(cost_frame, bg="#1A2A4A", height=1).pack(fill="x", padx=10, pady=2)

        tk.Label(cost_frame, text="LAST QUERY",
                 bg="#0D0F14", fg="#9B59B6",
                 font=("Rajdhani", 8, "bold")).pack(anchor="w", padx=10)
        row(cost_frame, "Input tokens:", f"{self._last_tokens_in:,}")
        row(cost_frame, "Output tokens:", f"{self._last_tokens_out:,}")
        row(cost_frame, "Input cost:", f"${last_cost_in:.6f}")
        row(cost_frame, "Output cost:", f"${last_cost_out:.6f}")
        row(cost_frame, "Query total:", f"${last_cost:.6f}", "#FFD700")

        tk.Frame(cost_frame, bg="#1A2A4A", height=1).pack(fill="x", padx=10, pady=4)
        tk.Label(cost_frame, text="SESSION TOTAL",
                 bg="#0D0F14", fg="#9B59B6",
                 font=("Rajdhani", 8, "bold")).pack(anchor="w", padx=10)
        row(cost_frame, "Queries this session:", f"{self._session_queries:,}")
        row(cost_frame, "Total input tokens:", f"{self._session_tokens_in:,}")
        row(cost_frame, "Total output tokens:", f"{self._session_tokens_out:,}")
        row(cost_frame, "Session cost:", f"${sess_cost:.4f}", "#39FF14")

        # Pricing table
        price_frame = tk.LabelFrame(inner, text=" MODEL PRICING (per 1M tokens) ",
                                    bg="#0D0F14", fg="#9B59B6",
                                    font=("Rajdhani", 9, "bold"),
                                    bd=1, relief="solid")
        price_frame.pack(fill="x", padx=12, pady=4)

        hrow = tk.Frame(price_frame, bg="#0D0F14")
        hrow.pack(fill="x", padx=10, pady=(4, 1))
        for txt, w in [("Model", 28), ("In $", 8), ("Out $", 8)]:
            tk.Label(hrow, text=txt, bg="#0D0F14", fg="#4A9EFF",
                     font=("Rajdhani", 8, "bold"), width=w,
                     anchor="w").pack(side="left")

        for model, p in PRICING.items():
            short = model.split("/")[-1][:26]
            is_current = model == current_model
            fg_col = "#FFD700" if is_current else "#6A7A9A"
            f = tk.Frame(price_frame, bg="#0D0F14")
            f.pack(fill="x", padx=10)
            tk.Label(f, text=("▶ " if is_current else "  ") + short,
                     bg="#0D0F14", fg=fg_col,
                     font=("Rajdhani", 8), width=28, anchor="w").pack(side="left")
            tk.Label(f, text=f"{p['in']:.2f}",
                     bg="#0D0F14", fg=fg_col,
                     font=("Rajdhani", 8), width=8, anchor="w").pack(side="left")
            tk.Label(f, text=f"{p['out']:.2f}",
                     bg="#0D0F14", fg=fg_col,
                     font=("Rajdhani", 8), width=8, anchor="w").pack(side="left")

        # ── Fixed footer with buttons ───────────────────────────
        tk.Frame(win, bg="#2A1A4A", height=1).pack(fill="x", padx=12)
        btn_frame = tk.Frame(win, bg="#0D0F14")
        btn_frame.pack(fill="x", padx=12, pady=8)

        def reset_session():
            self._session_tokens_in = 0
            self._session_tokens_out = 0
            self._session_queries = 0
            win.destroy()
            self._open_token_window()

        tk.Button(btn_frame, text="↺  RESET SESSION",
                  bg="#1A1F2E", fg="#9B59B6",
                  font=("Rajdhani", 9, "bold"),
                  relief="flat", width=16,
                  command=reset_session).pack(side="left", padx=4)

        tk.Button(btn_frame, text="✕  CLOSE",
                  bg="#1A1F2E", fg="#FF6B6B",
                  font=("Rajdhani", 9, "bold"),
                  relief="flat", width=10,
                  command=win.destroy).pack(side="right", padx=4)

    def _send_to_autocoder(self, code):
        replacements = {
            "\u201C": '"', "\u201D": '"',
            "\u2018": "'", "\u2019": "'",
            "\u2014": "-", "\u2013": "-",
            "\u2212": "-",  # ← Unicode minus sign → hyphen
            "\u2026": "...", "\u00d7": "*",
            "\u00f7": "/", "\u2192": "->",
        }
        for bad, good in replacements.items():
            code = code.replace(bad, good)

        self._append_conv("assistant", code)

        if hasattr(self, "code_window") and self.code_window.winfo_exists():
            self.code_window.set_code(code)
            self.code_window.show()

            # Build a proper task so the smart loop can FIX errors on retry
            task = f"""You are given this Python code to run. 
    Execute it exactly as written. If there are any errors, fix them and try again.
    IMPORTANT: Use only ASCII characters in comments and strings — no em dashes, 
    smart quotes, or special Unicode symbols.
    ````python
    {code}
    ```"""

            threading.Thread(
                target=self._run_autocoder,
                args=(task,),
                daemon=True
            ).start()

    def _build_conversation_panel(self, parent):
        """Build the conversation panel with detach capability"""
        # Store parent so we can re-dock later
        self._conv_dock_parent = parent

        outer = tk.Frame(parent, bg=SEAM, padx=1, pady=1)
        outer.pack(fill="both", expand=True, padx=10, pady=4)
        self._seam_frames.append(outer)
        self._conv_outer = outer  # ← save reference for re-docking

        sec = tk.Frame(outer, bg=BG_RIGHT)
        sec.pack(fill="both", expand=True)
        self._conv_sec = sec  # ← save reference

        # ── Header ──────────────────────────────────────
        hdr = tk.Frame(sec, bg=BG_RIGHT)
        hdr.pack(fill="x")

        tk.Label(hdr, text="CONVERSATION", font=F_RAJ_SM,
                 bg=BG_RIGHT, fg=ELECTRIC_BLUE).pack(side="left", padx=6, pady=(4, 0))

        # Clear button
        clear_lbl = tk.Label(hdr, text="✕", font=F_RAJ_SM,
                             bg="#1A1F2E", fg="#FF6B6B", padx=4, pady=2, cursor="hand2")
        clear_lbl.pack(side="right", padx=2, pady=2)
        clear_lbl.bind("<Button-1>", lambda e: self._clear_conversation())

        # Expand button (enlarges detached window)
        self._expand_btn = tk.Label(hdr, text="⛶", font=F_RAJ_SM,
                                    bg="#1A1F2E", fg=AMBER, padx=4, pady=2,
                                    cursor="hand2")
        self._expand_btn.pack(side="right", padx=2, pady=2)
        self._expand_btn.bind("<Button-1>", lambda e: self._expand_conv())

        # Detach / Dock toggle button
        self._detach_btn = tk.Label(hdr, text="⧉ Detach", font=F_RAJ_SM,
                                    bg="#1A1F2E", fg=ELECTRIC_BLUE, padx=4, pady=2,
                                    cursor="hand2")
        self._detach_btn.pack(side="right", padx=2, pady=2)
        self._detach_btn.bind("<Button-1>", lambda e: self._toggle_detach_conv())

        # ── Canvas + scrollbar ─────────────────────────
        self.conv_canvas = tk.Canvas(sec, bg="#0C1219", highlightthickness=0)
        self.conv_scrollbar = tk.Scrollbar(sec, orient="vertical",
                                           command=self.conv_canvas.yview)
        self.conv_canvas.configure(yscrollcommand=self.conv_scrollbar.set)

        self.conv_scrollbar.pack(side="right", fill="y")
        self.conv_canvas.pack(side="left", fill="both", expand=True)

        self.conv_frame = tk.Frame(self.conv_canvas, bg="#0C1219")
        self.conv_canvas.create_window((0, 0), window=self.conv_frame,
                                       anchor="nw", width=self.conv_canvas.winfo_width())

        def _configure_canvas(event):
            self.conv_canvas.configure(scrollregion=self.conv_canvas.bbox("all"))

        self.conv_frame.bind("<Configure>", _configure_canvas)

        # Fix: Properly define the resize function
        def _resize_canvas(event):
            """Resize the canvas window when canvas is resized"""
            # Find the window item and resize it
            for item in self.conv_canvas.find_all():
                if self.conv_canvas.type(item) == "window":
                    self.conv_canvas.itemconfig(item, width=event.width)
                    break

        self.conv_canvas.bind("<Configure>", _resize_canvas)

        # Fix: Properly define mousewheel function
        def _on_mousewheel(event):
            """Handle mousewheel scrolling"""
            self.conv_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        # Bind mousewheel to the canvas (not globally to avoid conflicts)
        self.conv_canvas.bind("<MouseWheel>", _on_mousewheel)

        # Also bind when mouse enters the canvas area
        self.conv_canvas.bind("<Enter>", lambda e: self.conv_canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self.conv_canvas.bind("<Leave>", lambda e: self.conv_canvas.unbind_all("<MouseWheel>"))

    def _fetch_live_pricing(self):
        """Fetch current model pricing from OpenRouter."""
        try:
            api_key = self.ai.cloud_config.get("api_key", "") if self.ai.cloud_config else ""
            if not api_key:
                return None
            r = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            if r.status_code == 200:
                pricing = {}
                for m in r.json().get("data", []):
                    mid = m.get("id", "")
                    p = m.get("pricing", {})
                    try:
                        pricing[mid] = {
                            "in": float(p.get("prompt", 0)) * 1_000_000,
                            "out": float(p.get("completion", 0)) * 1_000_000
                        }
                    except Exception:
                        pass
                self.log(f"[AUX] Live pricing fetched — {len(pricing)} models")
                return pricing
        except Exception as e:
            self.log(f"[AUX] Pricing fetch failed: {e}")
        return None

    # ══════════════════════════════════════
    # DETACHABLE CONVERSATION WINDOW
    # ══════════════════════════════════════
    def _toggle_detach_conv(self):
        """Detach conversation into its own window, or dock it back."""
        if self._conv_detached:
            self._dock_conv()
        else:
            self._detach_conv()

    def _detach_conv(self):
        """Lift the conversation panel out into a Toplevel window."""
        if self._conv_detached:
            return

        # Hide the original conversation panel
        self._conv_outer.pack_forget()

        # ── Create the Toplevel ──────────────────────────
        top = tk.Toplevel(self.root)
        top.title("Nova — Conversation")
        top.geometry("860x700+200+80")
        top.configure(bg=BG_ROOT)
        top.protocol("WM_DELETE_WINDOW", self._dock_conv)
        self._conv_toplevel = top

        # Create a NEW conversation panel in the toplevel
        self._conv_detached = True
        self.conv_canvas.unbind_all("<MouseWheel>")  # adds scroll
        self._create_detached_conversation(top)
        # Update button label
        self._detach_btn.config(text="⬛ Dock", fg=GREEN_GLOW)
        self._conv_detached = True
        self.log("[CONV] Detached to separate window")

    def _dock_conv(self):

        if not self._conv_detached:
            return

        if self._conv_toplevel:
            self._conv_toplevel.destroy()
            self._conv_toplevel = None

        for attr in ['_detached_canvas', '_detached_frame', '_detached_outer']:
            if hasattr(self, attr):
                delattr(self, attr)

        for widget in self.conv_frame.winfo_children():
            widget.destroy()

        self._conv_outer.pack(
            in_=self._conv_dock_parent,
            fill="both", expand=True,
            padx=10, pady=4
        )

        def _rebuild_all():
            self.root.update_idletasks()

            for entry in self.conversation_history:

                if entry.get("type") == "diagram":

                    if entry.get("engine") == "graphviz":
                        self.show_graphviz_diagram(entry["path"], store=False, target_frame=self.conv_frame)
                    else:
                        self.show_diagram(entry["path"], store=False)
                else:

                    self._rebuild_message(
                        self.conv_frame,
                        self.conv_canvas,
                        entry.get("role", "assistant"),
                        entry.get("content", "")
                    )

            self.conv_canvas.yview_moveto(1.0)

            # ── Restore main canvas mousewheel after docking ──
            def _on_mousewheel(event):
                self.conv_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

            self.conv_canvas.bind("<Enter>", lambda e: self.conv_canvas.bind_all("<MouseWheel>", _on_mousewheel))
            self.conv_canvas.bind("<Leave>", lambda e: self.conv_canvas.unbind_all("<MouseWheel>"))

        self._conv_detached = False
        self._detach_btn.config(text="⧉ Detach", fg=ELECTRIC_BLUE)

        self.root.after(300, _rebuild_all)

        self.log("[CONV] Docked back into main window")

    def _create_message_in_frame(self, target_frame, target_canvas, role, text):
        """Direct message creation without going through the queue"""
        msg_frame = tk.Frame(target_frame, bg="#0C1219")
        msg_frame.pack(fill="x", padx=10, pady=(5, 0))

        header = tk.Frame(msg_frame, bg="#0C1219")
        header.pack(fill="x")

        role_text = "You" if role == "user" else "Nova" if role == "assistant" else "System"
        role_color = ELECTRIC_BLUE if role == "user" else FG_CODE if role == "assistant" else DIM_TEXT

        tk.Label(header, text=role_text, font=("Rajdhani", 11, "bold"),
                 bg="#0C1219", fg=role_color).pack(side="left")

        tk.Label(header, text=f"[{datetime.now().strftime('%H:%M')}]",
                 font=F_RAJ_SM, bg="#0C1219", fg=DIM_TEXT).pack(side="left", padx=(5, 0))

        if "```" in text:
            self._display_with_code_blocks(msg_frame, text)
        else:
            self._create_message_text(msg_frame, text)

        tk.Frame(msg_frame, bg=SEAM, height=1).pack(fill="x", pady=(5, 0))

        if target_canvas:
            target_canvas.update_idletasks()
            target_canvas.configure(scrollregion=target_canvas.bbox("all"))

    def _rebuild_message(self, target_frame, target_canvas, role, text=None, diagram_path=None):
        """Rebuild a single message in the specified frame"""

        msg_frame = tk.Frame(target_frame, bg="#0C1219")
        msg_frame.pack(fill="x", padx=10, pady=(5, 0))

        header = tk.Frame(msg_frame, bg="#0C1219")
        header.pack(fill="x")

        role_text = "You" if role == "user" else "Nova" if role == "assistant" else "System"
        role_color = ELECTRIC_BLUE if role == "user" else FG_CODE if role == "assistant" else DIM_TEXT

        tk.Label(header, text=role_text, font=("Rajdhani", 11, "bold"),
                 bg="#0C1219", fg=role_color).pack(side="left")

        tk.Label(header, text=f"[{datetime.now().strftime('%H:%M')}]",
                 font=F_RAJ_SM, bg="#0C1219", fg=DIM_TEXT).pack(side="left", padx=(5, 0))

        if role == "assistant" and text and len(text) > 200:
            save_btn = tk.Label(header, text="💾", font=F_RAJ_MED,
                                bg="#0C1219", fg=ELECTRIC_BLUE, cursor="hand2")
            save_btn.pack(side="left", padx=(12, 4))

            save_btn.bind("<Button-1>", lambda e, c=text: self._save_response_as_html(c, save_btn))

        # ---- CONTENT ----
        if diagram_path:
            self.show_diagram(diagram_path, store=False)

        elif text and "```" in text:
            self._display_with_code_blocks(msg_frame, text)

        elif text:
            self._create_message_text(msg_frame, text)

        # Separator
        tk.Frame(msg_frame, bg=SEAM, height=1).pack(fill="x", pady=(5, 0))

        if target_canvas:
            target_canvas.update_idletasks()
            target_canvas.yview_moveto(1.0)

    def _create_detached_conversation(self, parent):
        """Create a new conversation panel in the detached window"""
        outer = tk.Frame(parent, bg=SEAM, padx=1, pady=1)
        outer.pack(fill="both", expand=True, padx=10, pady=4)

        sec = tk.Frame(outer, bg=BG_RIGHT)
        sec.pack(fill="both", expand=True)

        # Header
        hdr = tk.Frame(sec, bg=BG_RIGHT)
        hdr.pack(fill="x")

        tk.Label(hdr, text="CONVERSATION (DETACHED)", font=F_RAJ_SM,
                 bg=BG_RIGHT, fg=ELECTRIC_BLUE).pack(side="left", padx=6, pady=(4, 0))

        # Dock button
        dock_btn = tk.Label(hdr, text="⬛ Dock", font=F_RAJ_SM,
                            bg="#1A1F2E", fg=GREEN_GLOW, padx=4, pady=2,
                            cursor="hand2")
        dock_btn.pack(side="right", padx=2, pady=2)
        dock_btn.bind("<Button-1>", lambda e: self._dock_conv())

        # Canvas and scrollbar
        canvas = tk.Canvas(sec, bg="#0C1219", highlightthickness=0)
        scrollbar = tk.Scrollbar(sec, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        frame = tk.Frame(canvas, bg="#0C1219")
        canvas.create_window((0, 0), window=frame, anchor="nw", width=canvas.winfo_width())

        # ── scrollregion update so slider has a range to work with ──
        def _configure_frame(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        frame.bind("<Configure>", _configure_frame)

        def _resize_canvas(event):
            for item in canvas.find_all():
                if canvas.type(item) == "window":
                    canvas.itemconfig(item, width=event.width)
                    break

        canvas.bind("<Configure>", _resize_canvas)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Enter>", lambda e: canvas.focus_set())
        frame.bind("<MouseWheel>", _on_mousewheel)
        frame.bind("<Enter>", lambda e: canvas.focus_set())
        parent.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        parent.bind("<FocusIn>", lambda e: parent.focus_force())

        # Store references
        self._detached_canvas = canvas
        self._detached_frame = frame
        self._detached_outer = outer

        # Rebuild messages from conversation history
        for msg in self.conversation_history:
            if msg.get("type") == "diagram":
                if msg.get("engine") == "graphviz":
                    self.show_graphviz_diagram(msg["path"], store=False)
                else:
                    self.show_diagram(msg["path"], store=False)
            else:
                self._append_to_detached(msg["role"], msg["content"])

    def _append_to_detached(self, role, text):
        """Append a message to the detached conversation"""
        if not hasattr(self, '_detached_frame'):
            return

        msg_frame = tk.Frame(self._detached_frame, bg="#0C1219")
        msg_frame.pack(fill="x", padx=10, pady=(5, 0))

        header = tk.Frame(msg_frame, bg="#0C1219")
        header.pack(fill="x")

        role_text = "You" if role == "user" else "Nova" if role == "assistant" else "System"
        role_color = ELECTRIC_BLUE if role == "user" else FG_CODE if role == "assistant" else DIM_TEXT

        tk.Label(header, text=role_text, font=("Rajdhani", 11, "bold"),
                 bg="#0C1219", fg=role_color).pack(side="left")

        tk.Label(header, text=f"[{datetime.now().strftime('%H:%M')}]",
                 font=F_RAJ_SM, bg="#0C1219", fg=DIM_TEXT).pack(side="left", padx=(5, 0))

        if role == "assistant" and text and len(text) > 200:
            save_btn = tk.Label(header, text="💾", font=F_RAJ_MED,
                                bg="#0C1219", fg=ELECTRIC_BLUE, cursor="hand2")
            save_btn.pack(side="left", padx=(12, 4))

            save_btn.bind("<Button-1>", lambda e, c=text: self._save_response_as_html(c, save_btn))

        # ---- CONTENT ----
        if "```" in text:
            self._display_with_code_blocks(msg_frame, text)
        else:
            self._create_message_text(msg_frame, text)

        tk.Frame(msg_frame, bg=SEAM, height=1).pack(fill="x", pady=(5, 0))

        if hasattr(self, '_detached_canvas'):
            self._detached_canvas.yview_moveto(1.0)

    def _expand_conv(self):
        """Expand the detached window to a larger comfortable reading size."""
        if not self._conv_detached or not self._conv_toplevel:
            # If docked, detach first then expand
            self._detach_conv()
            # Small delay to allow window to create
            self.root.after(100, self._expand_conv)
            return

        top = self._conv_toplevel
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        if getattr(self, '_conv_expanded', False):
            # Shrink back to normal detached size
            top.geometry("860x700+200+80")
            self._conv_expanded = False
            self._expand_btn.config(text="⛶", fg=AMBER)
            self.log("[CONV] Restored to normal size")
        else:
            # Expand to ~80% of screen
            w = int(sw * 0.80)
            h = int(sh * 0.85)
            x = (sw - w) // 2
            y = (sh - h) // 2
            top.geometry(f"{w}x{h}+{x}+{y}")
            self._conv_expanded = True
            self._expand_btn.config(text="⊡", fg=GREEN_GLOW)
            self.log("[CONV] Expanded to large view")

    def _display_with_code_blocks(self, parent, text):

        # Split by code blocks
        parts = re.split(r'(```\w*\n.*?```)', text, flags=re.DOTALL)

        for part in parts:

            # ── CODE BLOCK ─────────────────────
            if part.startswith('```') and part.endswith('```'):

                lines = part.split('\n')
                first_line = lines[0]

                # Detect language
                lang = first_line[3:].strip() if len(first_line) > 3 else "python"

                # Extract code
                code = '\n'.join(lines[1:-1]) if len(lines) > 2 else ""

                if code.strip():
                    code_display = CodeDisplay(parent, bg_color="#0C1219")
                    code_display.set_code(code, lang)
                    code_display.pack(fill="x", padx=10, pady=5)

            # ── NORMAL TEXT ────────────────────
            else:

                if not part.strip():
                    continue

                part = part.replace("\t", "    ")

                self._create_message_text(parent, part.strip())

    # CODE PANEL (existing)
    # ══════════════════════════════════════
    def _build_code_panel(self, parent):
        outer = tk.Frame(parent, bg=SEAM, padx=2, pady=2)
        outer.pack(fill="both", expand=True, padx=10, pady=4)
        self._seam_frames.append(outer)
        inner = tk.Frame(outer, bg=BG_RIGHT);
        inner.pack(fill="both", expand=True)

        status_bar = tk.Canvas(inner, height=22, bg="#0A0C10", highlightthickness=0)
        status_bar.pack(fill="x")
        status_bar.create_text(10, 11, text="CODE ENVIRONMENT",
                               font=F_RAJ_SM, fill="#3A5A8A", anchor="w")

        ctrl_bar = tk.Frame(inner, bg="#0A0C10");
        ctrl_bar.pack(fill="x")
        view_btn = tk.Canvas(ctrl_bar, width=110, height=24, bg="#0A0C10", highlightthickness=0)
        view_btn.pack(side="right", padx=6, pady=2)
        view_btn.create_rectangle(1, 1, 109, 23, fill="#1A2035", outline=ELECTRIC_BLUE)
        view_btn.create_text(55, 12, text="VIEW CODE", font=F_RAJ_BTN, fill=ELECTRIC_BLUE)
        view_btn.bind("<Button-1>", lambda e: self.code_window.show())

        self.halt_btn = tk.Canvas(ctrl_bar, width=100, height=24, bg="#0A0C10", highlightthickness=0)
        self.halt_btn.pack(side="left", padx=6, pady=2)
        self._draw_halt_btn(False)
        self.halt_btn.bind("<Button-1>", lambda e: self._on_halt())

        self.exec_status = tk.Label(ctrl_bar, text="IDLE", font=F_RAJ_SM,
                                    bg="#0A0C10", fg=DIM_TEXT)
        self.exec_status.pack(side="left", padx=6)

        self.code_display = scrolledtext.ScrolledText(
            inner, bg="#0C1219", fg="#A8D8A8",
            font=F_COURIER, relief="flat", wrap="none", state="disabled")
        self.code_display.pack(fill="both", expand=True, padx=4, pady=4)
        self.code_display.config(state="normal")
        self.code_display.insert("1.0", "# Code will appear here when Nova writes a program\n")
        self.code_display.config(state="disabled")
        try:
            self.code_display.vbar.config(bg="#1A2A3A", troughcolor="#0D1117")
        except:
            pass

    def _draw_halt_btn(self, active=False):
        c = self.halt_btn;
        c.delete("all")
        if active:
            c.create_rectangle(1, 1, 99, 23, fill="#4A1A1A", outline=RED_GLOW)
            c.create_text(50, 12, text="⏹ HALT", font=F_RAJ_BTN, fill=RED_GLOW)
        else:
            c.create_rectangle(1, 1, 99, 23, fill="#1A1F2E", outline="#3A4A5A")
            c.create_text(50, 12, text="⏹ HALT", font=F_RAJ_BTN, fill=DIM_TEXT)

    # ══════════════════════════════════════
    # CONVERSATION DISPLAY (updated)
    # ══════════════════════════════════════
    def _append_conv(self, role, text):
        """Append a message to the conversation with proper formatting"""

        def _ins():

            if self._conv_detached and hasattr(self, '_detached_frame'):
                target_frame = self._detached_frame
                target_canvas = self._detached_canvas
            else:
                target_frame = self.conv_frame
                target_canvas = self.conv_canvas

            msg_frame = tk.Frame(target_frame, bg="#0C1219")
            msg_frame.pack(fill="x", padx=10, pady=(10, 6))

            header = tk.Frame(msg_frame, bg="#0C1219")
            header.pack(fill="x")

            role_text = "You" if role == "user" else "Nova" if role == "assistant" else "System"
            role_color = ELECTRIC_BLUE if role == "user" else FG_CODE if role == "assistant" else DIM_TEXT

            tk.Label(
                header,
                text=role_text,
                font=("Rajdhani", 11, "bold"),
                bg="#0C1219",
                fg=role_color
            ).pack(side="left")

            tk.Label(
                header,
                text=f"[{datetime.now().strftime('%H:%M')}]",
                font=F_RAJ_SM,
                bg="#0C1219",
                fg=DIM_TEXT
            ).pack(side="left", padx=(5, 0))

            # ── Save button ──────────────────────────────────────────
            if role == "assistant":
                save_btn = tk.Label(header, text="💾", font=F_RAJ_MED,
                                    bg="#0C1219", fg=ELECTRIC_BLUE, cursor="hand2")
                save_btn.pack(side="left", padx=(12, 4))

                save_btn.bind("<Button-1>", lambda e, c=text: self._save_response_as_html(c, save_btn))

            # ── IMAGE RENDERING ────────────────────────────────────
            if isinstance(text, str) and text.startswith("IMAGE_GRID:"):
                path = text.split(":", 1)[1].strip()
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(path)
                    img.thumbnail((500, 500))
                    photo = ImageTk.PhotoImage(img)
                    img_label = tk.Label(msg_frame, image=photo, bg="#0C1219")
                    img_label.image = photo
                    img_label.pack(anchor="w", pady=(5, 5))
                except Exception as e:
                    self.log(f"[IMAGE ERROR] {e}")

            # ── CONTENT ───────────────────────────────────────────
            if isinstance(text, dict) and text.get("type") == "diagram":
                self.show_diagram(text["path"], store=False)

            elif "```" in text:
                self._display_with_code_blocks(msg_frame, text)

            else:
                clean = self._clean_markdown(text)
                self._create_message_text(msg_frame, clean)

            # Separator
            tk.Frame(msg_frame, bg=SEAM, height=1).pack(fill="x", pady=(5, 0))

            if target_canvas:
                target_canvas.yview_moveto(1.0)

            children = target_frame.winfo_children()
            while len(children) > 300:
                children[0].destroy()

        self.root.after(0, _ins)

    def _clear_conversation(self):
        """Clear all messages from conversation"""
        for widget in self.conv_frame.winfo_children():
            widget.destroy()
        self._append_conv("system", "New conversation started")

    # ══════════════════════════════════════
    # HISTORY / CHAT MANAGEMENT
    # ══════════════════════════════════════
    def _new_chat(self):
        """Start a new conversation and clean up old images"""
        import os
        import glob
        import shutil

        # Clear conversation history
        self.conversation_history = []
        self._clear_conversation()

        # Reset UI elements
        self._set_internet_indicator(False)
        self._last_search_query = None
        self.ctx_label.config(text="NEW CONVERSATION", fg=DIM_TEXT)

        # Clear loaded PDF if any
        if self.loaded_paper_text:
            self.loaded_paper_text = ""
            self.loaded_paper_source = ""
            # Reset PDF button appearance
            self.local_pdf_btn.delete("all")
            self.local_pdf_btn.create_rectangle(1, 1, 139, 31, fill="#2A4A2E", outline="#2ECC71")
            self.local_pdf_btn.create_text(70, 16, text="📂 LOAD PDF", font=F_RAJ_SM, fill="white")

        # CLEAN UP ALL IMAGES AND DIAGRAMS
        self.log("[CHAT] Cleaning up old images and diagrams...")

        # Clean downloaded_images folder
        downloaded_images_dir = "downloaded_images"
        if os.path.exists(downloaded_images_dir):
            try:
                files = glob.glob(os.path.join(downloaded_images_dir, "*"))
                count = 0
                for f in files:
                    try:
                        if os.path.isfile(f):
                            os.remove(f)
                            count += 1
                    except Exception as e:
                        self.log(f"[CLEANUP] Could not remove {f}: {e}")
                self.log(f"[CLEANUP] Cleaned {count} files from {downloaded_images_dir}")
            except Exception as e:
                self.log(f"[CLEANUP] Error cleaning {downloaded_images_dir}: {e}")

        # Clean web_images folder
        web_images_dir = "web_images"
        if os.path.exists(web_images_dir):
            try:
                files = glob.glob(os.path.join(web_images_dir, "*"))
                count = 0
                for f in files:
                    try:
                        if os.path.isfile(f):
                            os.remove(f)
                            count += 1
                    except Exception as e:
                        self.log(f"[CLEANUP] Could not remove {f}: {e}")
                self.log(f"[CLEANUP] Cleaned {count} files from {web_images_dir}")
            except Exception as e:
                self.log(f"[CLEANUP] Error cleaning {web_images_dir}: {e}")

        # Clean diagrams folder (Graphviz diagrams)
        diagrams_dir = "diagrams"
        if os.path.exists(diagrams_dir):
            try:
                # Clean PNG files
                png_files = glob.glob(os.path.join(diagrams_dir, "*.png"))
                count = 0
                for f in png_files:
                    try:
                        if os.path.isfile(f):
                            os.remove(f)
                            count += 1
                    except Exception as e:
                        self.log(f"[CLEANUP] Could not remove {f}: {e}")

                # Clean DOT files (Graphviz source files)
                dot_files = glob.glob(os.path.join(diagrams_dir, "*.dot"))
                for f in dot_files:
                    try:
                        if os.path.isfile(f):
                            os.remove(f)
                            count += 1
                    except Exception as e:
                        self.log(f"[CLEANUP] Could not remove {f}: {e}")

                # Clean any other temporary files
                other_files = glob.glob(os.path.join(diagrams_dir, "gv_diagram_*"))
                for f in other_files:
                    try:
                        if os.path.isfile(f) and not f.endswith(('.png', '.dot')):
                            os.remove(f)
                            count += 1
                    except Exception as e:
                        self.log(f"[CLEANUP] Could not remove {f}: {e}")

                self.log(f"[CLEANUP] Cleaned {count} files from {diagrams_dir}")
            except Exception as e:
                self.log(f"[CLEANUP] Error cleaning {diagrams_dir}: {e}")

        # RESET THE STATE FILE - start fresh
        self.state = {
            "last_result": None,
            "last_task": None,
            "last_type": None,
            "history": [],
            "lessons": []
        }
        # Preserve memory block on new chat
        if hasattr(self, 'memory'):
            self.state["memory"] = self.memory.state.get("memory", {})
        self.save_state()
        # Add system message
        self._append_conv("system", "New conversation started - All images and diagrams cleaned")

        self.log("[CHAT] New conversation - state file reset to fresh start")

    def _show_history(self):
        popup = tk.Toplevel(self.root)
        popup.title("History");
        popup.geometry("700x500")
        popup.configure(bg=BG_LEFT)
        tk.Label(popup, text="CONVERSATION HISTORY", font=F_RAJ_BIG,
                 bg=BG_LEFT, fg=ELECTRIC_BLUE).pack(pady=10)
        txt = scrolledtext.ScrolledText(popup, bg=BG_CONSOLE, fg=TERMINAL_GREEN,
                                        font=F_COURIER, wrap="word")
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        if not self.conversation_history:
            txt.insert("end", "No history yet.")
        else:
            for e in self.conversation_history:
                role = "You" if e["role"] == "user" else "Nova"
                txt.insert("end", f"{role}: {e['content'][:200]}\n\n")
        txt.config(state="disabled")

    def _show_lessons(self):
        popup = tk.Toplevel(self.root)
        popup.title("Lessons");
        popup.geometry("700x500")
        popup.configure(bg=BG_LEFT)
        tk.Label(popup, text="CODING LESSONS LEARNED", font=F_RAJ_BIG,
                 bg=BG_LEFT, fg=VIOLET).pack(pady=10)
        txt = scrolledtext.ScrolledText(popup, bg=BG_CONSOLE, fg="#D4AAFF",
                                        font=F_COURIER, wrap="word")
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        if hasattr(self, 'ai'):
            txt.insert("end", self.ai.mistake_memory.export_lessons())
        txt.config(state="disabled")

    # ══════════════════════════════════════
    # CODE CALLBACKS
    # ══════════════════════════════════════
    def _record_tokens(self, tokens_in, tokens_out, model=""):
        self._last_tokens_in = tokens_in
        self._last_tokens_out = tokens_out
        self._last_model_used = model or getattr(self.ai, "model", "")
        self._session_tokens_in += tokens_in
        self._session_tokens_out += tokens_out
        self._session_queries += 1

    def _on_halt(self):
        if hasattr(self, 'smart_loop'):
            self.smart_loop.halt_requested = True
            self.log("🛑 HALT requested")
        if hasattr(self, 'code_window'):
            try:
                self.code_window._stop_execution()
            except:
                pass
        self.root.after(0, lambda: self._draw_halt_btn(False))
        self.root.after(0, lambda: self.exec_status.config(text="HALTED", fg=AMBER))

    def _on_goof(self, error_output):
        # Extract just the error type from the traceback
        import re
        error_match = re.search(r'(\w+Error|\w+Exception):\s*(.+)', error_output)
        if error_match:
            error_type = error_match.group(1)
            error_msg = error_match.group(2)[:60]
            query = f"python {error_type} {error_msg} fix"
        else:
            query = self.ai.internet._extract_search_query(error_output) + " python fix"

        self.log(f"[GOOF] Searching: {query}")
        results = self.ai.internet._brave_search(query, count=3)
        if results and hasattr(self, 'smart_loop'):
            self.smart_loop.extra_context = results
            self.log("[GOOF] ✅ Fix context injected")

    def _decay_affect(self):
        """Apply emotional decay periodically."""
        if hasattr(self, 'affect'):
            self.affect.decay()
        # Schedule next decay (runs every minute)
        self.root.after(60000, self._decay_affect)

    def _on_sandbox_output(self, output):
        """Handle output from sandbox"""
        self.log(f"[sandbox] Output received: {output[:100]}")

        # Add to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": output,
            "timestamp": datetime.now().strftime('%H:%M')
        })

        # Show in Tkinter
        self._append_conv("assistant", output)


    def _review_mistake(self, task, error_type, code, output):
        task_type = self.smart_loop.mistake_memory.classify_task(task)
        libraries = self.smart_loop.mistake_memory.extract_libraries(code + " " + output)
        auto_lesson = self.smart_loop.mistake_memory._generate_lesson(
            task_type, error_type, libraries, output)
        popup = tk.Toplevel(self.root)
        popup.title("Review Lesson");
        popup.geometry("700x400")
        popup.configure(bg=BG_LEFT);
        popup.grab_set()
        tk.Label(popup, text=f"Task: {task_type}  |  Error: {error_type}",
                 font=F_RAJ_BIG, bg=BG_LEFT, fg=ELECTRIC_BLUE).pack(pady=5)
        txt = tk.Text(popup, height=8, wrap="word", font=F_COURIER,
                      bg=BG_INPUT, fg=FG_MAIN, insertbackground=ELECTRIC_BLUE)
        txt.insert("1.0", auto_lesson);
        txt.pack(fill="both", expand=True, padx=10, pady=5)
        bf = tk.Frame(popup, bg=BG_LEFT);
        bf.pack(pady=10)

        def save():
            lesson = txt.get("1.0", "end").strip()
            if lesson:
                self.smart_loop.mistake_memory.save_mistake(
                    task=task, error_type=error_type,
                    failed_code=code, error_output=output, lesson=lesson)
                self.log("[LESSON] ✅ Saved")
            popup.destroy()

        def discard():
            self.log("[LESSON] ❌ Discarded");
            popup.destroy()

        tk.Button(bf, text="✅ Save", command=save, bg="#27ae60", fg=WHITE, width=12).pack(side="left", padx=5)
        tk.Button(bf, text="❌ Discard", command=discard, bg="#e74c3c", fg=WHITE, width=12).pack(side="left", padx=5)

    # ══════════════════════════════════════
    # AUDIO
    # ══════════════════════════════════════

    def _on_token_limit_hit(self):
        self.log(f"⚠️ TOKEN LIMIT HIT")
        self._append_conv("system", "⚠️ Response was cut off — max tokens reached.")
        threading.Thread(target=lambda: [self._play_chime(440, 120, 0.3) or time.sleep(0.2)] * 3,
                         daemon=True).start()

    def _on_send(self):
        user_input = self._get_input()
        if not user_input or getattr(self, '_thinking', False):
            return
        self._thinking = True
        self._draw_send_btn(False)
        self._start_nova_flash()
        # Clear input
        self.input_text.delete("1.0", "end")
        self._set_placeholder()
        # Show user message
        self._append_conv("user", user_input)
        self.conversation_history.append({"role": "user", "content": user_input})
        self.ctx_label.config(text=f"CTX: {len(self.conversation_history) // 2} exchange(s)", fg=GREEN_GLOW)
        threading.Thread(target=self._process_input, args=(user_input,), daemon=True).start()

    def _on_clear(self):
        self.input_text.delete("1.0", "end")
        self._set_placeholder()

    def save_state(self):
        try:
            path = os.path.abspath("nova_state.json")
            # Preserve the memory block if NovaMemory manages it
            if hasattr(self, 'memory') and "memory" in self.memory.state:
                self.state["memory"] = self.memory.state["memory"]
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
            self.log(f"[STATE] ✅ Saved → {path}")
        except Exception as e:
            self.log(f"[STATE ERROR] ❌ {e}")

    def load_state(self):
        path = os.path.abspath("nova_state.json")
        print(f"[DEBUG] Looking for file at: {path}")
        print(f"[DEBUG] File exists: {os.path.exists(path)}")
        self.log(f"[DEBUG] Looking for file at: {path}")
        self.log(f"[DEBUG] File exists: {os.path.exists(path)}")

        # CRITICAL: Initialize self.state FIRST with default values
        self.state = {
            "last_result": None,
            "last_task": None,
            "last_type": None,
            "history": [],
            "lessons": []
        }

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content.strip():
                        loaded_state = json.loads(content)
                        if isinstance(loaded_state, dict):
                            self.state.update(loaded_state)
                        else:
                            print(f"[STATE] ⚠️ Loaded data is not a dictionary")
                    else:
                        print(f"[STATE] ⚠️ File is empty")

                # Ensure required fields exist
                if "history" not in self.state:
                    self.state["history"] = []
                if "lessons" not in self.state:
                    self.state["lessons"] = []

                history_count = len(self.state.get('history', []))
                print(f"[STATE] ✅ Loaded {history_count} exchanges")
                self.log(f"[STATE] ✅ Loaded {history_count} exchanges")

                # Safely print last task (only if self.state is not None)
                if self.state is not None:
                    last_task = self.state.get('last_task', 'None')
                    if last_task is not None:
                        print(
                            f"[STATE] Last task: {last_task[:50] if isinstance(last_task, str) else str(last_task)[:50]}")
                        self.log(
                            f"[STATE] Last task: {last_task[:50] if isinstance(last_task, str) else str(last_task)[:50]}")
                else:
                    print(f"[STATE] State is None after load")

                # Rebuild conversation_history from saved state
                self.conversation_history = []
                for entry in self.state.get("history", []):
                    if isinstance(entry, dict):
                        self.conversation_history.append({
                            "role": "user",
                            "content": entry.get("task", ""),
                            "timestamp": entry.get("timestamp", "")
                        })
                        self.conversation_history.append({
                            "role": "assistant",
                            "content": entry.get("result", ""),
                            "timestamp": entry.get("timestamp", "")
                        })

                print(f"[STATE] ✅ Rebuilt {len(self.conversation_history)} messages")
                self.log(f"[STATE] ✅ Rebuilt {len(self.conversation_history)} messages")
                return

            except json.JSONDecodeError as e:
                print(f"[STATE] JSON decode error: {e}")
                self.log(f"[STATE] JSON decode error: {e}")
            except Exception as e:
                print(f"[STATE] Error loading: {e}")
                self.log(f"[STATE] Error loading: {e}")
                import traceback
                traceback.print_exc()

        # Create fresh state if we couldn't load
        print("[STATE] Starting fresh - no valid state file found")
        self.log("[STATE] Starting fresh - no valid state file found")
        self.state = {
            "last_result": None,
            "last_task": None,
            "last_type": None,
            "history": [],
            "lessons": []
        }
        self.conversation_history = []
        self.save_state()



    def _deliver_tool_result(self, tool_result):
        from datetime import datetime
        self.state["last_result"] = tool_result
        self.state["last_task"] = "tool"
        self.state["last_type"] = "tool"

        if isinstance(tool_result, str) and tool_result.startswith("DIAGRAM:"):
            path = tool_result.split(":", 1)[1].strip()
            self.root.after(0, lambda p=path: self.show_graphviz_diagram(p))
            # The diagram will add its own web-friendly entry to conversation_history
            # via the store=True parameter in show_graphviz_diagram
            return

        elif isinstance(tool_result, str) and tool_result.startswith("[DIAGRAM:"):
            # Already in web format, just add to conversation
            self.conversation_history.append({
                "role": "assistant",
                "content": tool_result,
                "timestamp": datetime.now().strftime('%H:%M')
            })
            return

        elif isinstance(tool_result, str) and tool_result.startswith("[IMAGE:"):
            # Already in web format
            self.conversation_history.append({
                "role": "assistant",
                "content": tool_result,
                "timestamp": datetime.now().strftime('%H:%M')
            })
            return

        elif isinstance(tool_result, str) and tool_result.startswith("IMAGE_GRID:"):
            # Handle old format (convert to new format)
            grid_path = tool_result.split(":", 1)[1]
            import os
            import shutil
            from datetime import datetime

            web_dir = "web_images"
            os.makedirs(web_dir, exist_ok=True)

            if os.path.exists(grid_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                web_filename = f"image_grid_{timestamp}.jpg"
                web_path = os.path.join(web_dir, web_filename)
                shutil.copy2(grid_path, web_path)

                self.conversation_history.append({
                    "role": "assistant",
                    "content": f"[IMAGE:{web_filename}]",
                    "timestamp": datetime.now().strftime('%H:%M')
                })

                # Also display in Tkinter
                self.root.after(0, lambda p=grid_path: self.show_graphviz_diagram(p))
                return

        else:
            # Normal text response
            self._append_conv("assistant", tool_result)
            self.conversation_history.append({
                "role": "assistant",
                "content": tool_result,
                "timestamp": datetime.now().strftime('%H:%M')
            })



    def _save_response_as_html(self, content, save_btn=None):
        import datetime as dt
        import re as re2
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        first_line = content.strip().split("\n")[0][:40]
        safe_name = re2.sub(r'[^\w\s-]', '', first_line).strip().replace(' ', '_')
        filename = f"nova_output_{safe_name}_{timestamp}"
        os.makedirs("nova_outputs", exist_ok=True)

        md_path = os.path.join("nova_outputs", filename + ".md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(content)

        try:
            import markdown
            latex_store = {}
            counter = [0]

            def protect(m):
                key = f"LATEXTOKEN{counter[0]}ENDTOKEN"
                latex_store[key] = m.group(0)
                counter[0] += 1
                return key

            protected = re.sub(r'\$\$.*?\$\$|\$.*?\$', protect, content, flags=re.DOTALL)
            protected = re.sub(r'(?<!\()(?<!\[)(https?://[^\s\)\]]+)', r'[\1](\1)', protected)
            html_body = markdown.markdown(protected, extensions=["tables", "fenced_code"])
            for key, val in latex_store.items():
                html_body = html_body.replace(key, val)
        except ImportError:
            html_body = f"<pre>{content}</pre>"

        html = f"""<!DOCTYPE html>
    <html><head><meta charset="utf-8">
    <script>
    MathJax = {{
      tex: {{
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
      }}
    }};
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
    body {{ background:#0D0F14; color:#C8D6E5; font-family:Georgia,serif;
           max-width:900px; margin:40px auto; padding:20px; line-height:1.7; }}
    h1,h2,h3 {{ color:#4A9EFF; }}
    code {{ background:#1A1F2E; padding:2px 6px; border-radius:3px; color:#39FF14; }}
    pre {{ background:#1A1F2E; padding:16px; border-radius:6px; overflow-x:auto; }}
    table {{ border-collapse:collapse; width:100%; }}
    th,td {{ border:1px solid #2A4A7F; padding:8px 12px; }}
    th {{ background:#1A2035; color:#4A9EFF; }}
    a {{ color:#4A9EFF; }}
    </style></head><body>{html_body}</body></html>"""

        html_path = os.path.join("nova_outputs", filename + ".html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        os.startfile(os.path.abspath(html_path))
        self.log(f"[SAVE] Written → {md_path}")
        if save_btn:
            save_btn.config(fg=GREEN_GLOW)

    def _dot_generator(self):
        """Generator that cycles through dot patterns for animation"""
        patterns = ["", ".", "..", "..."]
        while True:
            for pattern in patterns:
                yield pattern

    def _ask_code_permission(self, task, internet_ctx=""):
        """Show a dialog asking if user wants code written."""
        popup = tk.Toplevel(self.root)
        popup.title("Write a program?")
        popup.geometry("500x200")
        popup.configure(bg=BG_LEFT)
        popup.grab_set()

        # Center it
        popup.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 250
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 100
        popup.geometry(f"+{x}+{y}")

        tk.Label(popup, text="Run a Program?", font=F_RAJ_BIG,
                 bg=BG_LEFT, fg=ELECTRIC_BLUE).pack(pady=15)
        tk.Label(popup,
                 text=f"Task: {task[:80]}{'...' if len(task) > 80 else ''}",
                 font=F_RAJ_SM, bg=BG_LEFT, fg=DIM_TEXT, wraplength=460).pack()

        bf = tk.Frame(popup, bg=BG_LEFT);
        bf.pack(pady=20)

        def _yes():
            popup.destroy()
            self._append_conv("system", "Writing program...")
            threading.Thread(target=self._run_autocoder, args=(task, internet_ctx), daemon=True).start()

        def _no():
            popup.destroy()
            self._append_conv("assistant", "No problem — let me know if you need anything else.")
            self.speak_text("No problem, let me know if you need anything else.")

        tk.Button(bf, text="✅ Yes, write it", command=_yes,
                  bg="#27ae60", fg=WHITE, width=16,
                  font=F_RAJ_BTN).pack(side="left", padx=10)
        tk.Button(bf, text="❌ No thanks", command=_no,
                  bg="#e74c3c", fg=WHITE, width=14,
                  font=F_RAJ_BTN).pack(side="left", padx=10)

    def _run_autocoder(self, task, internet_ctx=""):
        """Run the full AutoCoder pipeline."""
        # Reset halt flag from any previous run
        if hasattr(self, 'smart_loop'):
            self.smart_loop.halt_requested = False
        if hasattr(self, 'code_window'):
            self.code_window.halt_code_generation = False

        # Show the code window as soon as autocoder starts
        self.root.after(0, self.code_window.show)

        self.root.after(0, lambda: self._draw_halt_btn(True))
        self.root.after(0, lambda: self.exec_status.config(text="RUNNING", fg=GREEN_GLOW))

        enhanced_task = task
        if internet_ctx:
            enhanced_task += f"\n\n{internet_ctx}"

        self.smart_loop.response_callback = lambda msg: self._append_conv("system", msg)
        self.smart_loop.review_callback = self._review_mistake

        success, result, attempts, metadata = self.smart_loop.run_with_loop_detection(enhanced_task)

        if metadata.get("halted_by_user"):
            self._append_conv("system", f"Halted after {attempts} attempt(s).")
        elif result:
            code_result = self.clean_code_for_execution(result)

            def _show():
                self.code_window.set_code(code_result)
                self.code_window.show()
                # Explicitly mirror to the preview panel
                try:
                    self.code_display.config(state="normal")
                    self.code_display.delete("1.0", tk.END)
                    self.code_display.insert("1.0", code_result)
                    self.code_display.see("1.0")
                    self.code_display.config(state="disabled")
                except Exception:
                    pass

            self.root.after(0, _show)

            status = "✅ SUCCESS" if success else "❌ FAILED"
            self.log(f"{'=' * 50}\n{status} (attempts: {attempts})\n{'=' * 50}")

            # Check for saved plots and add them to web interface
            if success:
                import glob
                import os
                import time

                # Give a moment for files to be written
                time.sleep(0.5)

                # Look for plot images in web_images folder
                latest_plots = glob.glob("web_images/plot_*.png")
                if latest_plots:
                    # Get the most recent plot
                    latest = max(latest_plots, key=os.path.getctime)
                    filename = os.path.basename(latest)

                    # Add to conversation history for web
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": f"[IMAGE:{filename}]",
                        "timestamp": datetime.now().strftime('%H:%M')
                    })
                    self.log(f"[AUTOCODER] Plot saved: {filename}")

            # Plain English explanation
            ep = f"""You are Nova. You just successfully wrote and ran a Python program.
            The task was: {task}
            The program ran successfully after {attempts} attempt(s).
            In 2 sentences, tell the user what the program does and that it is now running or has completed.
            Be conversational, no technical details. Do NOT say you haven't written anything."""
            explanation = self.ai.generate(ep) or f"Program completed in {attempts} attempt(s)."

            self._append_conv("assistant", explanation)
            self.speak_text(explanation)
        else:
            msg = f"Could not generate working code after {attempts} attempts. Try rephrasing."
            self._append_conv("assistant", msg)
            self.speak_text(msg)

        self.root.after(0, lambda: self._draw_halt_btn(False))
        done_text = "✅ DONE" if (result and success) else "❌ FAILED"
        done_col = GREEN_GLOW if (result and success) else RED_GLOW
        self.root.after(0, lambda: self.exec_status.config(text=done_text, fg=done_col))

    def clean_code_for_execution(self, text: str) -> str:
        if not text:
            return ""

        import re

        # Extract ANY code block (``` or ```python)
        matches = re.findall(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)
        if matches:
            code = "\n\n".join(m.strip() for m in matches)
        else:
            code = re.sub(r"```+", "", text).strip()

        # ── Strip smart/curly quotes the LLM loves to inject ──────────────
        replacements = {
            "\u201C": '"', "\u201D": '"',
            "\u2018": "'", "\u2019": "'",
            "\u2014": "-", "\u2013": "-",
            "\u2212": "-",  # ← Unicode minus sign → hyphen
            "\u2026": "...", "\u00d7": "*",
            "\u00f7": "/", "\u2192": "->",
        }
        for bad, good in replacements.items():
            code = code.replace(bad, good)

        return code

    def _draw_evolve_btn(self, hover=False):
        c = self.evolve_btn
        c.delete("all")
        brd = "#FF00FF" if hover else "#2A3A5A"
        fg = "#FF88FF" if hover else "#9B59B6"
        c.create_rectangle(1, 1, 69, 25, fill="#1A1F2E", outline=brd)
        c.create_text(35, 13, text="EVOLVE", font=F_RAJ_SM, fill=fg)
        if hover:
            self._show_evolve_tooltip()
        else:
            self._hide_evolve_tooltip()

    def _draw_debug_btn(self, hover=False):
        c = self.debug_btn
        c.delete("all")
        brd = RED_GLOW if hover else "#2A3A5A"
        fg = "#FF8888" if hover else "#8A4A4A"
        c.create_rectangle(1, 1, 59, 25, fill="#1A1F2E", outline=brd)
        c.create_text(30, 13, text="DEBUG", font=F_RAJ_SM, fill=fg)

    def _draw_search_bar(self, active=False):
        c = self.inet_canvas
        c.delete("all")
        w = c.winfo_width() or 70
        h = c.winfo_height() or 10

        if not active:
            # Dim inactive bar
            c.create_rectangle(0, 0, w, h, fill="#1A1F2E", outline="#2A3A5A")
            return

        # Colour stops for the animated gradient bar
        colours = [
            "#FF0080", "#FF4500", "#FFD700",
            "#00FF88", "#00BFFF", "#9B59B6", "#FF0080"
        ]

        phase = self._search_bar_phase
        total = len(colours) - 1
        segment_w = w / total

        for i in range(total):
            # Shift hue by phase
            ci = (i + phase) % total
            c1 = colours[ci]
            c2 = colours[(ci + 1) % total]

            x0 = int(i * segment_w)
            x1 = int((i + 1) * segment_w)

            # Simple two-colour fill per segment (no per-pixel gradient for speed)
            mid = (x0 + x1) // 2
            c.create_rectangle(x0, 0, mid, h, fill=c1, outline="")
            c.create_rectangle(mid, 0, x1, h, fill=c2, outline="")

        # Flash overlay — bright white pulse
        if self._search_bar_flash:
            alpha_fill = "#FFFFFF"
            c.create_rectangle(0, 0, w, h, fill=alpha_fill, outline="", stipple="gray50")

    def _animate_search_bar(self):
        if not getattr(self, "_internet_active", False):
            self._draw_search_bar(False)
            return

        # Advance colour phase
        self._search_bar_phase = (self._search_bar_phase + 1) % 6

        # Toggle flash every 3 frames
        frame = getattr(self, "_search_bar_frame", 0)
        self._search_bar_frame = frame + 1
        self._search_bar_flash = (frame % 6) < 2

        self._draw_search_bar(True)
        self.root.after(80, self._animate_search_bar)

    def _start_nova_flash(self):
        if self._nova_flash_running:
            return
        self._nova_flash_running = True
        self._nova_flash_state = True
        self._animate_nova_flash()

    def _stop_nova_flash(self):
        self._nova_flash_running = False
        # Restore all letters to normal colour
        for lbl in self._nova_labels:
            lbl.config(fg=ELECTRIC_BLUE)

    def _animate_nova_flash(self):
        if not self._nova_flash_running:
            return
        self._nova_flash_state = not self._nova_flash_state
        colour = ELECTRIC_BLUE if self._nova_flash_state else BG_LEFT
        for lbl in self._nova_labels:
            lbl.config(fg=colour)
        self.root.after(400, self._animate_nova_flash)

    def update_character_count(self, _=None):
        text = self.input_text.get("1.0", "end-1c")
        if self._placeholder_active:
            text = ""
        self.char_counter_lbl.config(text=f"{len(text)} characters")

    def _show_evolve_tooltip(self):
        if hasattr(self, '_evolve_tooltip') and self._evolve_tooltip and self._evolve_tooltip.winfo_exists():
            return
        try:
            x = self.evolve_btn.winfo_rootx()
            y = self.evolve_btn.winfo_rooty() - 60
            tip = tk.Toplevel(self.root)
            tip.overrideredirect(True)
            tip.attributes("-topmost", True)
            tip.geometry(f"+{x}+{y}")
            tip.configure(bg="#2D1B4E")
            outer = tk.Frame(tip, bg="#FF00FF", padx=1, pady=1)
            outer.pack()
            inner = tk.Frame(outer, bg="#2D1B4E", padx=8, pady=6)
            inner.pack()
            tk.Label(
                inner,
                text="🧬 Evolve Nova's own source code.\nAdd a feature or fix a weakness\nusing AI self-improvement.",
                font=F_RAJ_SM,
                bg="#2D1B4E",
                fg="#FF88FF",
                justify="left"
            ).pack()
            self._evolve_tooltip = tip
        except Exception:
            self._evolve_tooltip = None

    def _hide_evolve_tooltip(self):
        if hasattr(self, '_evolve_tooltip') and self._evolve_tooltip:
            try:
                self._evolve_tooltip.destroy()
            except Exception:
                pass
            self._evolve_tooltip = None

    def undock_system_log(self, target_widget=None):
        if self._syslog_detached:
            self._dock_syslog()
        else:
            self._detach_syslog()

    def _toggle_detach_syslog(self):
        if self._syslog_detached:
            self._dock_syslog()
        else:
            self._detach_syslog()

    def _detach_syslog(self):
        if self._syslog_detached:
            return

        # Hide the embedded log widget
        self.debug_text.pack_forget()

        top = tk.Toplevel(self.root)
        top.title("Nova — System Log")
        top.geometry("860x400+200+600")
        top.configure(bg=BG_ROOT)
        top.protocol("WM_DELETE_WINDOW", self._dock_syslog)
        self._syslog_toplevel = top

        self._syslog_detached = True
        self._create_detached_syslog(top)

        self._syslog_detach_btn.config(text="⬛ Dock", fg=GREEN_GLOW)
        self.log("[SYSLOG] Detached to separate window")

    def _create_detached_syslog(self, parent):
        outer = tk.Frame(parent, bg=SEAM, padx=1, pady=1)
        outer.pack(fill="both", expand=True, padx=10, pady=4)

        sec = tk.Frame(outer, bg=BG_LEFT)
        sec.pack(fill="both", expand=True)

        hdr = tk.Frame(sec, bg=BG_LEFT)
        hdr.pack(fill="x")

        tk.Label(hdr, text="SYSTEM LOG (DETACHED)", font=F_RAJ_SM,
                 bg=BG_LEFT, fg=ELECTRIC_BLUE).pack(side="left", padx=6, pady=(4, 0))

        dock_btn = tk.Label(hdr, text="⬛ Dock", font=F_RAJ_SM,
                            bg="#1A1F2E", fg=GREEN_GLOW, padx=4, pady=2,
                            cursor="hand2")
        dock_btn.pack(side="right", padx=2, pady=2)
        dock_btn.bind("<Button-1>", lambda e: self._dock_syslog())

        log_text = scrolledtext.ScrolledText(
            sec, bg=BG_CONSOLE, fg=TERMINAL_GREEN,
            font=F_COURIER, relief="flat", wrap="word", state="disabled")
        log_text.pack(fill="both", expand=True, padx=4, pady=4)

        try:
            existing = self.debug_text.get("1.0", "end")
            log_text.config(state="normal")
            log_text.insert("1.0", existing)
            log_text.config(state="disabled")
            log_text.see("end")
        except Exception:
            pass

        self._detached_log_text = log_text

    def _dock_syslog(self):
        if not self._syslog_detached:
            return

        if self._syslog_toplevel:
            self._syslog_toplevel.destroy()
            self._syslog_toplevel = None

        if hasattr(self, '_detached_log_text'):
            delattr(self, '_detached_log_text')

        # Restore the embedded log widget
        self.debug_text.pack(fill="both", expand=True)

        self._syslog_detached = False
        self._syslog_expanded = False

        try:
            self._syslog_detach_btn.config(text="⧉ Detach", fg=ELECTRIC_BLUE)
        except Exception:
            pass
        try:
            self._syslog_expand_btn.config(text="⛶", fg=AMBER)
        except Exception:
            pass

        self.log("[SYSLOG] Docked back into main window")

    def _expand_syslog(self):
        if not self._syslog_detached or not self._syslog_toplevel:
            self._detach_syslog()
            self.root.after(100, self._expand_syslog)
            return

        top = self._syslog_toplevel
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        if self._syslog_expanded:
            top.geometry("860x400+200+600")
            self._syslog_expanded = False
            self._syslog_expand_btn.config(text="⛶", fg=AMBER)
            self.log("[SYSLOG] Restored to normal size")
        else:
            w = int(sw * 0.80)
            h = int(sh * 0.85)
            x = (sw - w) // 2
            y = (sh - h) // 2
            top.geometry(f"{w}x{h}+{x}+{y}")
            self._syslog_expanded = True
            self._syslog_expand_btn.config(text="⊡", fg=GREEN_GLOW)
            self.log("[SYSLOG] Expanded to large view")

    def _build_resize_handle(self):
        """Add a draggable resize grip to the bottom-right corner of the window."""
        self._resize_handle = tk.Canvas(
            self.root,
            width=18, height=18,
            bg=BG_ROOT,
            highlightthickness=0,
            cursor="size_nw_se"
        )
        self._resize_handle.place(relx=1.0, rely=1.0, anchor="se")
        self._draw_resize_grip()

        # Drag state
        self._resize_dragging = False
        self._resize_start_x = 0
        self._resize_start_y = 0
        self._resize_start_w = 0
        self._resize_start_h = 0

        self._resize_handle.bind("<ButtonPress-1>", self._on_mouse_press)
        self._resize_handle.bind("<B1-Motion>", self._on_mouse_move)
        self._resize_handle.bind("<ButtonRelease-1>", self._on_mouse_release)
        self._resize_handle.bind("<Enter>", self._on_resize_enter)
        self._resize_handle.bind("<Leave>", self._on_resize_leave)

    def _draw_resize_grip(self, hover=False):
        """Draw the three-line diagonal grip icon inside the resize handle canvas."""
        c = self._resize_handle
        c.delete("all")
        col = ELECTRIC_BLUE if hover else DIM_TEXT
        for i, (x1, y1, x2, y2) in enumerate([
            (10, 2, 16, 8),
            (6, 6, 16, 16),
            (2, 10, 16, 16),
        ]):
            width = 2 if i == 2 else 1
            c.create_line(x1, y1, x2, y2, fill=col, width=width, capstyle="round")

    def _resize_start(self, event):
        """Record window geometry at the moment the resize drag begins."""
        self._on_mouse_press(event)

    def _resize_motion(self, event):
        """Resize the window as the grip is dragged."""
        self._on_mouse_move(event)

    def _resize_end(self, event):
        """Finalise the resize and restore the grip to its idle appearance."""
        self._on_mouse_release(event)

    def _on_mouse_press(self, event):
        """Record window geometry and cursor position when resize drag begins."""
        self._resize_dragging = True
        self._resize_start_x = event.x_root
        self._resize_start_y = event.y_root
        self._resize_start_w = self.root.winfo_width()
        self._resize_start_h = self.root.winfo_height()
        self._draw_resize_grip(hover=True)

    def _on_mouse_move(self, event):
        """Resize the window while the grip is being dragged."""
        if not self._resize_dragging:
            return
        dx = event.x_root - self._resize_start_x
        dy = event.y_root - self._resize_start_y
        new_w = max(800, self._resize_start_w + dx)
        new_h = max(500, self._resize_start_h + dy)
        self.resize_panel(new_w, new_h)

    def _on_mouse_release(self, event):
        """Finalise the resize and restore the grip to its idle appearance."""
        self._resize_dragging = False
        self._draw_resize_grip(hover=False)

    def resize_panel(self, width, height):
        """Resize the main UI panel to the given width and height, clamped within min/max bounds."""
        MIN_W = 800
        MIN_H = 500
        MAX_W = self.root.winfo_screenwidth()
        MAX_H = self.root.winfo_screenheight()
        new_w = max(MIN_W, min(MAX_W, int(width)))
        new_h = max(MIN_H, min(MAX_H, int(height)))
        self.root.geometry(f"{new_w}x{new_h}")
        self.root.update_idletasks()
        #self.log(f"[UI] Panel resized to {new_w}x{new_h}")

    def _on_resize_enter(self, event=None):
        """Show resize cursor and highlight grip when mouse enters the handle."""
        self._resize_handle.config(cursor="size_nw_se")
        self._draw_resize_grip(hover=True)

    def _on_resize_leave(self, event=None):
        """Restore default cursor and dim grip when mouse leaves the handle."""
        if not self._resize_dragging:
            self._resize_handle.config(cursor="")
            self._draw_resize_grip(hover=False)

    def run(self):
        self.root.mainloop()


# ──────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("Nova Assistant — Starting...")
    print("=" * 60)
    import sys

    load_dotenv()
    validate_environment()

    if not check_ollama_running():
        print("[Ollama] Starting in background...")
        start_ollama()
    else:
        print("[Ollama] ✓ Already running")

    app = NovaAssistant()

    app.run()
    print("[Nova] Session ended.")