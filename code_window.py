# code_window.py - WITH AUTO-INSTALL MISSING LIBRARIES
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import subprocess
import tempfile
import os
import sys
import re
import threading
import queue
import time
import importlib
import importlib.util
import shutil
import glob
from code_display import CodeDisplay


class CodeWindow(tk.Toplevel):
    """Popup window for code execution with run button"""

    # Map of common package names to pip names (some differ)
    PACKAGE_NAME_MAP = {
        'cv2': 'opencv-python',
        'PIL': 'pillow',
        'sklearn': 'scikit-learn',
        'yaml': 'pyyaml',
        'bs4': 'beautifulsoup4',

        # Windows-specific packages (all part of pywin32)
        'win32com': 'pywin32',
        'win32api': 'pywin32',
        'win32gui': 'pywin32',
        'win32con': 'pywin32',
        'win32event': 'pywin32',
        'win32file': 'pywin32',
        'win32process': 'pywin32',
        'win32security': 'pywin32',
        'win32service': 'pywin32',
        'pywintypes': 'pywin32',

        'dateutil': 'python-dateutil',
        'dotenv': 'python-dotenv',
        'magic': 'python-magic-bin',
        'Image': 'pillow',
        'beep': 'python-beep',
        'ffmpeg': 'ffmpeg-python',
        'OpenGL': 'pyopengl',

        # Matplotlib submodules
        'mpl_toolkits': 'matplotlib',
        'mpl_toolkits.mplot3d': 'matplotlib',
        'mpl_toolkits.axes_grid1': 'matplotlib',
        'mpl_toolkits.axes_grid': 'matplotlib',
        'mpl_toolkits.basemap': 'basemap',
        'pyplot': 'matplotlib',

        'webview': 'pywebview',

        # SciPy functions/submodules
        'quad': 'scipy',
        'odeint': 'scipy',
        'fft': 'scipy',
        'signal': 'scipy',
        'integrate': 'scipy',
        'optimize': 'scipy',
        'linalg': 'scipy',
        'sparse': 'scipy',
        'stats': 'scipy',
        'spatial': 'scipy',
        'interpolate': 'scipy',
        'bode': 'control',

        # NumPy submodules
        'ndarray': 'numpy',
        'np': 'numpy',

        # Pandas submodules
        'DataFrame': 'pandas',
        'Series': 'pandas',

        # Audio - NOT packages
        'simpleaudio': None,

        # Standard library (don't install)
        'os': None,
        'sys': None,
        'json': None,
        'csv': None,
        'pathlib': None,
        'time': None,
        'datetime': None,
        'math': None,
        're': None,
        'random': None,
        'collections': None,
        'itertools': None,
        'functools': None,
        'subprocess': None,
        'threading': None,
        'multiprocessing': None,
        'pickle': None,
        'copy': None,
        'typing': None,
    }

    def __init__(self, master, log_callback=None, output_callback=None, stop_callback=None, main_app=None):
        super().__init__(master)
        self.goof_callback = None
        self.from_smart_loop = False
        self.title("Code Sandbox")
        self.geometry("850x650")
        self.protocol("WM_DELETE_WINDOW", self.hide)

        self.log_callback = log_callback or print
        self.output_callback = output_callback
        self.stop_callback = stop_callback
        self.main_app = main_app

        self.configure(bg="#0C1219")

        self.auto_send_var = tk.BooleanVar(value=True)

        self.sandbox_python = self._setup_sandbox_venv()

        self._create_ui()

        self.current_code = ""
        self.last_plot_path = None
        self.last_plot_filename = None
        self._last_output = ""
        self._last_had_error = False
        self._code_saved = False

        self.process = None
        self.execution_stopped = False
        self.halt_code_generation = False
        self.execution_complete = threading.Event()
        self.execution_lock = threading.Lock()

        self.log("[sandbox] Code window initialized")

    def _setup_sandbox_venv(self):
        """Create or reuse a single persistent sandbox venv"""
        try:
            project_dir = os.path.dirname(os.path.abspath(__file__))
        except:
            project_dir = os.getcwd()

        sandbox_venv_path = os.path.join(project_dir, '.venv_sandbox')

        if sys.platform == 'win32':
            python_exe = os.path.join(sandbox_venv_path, 'Scripts', 'python.exe')
        else:
            python_exe = os.path.join(sandbox_venv_path, 'bin', 'python')

        if os.path.exists(python_exe):
            self.log(f"[sandbox] ✅ Reusing existing sandbox venv")
            return python_exe

        self.log(f"[sandbox] 🔧 Creating sandbox venv at: {sandbox_venv_path}")
        try:
            if os.path.exists(sandbox_venv_path):
                shutil.rmtree(sandbox_venv_path, ignore_errors=True)

            result = subprocess.run(
                [sys.executable, '-m', 'venv', sandbox_venv_path],
                capture_output=True, text=True, timeout=120
            )

            if result.returncode == 0 and os.path.exists(python_exe):
                self.log(f"[sandbox] ✅ Sandbox venv created")
                return python_exe
            else:
                self.log(f"[sandbox] ⚠️ Venv creation failed, using system python")
                return sys.executable

        except Exception as e:
            self.log(f"[sandbox] ⚠️ Error: {e}, using system python")
            return sys.executable

    def _create_ui(self):
        self.top_bar = tk.Frame(self, bg="#0A0C10")
        self.top_bar.pack(fill="x")

        tk.Label(self.top_bar, text="CODE SANDBOX", font=("Rajdhani", 11, "bold"),
                 bg="#0A0C10", fg="#4A9EFF").pack(side="left", padx=10, pady=4)

        self.run_btn = tk.Button(self.top_bar, text="▶ RUN", command=self._run_code_safe,
                                 bg="#1A4A2E", fg="#39FF14", font=("Rajdhani", 10, "bold"),
                                 relief="flat", padx=8)
        self.run_btn.pack(side="left", padx=4, pady=3)

        self.stop_btn = tk.Button(self.top_bar, text="⏹ STOP", command=self._stop_execution,
                                  bg="#3A1515", fg="#FF4444", font=("Rajdhani", 10, "bold"),
                                  relief="flat", padx=8)
        self.stop_btn.pack(side="left", padx=4, pady=3)

        self.halt_btn = tk.Button(self.top_bar, text="🛑 HALT GEN", command=self._halt_code_generation,
                                  bg="#2D1B4E", fg="#9B59B6", font=("Rajdhani", 10, "bold"),
                                  relief="flat", padx=8)
        self.halt_btn.pack(side="left", padx=4, pady=3)

        self.copy_btn = tk.Button(self.top_bar, text="📋 COPY", command=self._copy_code,
                                  bg="#1A2035", fg="#C8D6E5", font=("Rajdhani", 10, "bold"),
                                  relief="flat", padx=8)
        self.copy_btn.pack(side="left", padx=4, pady=3)

        self.clear_code_btn = tk.Button(self.top_bar, text="🗑 CLEAR", command=self._clear_code,
                                        bg="#1A2035", fg="#6B7A99", font=("Rajdhani", 10, "bold"),
                                        relief="flat", padx=8)
        self.clear_code_btn.pack(side="left", padx=4, pady=3)

        self.goof_btn = tk.Button(self.top_bar, text="🔍 GOOF", command=self.on_goof_button,
                                  bg="#1A2035", fg="#F39C12", font=("Rajdhani", 10, "bold"),
                                  relief="flat", padx=8)
        self.goof_btn.pack(side="left", padx=4, pady=3)

        self.status_label = tk.Label(self.top_bar, text="IDLE", font=("Rajdhani", 10),
                                     bg="#0A0C10", fg="#6B7A99")
        self.status_label.pack(side="right", padx=10)

        # Paned layout: code top, output bottom
        paned = tk.PanedWindow(self, orient="vertical", bg="#1E3A5F",
                               sashwidth=4, sashrelief="flat")
        paned.pack(fill="both", expand=True)

        # Code area using CodeDisplay
        code_frame = tk.Frame(paned, bg="#0F1318")
        paned.add(code_frame, minsize=150)

        self.code_display = CodeDisplay(code_frame, bg_color="#0F1318")
        self.code_display.set_editable(True)
        self.code_display.pack(fill="both", expand=True)

        # Output area
        output_frame = tk.Frame(paned, bg="#080C12")
        paned.add(output_frame, minsize=100)

        tk.Label(output_frame, text="OUTPUT", font=("Rajdhani", 9),
                 bg="#080C12", fg="#3A5A8A").pack(anchor="w", padx=6, pady=(2, 0))

        out_inner = tk.Frame(output_frame, bg="#080C12")
        out_inner.pack(fill="both", expand=True)

        self.output_text = tk.Text(out_inner, bg="#080C12", fg="#39FF14",
                                   font=("Courier New", 10), relief="flat",
                                   wrap="word", state="disabled",
                                   borderwidth=0, padx=4, pady=4)
        out_scroll = tk.Scrollbar(out_inner, orient="vertical",
                                  command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=out_scroll.set)
        out_scroll.pack(side="right", fill="y")
        self.output_text.pack(side="left", fill="both", expand=True)

        # Input line for interactive programs
        input_frame = tk.Frame(output_frame, bg="#080C12")
        input_frame.pack(fill="x", padx=4, pady=2)

        tk.Label(input_frame, text="›", font=("Courier New", 12, "bold"),
                 bg="#080C12", fg="#4A9EFF").pack(side="left")

        self.input_entry = tk.Entry(input_frame, bg="#141926", fg="#C8D6E5",
                                    font=("Courier New", 10), relief="flat",
                                    insertbackground="#4A9EFF")
        self.input_entry.pack(side="left", fill="x", expand=True, padx=4)
        self.input_entry.bind("<Return>", self._send_input_line)

        # Plot controls
        plot_frame = tk.Frame(self, bg="#0A0C10")
        plot_frame.pack(fill="x")

        self.save_plot_btn = tk.Button(plot_frame, text="💾 SAVE PLOT",
                                       command=self._save_plot,
                                       bg="#1A2035", fg="#4A9EFF",
                                       font=("Rajdhani", 10, "bold"),
                                       relief="flat", padx=8)
        self.save_plot_btn.pack(side="left", padx=4, pady=2)

        self.open_plot_btn = tk.Button(plot_frame, text="🖼 OPEN PLOT",
                                       command=self._open_plot,
                                       bg="#1A2035", fg="#4A9EFF",
                                       font=("Rajdhani", 10, "bold"),
                                       relief="flat", padx=8)
        self.open_plot_btn.pack(side="left", padx=4, pady=2)

        self.send_output_btn = tk.Button(plot_frame, text="📤 SEND TO AI",
                                         command=self._send_output_to_ai,
                                         bg="#1A2035", fg="#9B59B6",
                                         font=("Rajdhani", 10, "bold"),
                                         relief="flat", padx=8)
        self.send_output_btn.pack(side="left", padx=4, pady=2)

    def set_code(self, code: str, auto_run=False, from_smart_loop=False):
        """Set code in the editor and optionally run it"""
        # Strip markdown fences in case AI included them
        code = re.sub(r'^```python\s*\n?', '', code, flags=re.MULTILINE)
        code = re.sub(r'^```\s*$', '', code, flags=re.MULTILINE)
        code = code.strip()

        # Reset save flag here so _save_code_to_file works for new code
        self._code_saved = False

        self.from_smart_loop = from_smart_loop
        self.current_code = code
        self.code_display.set_editable(True)
        self.code_display.text.delete("1.0", tk.END)
        self.code_display.text.insert("1.0", self.current_code)
        self.code_display._apply_syntax_highlighting()
        self.code_display._update_line_numbers()
        self._clear_output()
        self.status_label.config(text="Code loaded", fg="#4A9EFF")
        self.log(f"[CODE] Code loaded ({len(code)} chars)")

        self._save_code_to_file(code)

        if auto_run:
            self.after(300, self._run_code_safe, from_smart_loop)

    def _save_code_to_file(self, code):
        """Save code to history folder - only if it's final/executed"""
        try:
            from datetime import datetime
            import hashlib
            import re

            # Only save if this is the final, cleaned code
            # Skip if code still has markdown markers (means it's not cleaned yet)
            if '```' in code or code.strip().startswith('```'):
                self.log(f"[CODE SAVE] Skipping - still has markdown markers")
                return

            # Skip if we already saved this code for this execution
            if hasattr(self, '_code_saved') and self._code_saved:
                self.log(f"[CODE SAVE] Skipping - already saved for this execution")
                return

            # Skip if code too short
            if len(code) < 50:
                self.log(f"[CODE SAVE] Skipping - code too short")
                return

            # Create a unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            task_hash = hashlib.md5(code[:100].encode()).hexdigest()[:8]
            filename = f"code_{timestamp}_{task_hash}.py"

            # Get the code history directory
            code_history_dir = "code_history"
            if hasattr(self, 'main_app') and self.main_app:
                code_history_dir = getattr(self.main_app, 'code_history_dir', "code_history")

            os.makedirs(code_history_dir, exist_ok=True)
            filepath = os.path.join(code_history_dir, filename)

            # Save the code
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# {'=' * 60}\n\n")
                f.write(code)

            self._code_saved = True
            self.log(f"[CODE SAVE] ✅ Saved final code to {filepath}")

        except Exception as e:
            self.log(f"[CODE SAVE ERROR] {e}")


    def _extract_imports(self, code: str) -> set:
        """Extract all import statements from code"""
        imports = set()
        import_pattern = r'^\s*import\s+([\w\., ]+)'
        from_pattern = r'^\s*from\s+([\w\.]+)\s+import'

        for line in code.split('\n'):
            if '#' in line:
                line = line[:line.index('#')]

            import_match = re.match(import_pattern, line)
            if import_match:
                modules = import_match.group(1).split(',')
                for module in modules:
                    base_module = module.strip().split()[0].split('.')[0]
                    if base_module:
                        mapped = self.PACKAGE_NAME_MAP.get(base_module, base_module)
                        imports.add(mapped)

            from_match = re.match(from_pattern, line)
            if from_match:
                module = from_match.group(1).split('.')[0]
                if module:
                    mapped = self.PACKAGE_NAME_MAP.get(module, module)
                    imports.add(mapped)

        return imports

    def on_goof_button(self):
        """Search web for fix to current error and inject into next attempt"""
        if not self._last_had_error or not self._last_output:
            self.status_label.config(text="No error to search for", fg="#F39C12")
            self.log("[GOOF] No error - nothing to search")
            return

        if self.goof_callback:
            self.log("[GOOF] 🔍 Requesting web search for error fix")
            self.status_label.config(text="Searching web for fix...", fg="#F39C12")
            self.goof_callback(self._last_output)
        else:
            self.log("[GOOF] No goof_callback configured")

    def _check_dependencies(self, code: str) -> tuple:
        """Check which packages are available in SANDBOX venv and which are missing"""
        imports = self._extract_imports(code)
        available = []
        missing = []

        builtin_modules = {
            'os', 'sys', 're', 'time', 'threading', 'subprocess', 'tempfile',
            'json', 'csv', 'math', 'random', 'datetime', 'collections', 'itertools',
            'functools', 'operator', 'pathlib', 'pickle', 'base64', 'hashlib',
            'urllib', 'http', 'socket', 'email', 'html', 'xml', 'queue',
            'copy', 'pprint', 'enum', 'dataclasses', 'typing', 'io', 'struct',
            'ctypes', 'asyncio', 'concurrent', 'multiprocessing',
            'simpleaudio',
            # Local project files — never try to pip install these
            'asr_whisper', 'document_reader', 'Internet_Tools', 'math_speech',
            'code_window', 'code_execution_loop', 'mistake_memory', 'latex_window',
            'paper_tools_window', 'theme_manager', 'self_improver', 'planner',
            'agent_executor', 'code_display'
        }

        for module in imports:
            if module is None:
                continue

            if module in builtin_modules:
                available.append(module)
                continue

            if module == 'mpl_toolkits' or module.startswith('mpl_toolkits'):
                check_module = 'matplotlib'
            else:
                check_module = module

            try:
                result = subprocess.run(
                    [self.sandbox_python, '-c', f'import {check_module}'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    available.append(module)
                else:
                    missing.append(module)
            except:
                missing.append(module)

        return available, missing

    def _install_package(self, package_name: str) -> bool:
        """Attempt to install a package via pip in sandbox venv"""
        pip_name = self.PACKAGE_NAME_MAP.get(package_name, package_name)

        version_pins = {
            'numpy': 'numpy==2.2.6',
            'scipy': 'scipy==1.15.2',
            'matplotlib': 'matplotlib==3.10.1',
            'pygame': 'pygame==2.6.1',
            'pandas': 'pandas==2.2.3',
            'pillow': 'pillow==11.1.0'
        }

        if pip_name in version_pins:
            pip_name = version_pins[pip_name]
            self.log(f"[sandbox] Using pinned version: {pip_name}")

        self.log(f"[sandbox] Installing '{pip_name}' into sandbox venv...")
        self._append_output(f"📦 Installing {pip_name}...\n", False)

        try:
            result = subprocess.run(
                [self.sandbox_python, '-m', 'pip', 'install', pip_name, '-q'],
                capture_output=True, text=True, timeout=120
            )

            if result.returncode == 0:
                self.log(f"[sandbox] ✓ Successfully installed {pip_name}")
                self._append_output(f"✓ Installed {pip_name}\n", False)
                return True
            else:
                self.log(f"[sandbox] ✗ Failed to install {pip_name}: {result.stderr}")
                self._append_output(f"✗ Failed to install {pip_name}\n", True)
                return False
        except subprocess.TimeoutExpired:
            self.log(f"[sandbox] ✗ Installation timeout for {pip_name}")
            self._append_output(f"✗ Installation timeout for {pip_name}\n", True)
            return False
        except Exception as e:
            self.log(f"[sandbox] ✗ Error installing {pip_name}: {e}")
            self._append_output(f"✗ Error: {e}\n", True)
            return False

    def _ensure_dependencies(self, code: str) -> bool:
        """Check and auto-install missing dependencies"""
        available, missing = self._check_dependencies(code)

        if not missing:
            self.log(f"[sandbox] All dependencies available: {', '.join(available) if available else 'none needed'}")
            return True

        self.log(f"[sandbox] Missing packages: {missing}")
        self._append_output(f"Missing packages detected: {', '.join(missing)}\n\n", False)

        failed = []
        for package in missing:
            if not self._install_package(package):
                failed.append(package)

        if failed:
            self._append_output(f"\n⚠️ Could not install: {', '.join(failed)}\n", False)
            self._append_output(f"These may be local project files — continuing anyway...\n\n", False)
            self.log(f"[sandbox] ⚠️ Failed to install {failed} — running anyway (may be local modules)")

        self._append_output("\n✅ Dependencies checked — running code...\n\n", False)
        self.log("[sandbox] All dependencies checked, proceeding to execution")
        return True

    def _run_code_safe(self, from_smart_loop=False):
        """Execute code safely"""
        self.log("[sandbox] ⚡ AUTO-RUN STARTING")
        # reset save flag for new execution as we save code
        self._code_saved = False
        self.execution_complete.clear()
        self._last_output = ""
        self._last_had_error = False

        if not from_smart_loop:
            self.log("[sandbox] 🔄 Manual run - resetting halt flags")
            self.halt_code_generation = False
            self.halt_preserve_current = False
        else:
            self.log("[sandbox] 🤖 Smart loop run - preserving halt flags")

        code = self.code_display.text.get("1.0", tk.END).strip()
        self.log(f"[sandbox] Code length: {len(code)} chars")
        if not code:
            self._show_output("No code to execute.", is_error=True)
            return

        self.run_btn.config(text="Checking...")
        self.status_label.config(text="Checking dependencies...", fg="#F39C12")
        self._clear_output()
        self.save_plot_btn.config(state=tk.DISABLED)
        self.open_plot_btn.config(state=tk.DISABLED)
        self.execution_stopped = False

        threading.Thread(target=self._run_with_dependencies, args=(code,), daemon=True).start()

    def _run_with_dependencies(self, code: str):
        """Check dependencies and run code"""
        if not self._ensure_dependencies(code):
            self.after(0, self._reset_ui_after_execution)
            return

        self.after(0, lambda: self.run_btn.config(text="Running..."))
        self.after(0, lambda: self.status_label.config(text="Executing...", fg="#F39C12"))
        self._execute_code(code)

    def _stop_execution(self):
        """Stop the currently running process"""
        self.log("[sandbox] ⚠️ STOP BUTTON CLICKED")
        self.execution_stopped = True

        if self.process and self.process.poll() is None:
            self.log(f"[sandbox] Killing process PID: {self.process.pid}")
            try:
                self.process.kill()
                self.process.wait(timeout=2)
                self.log("[sandbox] Process killed successfully")
            except Exception as e:
                self.log(f"[sandbox] Error killing process: {e}")

        self.after(0, self._append_output, "\n[⚠️ EXECUTION STOPPED BY USER]\n", True)
        self.after(0, lambda: self.status_label.config(text="Stopped by user", fg="#F39C12"))
        self.after(0, lambda: self.input_entry.config(state="disabled"))
        self.after(0, self._reset_ui_after_execution)

    def _halt_code_generation(self):
        """HALT auto code generation - preserve current code in editor"""
        self.log("[sandbox] 🛑 HALT CODE GENERATION REQUESTED")
        self.halt_code_generation = True
        self.halt_preserve_current = True

        self._stop_execution()

        if self.stop_callback:
            self.stop_callback()

        current_code = self.code_display.text.get("1.0", tk.END).strip()
        self.log(f"[sandbox] Preserving current code in editor ({len(current_code)} chars)")

        self.halt_btn.config(state=tk.DISABLED)
        self.after(0, self._append_output, "\n[🛑 CODE GENERATION HALTED - PRESERVING CURRENT CODE]\n", True)
        self.after(0, lambda: self.status_label.config(text="🛑 HALTED", fg="#9B59B6"))
        self.log("[sandbox] Code generation disabled - user can review and modify code manually")

    def reset_for_new_task(self):
        """Reset all flags and state for a new task"""
        for pattern in ["plot.png", "*.png", "figure*.png"]:
            for f in glob.glob(pattern):
                try:
                    os.remove(f)
                except:
                    pass
        self._code_saved = False  # for saving code again
        self._last_had_error = False
        self.execution_complete.set()
        self._last_output = ""

        if hasattr(self, 'halt_code_generation'):
            self.halt_code_generation = False

        self.log("[sandbox] ✅ All state reset")

    def _detect_plotting(self, code: str) -> bool:
        """Detect if code uses matplotlib plotting"""
        plotting_indicators = [
            'matplotlib', 'plt.show', 'plt.plot', 'plt.figure',
            'plt.subplot', 'plt.savefig', '.plot(', 'pyplot',
            'plt.bar', 'plt.scatter', 'plt.hist', 'plt.imshow',
            'plt.contour', 'ax.plot', 'ax.bar', 'fig,', 'fig =',
        ]
        code_lower = code.lower()
        return any(indicator.lower() in code_lower for indicator in plotting_indicators)

    def _wrap_code_for_plotting(self, code: str) -> tuple:
        """Wrap code to save plot to temp file AND show interactively"""
        timestamp = int(time.time() * 1000)
        plot_path = os.path.join(
            tempfile.gettempdir(),
            f"sandbox_plot_{os.getpid()}_{timestamp}.png"
        )
        plot_path_safe = plot_path.replace('\\', '/')

        wrapped = f'''
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

_plot_save_path = "{plot_path_safe}"
_original_show = plt.show

def _patched_show(*args, **kwargs):
    for fig_num in plt.get_fignums():
        fig = plt.figure(fig_num)
        fig.savefig(_plot_save_path, dpi=150, bbox_inches='tight', facecolor='white')
        print("[Plot auto-saved to:", _plot_save_path, "]")
    _original_show(*args, **kwargs)

plt.show = _patched_show

# === USER CODE BELOW ===
{code}
'''
        return wrapped, plot_path

    def _wrap_code_for_safety(self, code: str) -> str:
        """Add safety header"""
        safety_header = (
            "import warnings\n"
            "warnings.filterwarnings('ignore')\n"
            "import os, sys\n"
        )
        return safety_header + code

    def _execute_code(self, code: str, retry_count=0):
        """Actually execute the code"""
        self.log(f"[EXEC] Executing (attempt {retry_count + 1})")
        self.after(0, lambda: self.status_label.config(text="RUNNING", fg="#39FF14"))

        has_plotting = self._detect_plotting(code)

        if has_plotting:
            safe_code, plot_path = self._wrap_code_for_plotting(code)
        else:
            safe_code = self._wrap_code_for_safety(code)
            plot_path = None
        if has_plotting and plot_path:
            self._start_plot_watcher(plot_path)

        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.py',
                delete=False, encoding='utf-8') as f:
            f.write(safe_code)
            temp_path = f.name

        python_exe = getattr(self, 'sandbox_python', sys.executable)
        if not os.path.exists(python_exe):
            python_exe = sys.executable

        try:
            self.process = subprocess.Popen(
                [python_exe, '-u', temp_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                cwd=getattr(self, 'working_dir', os.path.dirname(os.path.abspath(__file__)))
            )

            self.after(0, lambda: self.input_entry.config(state="normal"))
            self.after(0, lambda: self.input_entry.focus_set())

            output_queue = queue.Queue()

            def read_stdout():
                try:
                    while True:
                        if self.execution_stopped:
                            break
                        char = self.process.stdout.read(1)
                        if not char:
                            break
                        output_queue.put(('out', char))
                except:
                    pass

            def read_stderr():
                try:
                    while True:
                        if self.execution_stopped:
                            break
                        char = self.process.stderr.read(1)
                        if not char:
                            break
                        output_queue.put(('err', char))
                except:
                    pass

            stdout_thread = threading.Thread(target=read_stdout, daemon=True)
            stderr_thread = threading.Thread(target=read_stderr, daemon=True)
            stdout_thread.start()
            stderr_thread.start()

            output_lines = []
            error_lines = []

            timeout = 900 if has_plotting else 300
            start_time = time.time()

            while True:
                if self.execution_stopped:
                    self.log("[sandbox] Execution stopped flag detected, exiting loop")
                    break

                if time.time() - start_time > timeout:
                    self.process.kill()
                    self.after(0, self._show_output, f"Timeout: Exceeded {timeout}s", True)
                    break

                retcode = self.process.poll()
                if retcode is not None:
                    time.sleep(0.1)
                    while not output_queue.empty():
                        try:
                            msg_type, char = output_queue.get_nowait()
                            if msg_type == 'out':
                                output_lines.append(char)
                                self.after(0, self._append_output, char, False)
                            else:
                                error_lines.append(char)
                                self.after(0, self._append_output, char, True)
                        except queue.Empty:
                            break

                    final_output = ''.join(output_lines)
                    final_error = ''.join(error_lines)

                    if not self.execution_stopped:
                        self.after(0, self._finish_execution,
                                   final_output, final_error, retcode, plot_path)
                    break

                try:
                    msg_type, char = output_queue.get(timeout=0.05)
                    if msg_type == 'out':
                        output_lines.append(char)
                        self.after(0, self._append_output, char, False)
                    else:
                        error_lines.append(char)
                        self.after(0, self._append_output, char, True)
                except queue.Empty:
                    pass

        except Exception as e:
            if not self.execution_stopped:
                self.after(0, self._show_output, f"Execution error: {e}", True)

        finally:
            self.after(0, lambda: self.input_entry.config(state="disabled"))
            try:
                os.unlink(temp_path)
            except:
                pass

        if not self.execution_stopped:
            self.after(0, self._reset_ui_after_execution)

    def _start_plot_watcher(self, plot_path: str):
        """Watch for plot file and copy to web_images immediately when it appears"""

        def watch():
            import time
            import shutil
            deadline = time.time() + 60  # Watch for up to 60 seconds
            last_size = -1
            while time.time() < deadline:
                if self.execution_stopped:
                    break
                if os.path.exists(plot_path):
                    size = os.path.getsize(plot_path)
                    if size > 0 and size == last_size:
                        # File is stable — copy it
                        try:
                            project_root = os.path.dirname(os.path.abspath(__file__))
                            web_dir = os.path.join(project_root, "web_images")
                            os.makedirs(web_dir, exist_ok=True)
                            timestamp = int(time.time() * 1000)
                            web_filename = f"plot_{timestamp}.png"
                            web_path = os.path.join(web_dir, web_filename)
                            shutil.copy2(plot_path, web_path)
                            self.log(f"[PLOT WATCHER] Copied to web: {web_filename}")
                            if self.output_callback:
                                self.after(0, lambda fn=web_filename: self.output_callback(f"[IMAGE:{fn}]"))
                        except Exception as e:
                            self.log(f"[PLOT WATCHER] Error: {e}")
                        break
                    last_size = size
                time.sleep(0.5)

        threading.Thread(target=watch, daemon=True).start()


    def _send_input_line(self, event=None):
        """Send a line of input to the running process"""
        if not self.process or self.process.poll() is not None:
            return

        line = self.input_entry.get()
        try:
            self._append_output(f"> {line}\n", False)
            self.process.stdin.write(line + '\n')
            self.process.stdin.flush()
            self.input_entry.delete(0, tk.END)
        except Exception as e:
            self._append_output(f"[Input error: {e}]\n", True)

    def _append_output(self, text: str, is_error=False):
        """Append text to output"""
        self.output_text.config(state="normal")
        if is_error:
            self.output_text.tag_configure("error", foreground="#ff6b6b")
            self.output_text.insert(tk.END, text, "error")
        else:
            self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state="disabled")

    def _finish_execution(self, stdout, stderr, returncode, plot_path):
        """Finish execution and show summary"""
        self._last_output = stdout + ("\n" + stderr if stderr else "")
        self._last_had_error = returncode != 0
        has_error = returncode != 0 or stderr.strip()

        if has_error:
            self.status_label.config(text=f"Failed (exit code: {returncode})", fg="#FF4444")
        else:
            self.status_label.config(text="Success", fg="#39FF14")

        if plot_path and os.path.exists(plot_path):
            self.last_plot_path = plot_path
            self.save_plot_btn.config(state=tk.NORMAL)
            self.open_plot_btn.config(state=tk.NORMAL)
            self.status_label.config(text="Success - Plot saved!", fg="#39FF14")
            self.log("[sandbox] Plot generated successfully")

            # Save the final code to history
            if not self._code_saved:
                final_code = self.code_display.text.get("1.0", tk.END).strip()
                self._save_code_to_file(final_code)
                self._code_saved = True
                self.log("[sandbox] Saved final code to history")

            # Web image copy is handled by _start_plot_watcher — no need to copy here

            self.execution_complete.set()
            return

        if has_error and self.auto_send_var.get():
            if self.from_smart_loop:
                self.log("[sandbox] Smart loop active - error handled internally")
            elif not self.halt_code_generation:
                self.log("[sandbox] Error detected - auto-sending to AI for fix")
                self._send_output_to_ai()
            else:
                self.log("[sandbox] 🛑 Error detected but generation HALTED - NOT auto-sending")
        elif not has_error:
            self.from_smart_loop = False
            self.log("[sandbox] Code succeeded - not sending error")

        self.execution_complete.set()


    def _send_output_to_ai(self):
        """Send the last output to the main app"""
        if not hasattr(self, '_last_output') or not self._last_output:
            self.status_label.config(text="No output to send", fg="#F39C12")
            self.log("[sandbox] No output to send to AI")
            return

        if not self.output_callback:
            self.status_label.config(text="No AI connection", fg="#FF4444")
            self.log("[sandbox] No output callback configured")
            return

        try:
            output_lower = self._last_output.lower()

            actual_error_indicators = [
                'traceback (most recent call last)',
                'error:', 'exception:', 'failed', 'failure',
            ]
            success_indicators = [
                'ran 4 tests', 'ran 3 tests', 'ran 2 tests', 'ran 1 test',
                '\nok\n', 'tests in ',
            ]

            is_unittest_success = any(indicator in output_lower for indicator in success_indicators)
            has_actual_error = any(indicator in output_lower for indicator in actual_error_indicators)

            code = self.code_display.text.get("1.0", tk.END).strip()

            if is_unittest_success and not has_actual_error:
                message = f"""Here is the output from my Python program:

OUTPUT:
{self._last_output}

CODE:
{code}
"""
                self.log("[sandbox] Unittest success detected - sending as success")

            elif self._last_had_error or has_actual_error:
                message = f"""
The following Python code produced errors.

Fix the program and return the COMPLETE corrected script.

Return ONLY Python code.

ERROR OUTPUT:
{self._last_output}

CODE:
{code}
"""
            else:
                message = f"""Here is the output from my Python program:

OUTPUT:
{self._last_output}

CODE:
{code}
"""

            self.output_callback(message)
            self.status_label.config(text="Sent to AI", fg="#39FF14")
            self.log(f"[sandbox] Output sent to AI ({len(self._last_output)} chars)")

        except Exception as e:
            self.status_label.config(text="Send failed", fg="#FF4444")
            self.log(f"[sandbox] Failed to send to AI: {e}")

    def _save_plot(self):
        """Save the last generated plot"""
        if not self.last_plot_path or not os.path.exists(self.last_plot_path):
            self.status_label.config(text="No plot to save", fg="#F39C12")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG Image", "*.png"),
                ("JPEG Image", "*.jpg"),
                ("PDF Document", "*.pdf"),
                ("SVG Vector", "*.svg"),
                ("All Files", "*.*")
            ],
            title="Save Plot As"
        )

        if save_path:
            try:
                shutil.copy2(self.last_plot_path, save_path)
                self.status_label.config(
                    text=f"Plot saved to {os.path.basename(save_path)}", fg="#4A9EFF")
                self.log(f"[sandbox] Plot saved to: {save_path}")
            except Exception as e:
                self.status_label.config(text=f"Save failed: {e}", fg="#FF4444")

    def _open_plot(self):
        """Open the last generated plot in default viewer"""
        if not self.last_plot_path or not os.path.exists(self.last_plot_path):
            self.status_label.config(text="No plot to open", fg="#F39C12")
            return

        try:
            if sys.platform == 'win32':
                os.startfile(self.last_plot_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', self.last_plot_path])
            else:
                subprocess.run(['xdg-open', self.last_plot_path])
            self.status_label.config(text="Plot opened in viewer", fg="#4A9EFF")
        except Exception as e:
            self.status_label.config(text=f"Could not open: {e}", fg="#FF4444")

    def _show_output(self, text: str, is_error=False):
        """Show output in the output text area"""
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        text_clean = text.encode('ascii', 'ignore').decode('ascii')
        if is_error:
            self.output_text.tag_configure("error", foreground="#ff6b6b")
            self.output_text.insert("1.0", text_clean, "error")
        else:
            self.output_text.tag_configure("success", foreground="#50c878")
            self.output_text.insert("1.0", text_clean, "success")
        self.output_text.config(state="disabled")
        self.output_text.see("1.0")

    def _clear_output(self):
        """Clear the output text area"""
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state="disabled")

    def _reset_ui_after_execution(self):
        """Reset UI after code execution"""
        self.run_btn.config(text="▶ RUN")
        self.status_label.config(text="IDLE", fg="#6B7A99")

    def _copy_code(self):
        """Copy code to clipboard"""
        code = self.code_display.text.get("1.0", tk.END).strip()
        if code:
            self.clipboard_clear()
            self.clipboard_append(code)
            self.status_label.config(text="Copied to clipboard", fg="#4A9EFF")
            self.log("[sandbox] Code copied to clipboard")

    def _clear_code(self):
        """Clear the code editor"""
        self.code_display.set_editable(True)
        self.code_display.text.delete("1.0", tk.END)
        self._clear_output()
        self.status_label.config(text="Cleared", fg="#6B7A99")
        self.log("[sandbox] Code cleared")

    def show(self):
        """Show the code window"""
        self.deiconify()
        self.lift()
        self.focus_set()
        self.code_display.text.focus_set()

    def hide(self):
        """Hide the code window"""
        if self.process and self.process.poll() is None:
            self._stop_execution()
        self.withdraw()

    def log(self, message):
        """Log messages through callback"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def run(self, code):
        self.execution_complete.clear()
        self.set_code(code, auto_run=True, from_smart_loop=True)
        self.execution_complete.wait()
        return self._last_output