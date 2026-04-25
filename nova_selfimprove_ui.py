"""
nova_selfimprove_ui.py — Self-improvement UI mixin for Nova Assistant.

Contains NovaSelfImproveUI: all EVOLVE, DEBUG, DIAGNOSE, and DOCUMENT
popup dialogs and their background worker threads.

Usage:
    from nova_selfimprove_ui import NovaSelfImproveUI

    class NovaAssistant(NovaTTS, NovaSelfImproveUI):
        ...
"""

import os
import re
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext

# ── Colour / font constants (mirrors nova_assistant_v1.py) ────────────────────
BG_LEFT        = "#111520"
BG_INPUT       = "#141926"
BG_CONSOLE     = "#080C12"
SEAM           = "#1E3A5F"
ELECTRIC_BLUE  = "#4A9EFF"
DIM_TEXT       = "#6B7A99"
GREEN_GLOW     = "#2ECC71"
RED_GLOW       = "#FF4444"
AMBER          = "#F39C12"
VIOLET         = "#9B59B6"
WHITE          = "#FFFFFF"
FG_MAIN        = "#D4E0F7"

F_RAJ_BIG  = ("Rajdhani", 13, "bold")
F_RAJ_SM   = ("Rajdhani", 10)
F_RAJ_BTN  = ("Rajdhani", 12, "bold")
F_CONSOLAS = ("Consolas", 11)
F_COURIER  = ("Courier New", 10)


class NovaSelfImproveUI:
    """Mixin that adds EVOLVE, DEBUG, DIAGNOSE and DOCUMENT UI to NovaAssistant."""

    # ──────────────────────────────────────────────────────────────────────────
    # EVOLVE
    # ──────────────────────────────────────────────────────────────────────────

    def _run_evolution(self):
        """Show the EVOLVE popup — add a feature or fix a known weakness."""
        popup = tk.Toplevel(self.root)
        popup.title("Self Improvement")
        popup.geometry("520x300")
        popup.configure(bg=BG_LEFT)
        popup.grab_set()

        popup.update_idletasks()
        x = self.root.winfo_x() + self.root.winfo_width() // 2 - 260
        y = self.root.winfo_y() + self.root.winfo_height() // 2 - 150
        popup.geometry(f"+{x}+{y}")

        tk.Label(popup, text="🧬 EVOLVE NOVA",
                 font=F_RAJ_BIG, bg=BG_LEFT, fg="#FF00FF").pack(pady=(16, 4))
        tk.Label(popup,
                 text="Describe a new feature, or leave blank to fix a known weakness.",
                 font=F_RAJ_SM, bg=BG_LEFT, fg=DIM_TEXT,
                 wraplength=480).pack(pady=(0, 8))
        tk.Label(popup, text="Feature request (optional):",
                 font=F_RAJ_SM, bg=BG_LEFT, fg=FG_MAIN).pack(anchor="w", padx=20)

        entry = tk.Text(popup, height=4, bg=BG_INPUT, fg=FG_MAIN,
                        font=F_CONSOLAS, relief="flat",
                        insertbackground=ELECTRIC_BLUE, wrap="word")
        entry.pack(fill="x", padx=20, pady=6)

        bf = tk.Frame(popup, bg=BG_LEFT)
        bf.pack(pady=8)

        def _go():
            feature_text = entry.get("1.0", "end").strip()
            popup.destroy()
            if feature_text:
                self._append_conv("system", f"🔧 Adding feature: {feature_text}")
                threading.Thread(target=self._feature_worker,
                                 args=(feature_text,), daemon=True).start()
            else:
                self._append_conv("system", "🧬 Analysing weaknesses...")
                threading.Thread(target=self._evolution_worker, daemon=True).start()

        def _history():
            popup.destroy()
            self._show_evolution_history()

        def _cancel():
            popup.destroy()

        tk.Button(bf, text="🚀 Run", command=_go,
                  bg="#27ae60", fg=WHITE, width=12,
                  font=F_RAJ_BTN).pack(side="left", padx=6)
        tk.Button(bf, text="📜 History", command=_history,
                  bg=VIOLET, fg=WHITE, width=12,
                  font=F_RAJ_BTN).pack(side="left", padx=6)
        tk.Button(bf, text="Cancel", command=_cancel,
                  bg="#e74c3c", fg=WHITE, width=10,
                  font=F_RAJ_BTN).pack(side="left", padx=6)

    def _evolution_worker(self):
        """Run the self-improvement cycle and report the result."""
        try:
            success = self.self_improver.run_improvement_cycle()
            if success:
                v = self.self_improver._get_current_version("nova_assistant")
                self._append_conv("assistant",
                                  f"I applied an improvement. "
                                  f"A new version nova_assistant_v{v}.py has been created. "
                                  f"Restart using that file to use the improvement.")
            else:
                self._append_conv("assistant",
                                  "I analysed my code but could not find a safe improvement to apply right now.")
        except Exception as e:
            self.log(f"[EVOLVE] ❌ Evolution worker failed: {e}")
            self._append_conv("assistant", f"❌ Evolution failed: {e}")

    def _feature_worker(self, feature_request):
        """Generate and apply a new feature — single-step or multi-step depending on complexity."""
        try:
            word_count = len(feature_request.split())
            complexity_words = ["and", "also", "with", "plus", "including", "as well"]
            use_multi = word_count > 15 or any(
                w in feature_request.lower() for w in complexity_words)

            if use_multi:
                self._append_conv("system", "🔀 Complex feature — decomposing into steps...")

                def _progress(step_num, total, step_desc):
                    self._append_conv("system", f"  Step {step_num}/{total}: {step_desc}")

                success, working_source, msg = self.self_improver.run_multi_step_feature(
                    feature_request, progress_callback=_progress)

                if not success or not working_source:
                    self._append_conv("assistant", f"❌ {msg}")
                    return
            else:
                self._append_conv("system", "🔧 Generating feature...")
                success, cycle_result = self.self_improver.run_feature_cycle(feature_request)

                if not success:
                    self._append_conv("assistant", f"❌ {cycle_result}")
                    return

                working_source, msg, nova_was_patched = cycle_result

                if not nova_was_patched:
                    ver = self.self_improver._get_current_version("nova_assistant")
                    self.self_improver._log_entry("nova_assistant", ver, feature_request, msg)
                    self._append_conv("assistant",
                                      f"✅ {msg}\n\nExternal files patched — no new Nova version needed.")
                    return

            project_root = os.path.dirname(os.path.abspath(__file__))
            ver_success, ver = self.self_improver._write_new_version(
                "nova_assistant", working_source, feature_request[:60].replace("\n", " "))
            if not ver_success:
                self._append_conv("assistant", "❌ Failed to save version.")
                return

            fname = self.self_improver._versioned_filename("nova_assistant", ver)
            self.self_improver._log_entry("nova_assistant", ver, feature_request, msg)
            self.log(f"[EVOLVE] New version written: {fname}")

            def _show():
                main_python = os.path.join(project_root, ".venv", "Scripts", "python.exe")
                if os.path.exists(main_python):
                    self.code_window.sandbox_python = main_python
                if hasattr(self.code_window, "working_dir"):
                    self.code_window.working_dir = project_root
                path_fix = (
                    f"import sys, os\n"
                    f"sys.path.insert(0, r'{project_root}')\n\n"
                )
                self.code_window.set_code(path_fix + working_source)
                self.code_window.show()

            self.root.after(0, _show)
            self._append_conv("assistant",
                              f"✅ {msg}\n\nSaved as {fname}. Review the code in the sandbox window.")

        except Exception as e:
            self.log(f"[EVOLVE] ❌ Feature worker failed: {e}")
            self._append_conv("assistant", f"❌ Feature generation failed: {e}")

    def _show_evolution_history(self):
        """Show a popup with the full evolution history log."""
        popup = tk.Toplevel(self.root)
        popup.title("Evolution History")
        popup.geometry("700x500")
        popup.configure(bg=BG_LEFT)
        tk.Label(popup, text="EVOLUTION HISTORY", font=F_RAJ_BIG,
                 bg=BG_LEFT, fg="#FF00FF").pack(pady=10)
        txt = scrolledtext.ScrolledText(popup, bg=BG_CONSOLE, fg="#FF88FF",
                                        font=F_COURIER, wrap="word")
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        try:
            txt.insert("end", self.self_improver.export_history())
        except Exception as e:
            txt.insert("end", f"Could not load history: {e}")
        txt.config(state="disabled")

    # ──────────────────────────────────────────────────────────────────────────
    # DEBUG
    # ──────────────────────────────────────────────────────────────────────────

    def _run_debug(self):
        """Show the DEBUG popup with target version selector and symptom entry."""
        popup = tk.Toplevel(self.root)
        popup.title("Debug Nova")
        popup.geometry("520x320")
        popup.configure(bg=BG_LEFT)
        popup.grab_set()

        popup.update_idletasks()
        x = self.root.winfo_x() + self.root.winfo_width() // 2 - 260
        y = self.root.winfo_y() + self.root.winfo_height() // 2 - 160
        popup.geometry(f"+{x}+{y}")

        tk.Label(popup, text="DEBUG NOVA",
                 font=F_RAJ_BIG, bg=BG_LEFT, fg=RED_GLOW).pack(pady=(16, 4))
        tk.Label(popup,
                 text="Describe what is broken or not working as expected.",
                 font=F_RAJ_SM, bg=BG_LEFT, fg=DIM_TEXT,
                 wraplength=480).pack(pady=(0, 8))

        target_row = tk.Frame(popup, bg=BG_LEFT)
        target_row.pack(fill="x", padx=20, pady=(0, 6))
        tk.Label(target_row, text="Debug target:",
                 font=F_RAJ_SM, bg=BG_LEFT, fg=FG_MAIN).pack(side="left", padx=(0, 8))

        project_root = os.path.dirname(os.path.abspath(__file__))
        try:
            version_files = sorted([
                f for f in os.listdir(project_root)
                if f.startswith("nova_assistant_v") and f.endswith(".py")
            ])
        except OSError:
            version_files = []
        options = ["current version"] + version_files

        target_var = tk.StringVar(value="current version")
        target_cb = ttk.Combobox(target_row, values=options,
                                 textvariable=target_var,
                                 style="Dark.TCombobox",
                                 state="readonly", width=28)
        target_cb.pack(side="left")

        tk.Label(popup, text="Symptom:",
                 font=F_RAJ_SM, bg=BG_LEFT, fg=FG_MAIN).pack(anchor="w", padx=20)

        entry = tk.Text(popup, height=4, bg=BG_INPUT, fg=FG_MAIN,
                        font=F_CONSOLAS, relief="flat",
                        insertbackground=ELECTRIC_BLUE, wrap="word")
        entry.pack(fill="x", padx=20, pady=6)

        bf = tk.Frame(popup, bg=BG_LEFT)
        bf.pack(pady=8)

        def _go():
            symptom = entry.get("1.0", "end").strip()
            target = target_var.get()
            if not symptom:
                entry.config(bg="#4A1A1A")
                return
            popup.destroy()
            threading.Thread(target=self._debug_worker,
                             args=(symptom, target), daemon=True).start()

        def _cancel():
            popup.destroy()

        tk.Button(bf, text="Fix It", command=_go,
                  bg="#c0392b", fg=WHITE, width=12,
                  font=F_RAJ_BTN).pack(side="left", padx=6)
        tk.Button(bf, text="Cancel", command=_cancel,
                  bg="#7f8c8d", fg=WHITE, width=10,
                  font=F_RAJ_BTN).pack(side="left", padx=6)

    def _debug_worker(self, symptom, target="current version"):
        """Background thread — run a debug cycle and write the fixed version."""
        try:
            if target == "current version":
                self._append_conv("system", f"Diagnosing current version: {symptom}")
                success, cycle_result = self.self_improver.run_debug_cycle(symptom)
            else:
                project_root = os.path.dirname(os.path.abspath(__file__))
                target_path = os.path.join(project_root, target)
                self._append_conv("system", f"Diagnosing {target}: {symptom}")
                success, cycle_result = self.self_improver.run_debug_cycle_on_file(
                    symptom, target_path)

            if not success:
                self._append_conv("assistant", f"Debug failed: {cycle_result}")
                return

            working_source, msg, nova_was_patched = cycle_result

            if not nova_was_patched:
                self._append_conv("assistant",
                                  f"{msg}\n\nExternal files patched - no new Nova version needed.")
                return

            project_root = os.path.dirname(os.path.abspath(__file__))
            ver_success, ver = self.self_improver._write_new_version(
                "nova_assistant", working_source, f"Debug fix: {symptom[:50]}")

            if not ver_success:
                self._append_conv("assistant", "Failed to save version.")
                return

            fname = self.self_improver._versioned_filename("nova_assistant", ver)
            self.self_improver._log_entry("nova_assistant", ver, f"DEBUG: {symptom}", msg)
            self.log(f"[DEBUG] Fix written: {fname}")

            def _show():
                project_root = os.path.dirname(os.path.abspath(__file__))
                main_python = os.path.join(project_root, ".venv", "Scripts", "python.exe")
                if os.path.exists(main_python):
                    self.code_window.sandbox_python = main_python
                path_fix = (
                    f"import sys, os\n"
                    f"sys.path.insert(0, r'{project_root}')\n\n"
                )
                self.code_window.set_code(path_fix + working_source)
                self.code_window.show()

            self.root.after(0, _show)
            self._append_conv("assistant",
                              f"{msg}\n\nSaved as {fname}. "
                              f"{'Restart' if target == 'current version' else 'Launch ' + fname} "
                              f"to apply the fix.")

        except Exception as e:
            self.log(f"[DEBUG] ❌ Debug worker failed: {e}")
            self._append_conv("assistant", f"❌ Debug failed: {e}")

    def _debug_external_file(self, symptom, file_path):
        """Debug an external file and save a fixed copy alongside the original."""
        self._append_conv("system", f"Debugging external file: {file_path}")

        try:
            success, cycle_result = self.self_improver.run_debug_cycle_on_file(
                symptom, file_path)
        except Exception as e:
            self._append_conv("assistant", f"❌ Debug failed: {e}")
            return

        if not success:
            self._append_conv("assistant", f"Debug failed: {cycle_result}")
            return

        working_source, msg, _ = cycle_result
        base, ext = os.path.splitext(file_path)
        out_path = base + "_fixed" + ext

        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(working_source)
            self._append_conv("assistant",
                              f"{msg}\n\n"
                              f"Fixed copy saved as {out_path}\n"
                              f"Original file untouched.")
            self.log(f"[DEBUG] External fix written: {out_path}")
        except Exception as e:
            self._append_conv("assistant", f"Could not save fixed file: {e}")

    def _show_in_code_window(self, code):
        """Display patched source in the code window using the main project venv."""
        try:
            project_root = os.path.dirname(os.path.abspath(__file__))
            main_venv = os.path.join(project_root, ".venv")

            if hasattr(self.code_window, "venv_path"):
                self.code_window.venv_path = main_venv
            if hasattr(self.code_window, "working_dir"):
                self.code_window.working_dir = project_root
            if hasattr(self.smart_loop, "sandbox"):
                self.smart_loop.sandbox.venv_path = main_venv
                self.smart_loop.sandbox.working_dir = project_root

            path_fix = (
                f"import sys, os\n"
                f"sys.path.insert(0, r'{project_root}')\n\n"
            )
            self.code_window.set_code(path_fix + code)
            self.code_window.show()
            self.log(f"[EVOLVE] Using main venv: {main_venv}")
        except Exception as e:
            self.log(f"[EVOLVE] Could not show in code window: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # DIAGNOSE
    # ──────────────────────────────────────────────────────────────────────────

    def _run_diagnostic(self):
        """Show the DIAGNOSE popup — choose which file to analyse."""
        popup = tk.Toplevel(self.root)
        popup.title("Diagnose Nova")
        popup.geometry("520x220")
        popup.configure(bg=BG_LEFT)
        popup.grab_set()

        popup.update_idletasks()
        x = self.root.winfo_x() + self.root.winfo_width() // 2 - 260
        y = self.root.winfo_y() + self.root.winfo_height() // 2 - 110
        popup.geometry(f"+{x}+{y}")

        tk.Label(popup, text="DIAGNOSE NOVA",
                 font=F_RAJ_BIG, bg=BG_LEFT, fg=AMBER).pack(pady=(16, 4))
        tk.Label(popup,
                 text="Analyse source code for issues, dead code and improvements.",
                 font=F_RAJ_SM, bg=BG_LEFT, fg=DIM_TEXT,
                 wraplength=480).pack(pady=(0, 8))

        target_row = tk.Frame(popup, bg=BG_LEFT)
        target_row.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(target_row, text="Analyse target:",
                 font=F_RAJ_SM, bg=BG_LEFT, fg=FG_MAIN).pack(side="left", padx=(0, 8))

        project_root = os.path.dirname(os.path.abspath(__file__))
        try:
            version_files = sorted([
                f for f in os.listdir(project_root)
                if f.startswith("nova_assistant_v") and f.endswith(".py")
            ])
        except OSError:
            version_files = []
        options = ["current version"] + version_files

        target_var = tk.StringVar(value="current version")
        target_cb = ttk.Combobox(target_row, values=options,
                                 textvariable=target_var,
                                 style="Dark.TCombobox",
                                 state="readonly", width=28)
        target_cb.pack(side="left")

        def _browse():
            from tkinter import filedialog
            path = filedialog.askopenfilename(
                title="Select Python file to diagnose",
                filetypes=[("Python files", "*.py")],
                initialdir=project_root
            )
            if path:
                current_values = list(target_cb["values"])
                if path not in current_values:
                    current_values.append(path)
                    target_cb["values"] = current_values
                target_cb.set(path)

        tk.Button(target_row, text="📂 Browse...", command=_browse,
                  bg="#2A3A5A", fg=FG_MAIN, font=F_RAJ_SM,
                  relief="flat", padx=6).pack(side="left", padx=(6, 0))

        bf = tk.Frame(popup, bg=BG_LEFT)
        bf.pack(pady=10)

        def _go():
            target = target_var.get()
            popup.destroy()
            threading.Thread(target=self._diagnostic_worker,
                             args=(target,), daemon=True).start()

        def _cancel():
            popup.destroy()

        tk.Button(bf, text="Analyse", command=_go,
                  bg="#B7950B", fg=WHITE, width=12,
                  font=F_RAJ_BTN).pack(side="left", padx=6)
        tk.Button(bf, text="Cancel", command=_cancel,
                  bg="#7f8c8d", fg=WHITE, width=10,
                  font=F_RAJ_BTN).pack(side="left", padx=6)

    def _diagnostic_worker(self, target):
        """Background thread — read source, run diagnostic, show report popup."""
        self._append_conv("system", f"Analysing {target}...")

        project_root = os.path.dirname(os.path.abspath(__file__))

        try:
            if os.path.isabs(target):
                source_path = target
            elif target == "current version":
                source_path = os.path.abspath(__file__)
            else:
                source_path = os.path.join(project_root, target)

            with open(source_path, "r", encoding="utf-8") as f:
                source = f.read()
        except Exception as e:
            self._append_conv("assistant", f"Could not read source: {e}")
            return

        try:
            report = self.self_improver.run_diagnostic(source)
            issues = self.self_improver._parse_diagnostic_issues(report)
        except Exception as e:
            self._append_conv("assistant", f"Diagnostic failed: {e}")
            return

        self._append_conv("system", f"Diagnostic complete - {len(issues)} issues found")
        self.root.after(0, lambda: self._show_diagnostic_report(report, issues, target))

    def _show_diagnostic_report(self, report, issues, target):
        """Display the diagnostic report in a popup with EVOLVE / DEBUG action buttons."""
        try:
            from code_display import CodeDisplay
        except ImportError as e:
            self._append_conv("assistant", f"❌ Could not load CodeDisplay: {e}")
            return

        popup = tk.Toplevel(self.root)
        popup.title(f"Diagnostic Report - {target}")
        popup.geometry("900x620")
        popup.configure(bg=BG_LEFT)

        project_root = os.path.dirname(os.path.abspath(__file__))
        is_external = (
            os.path.isabs(target) and
            target != os.path.abspath(__file__) and
            not target.startswith(project_root + os.sep)
        )

        tk.Label(popup, text=f"DIAGNOSTIC REPORT - {target}",
                 font=F_RAJ_BIG, bg=BG_LEFT, fg=AMBER).pack(pady=(12, 2))
        tk.Label(popup, text=f"{len(issues)} issues found",
                 font=F_RAJ_SM, bg=BG_LEFT, fg=DIM_TEXT).pack(pady=(0, 4))

        if is_external:
            tk.Label(popup,
                     text="External file - EVOLVE disabled. DEBUG will save a fixed copy alongside the original.",
                     font=F_RAJ_SM, bg=BG_LEFT, fg=AMBER,
                     wraplength=860).pack(pady=(0, 4))

        try:
            cd = CodeDisplay(popup, bg_color=BG_LEFT)
            cd.set_code(report, language="text")
            cd.pack(fill="both", expand=True, padx=10, pady=4)
        except Exception as e:
            popup.destroy()
            self._append_conv("assistant", f"❌ Could not display report: {e}")
            return

        bf = tk.Frame(popup, bg=BG_LEFT)
        bf.pack(pady=10)

        def _send_to_evolve():
            popup.destroy()
            self._send_diagnostic_to_evolve(issues)
        def _send_to_debug():
            popup.destroy()
            critical = [i for i in issues if i.startswith("CRITICAL")][:3]
            symptom = "\n".join(critical) if critical else "\n".join(issues[:3])
            if not symptom:
                self._append_conv("assistant", "No issues to send to DEBUG.")
                return
            if is_external:
                threading.Thread(target=self._debug_external_file,
                                 args=(symptom, target), daemon=True).start()
            else:
                threading.Thread(target=self._debug_worker,
                                 args=(symptom, target), daemon=True).start()

        tk.Button(bf, text="Send to EVOLVE",
                  command=_send_to_evolve,
                  bg="#6C3483" if not is_external else "#3A3A3A",
                  fg=WHITE,
                  state="normal" if not is_external else "disabled",
                  width=16, font=F_RAJ_BTN).pack(side="left", padx=6)

        tk.Button(bf, text="Send to DEBUG",
                  command=_send_to_debug,
                  bg="#922B21", fg=WHITE, width=16,
                  font=F_RAJ_BTN).pack(side="left", padx=6)

        tk.Button(bf, text="Close",
                  command=popup.destroy,
                  bg="#7f8c8d", fg=WHITE, width=10,
                  font=F_RAJ_BTN).pack(side="left", padx=6)

    def _send_diagnostic_to_evolve(self, issues):
        """Package diagnostic issues as an EVOLVE feature request and start the worker."""
        if not issues:
            self._append_conv("assistant", "No issues to send to EVOLVE.")
            return

        issue_list = "\n".join(issues[:10])
        feature_request = f"""Fix the following issues identified by diagnostic analysis:

{issue_list}

Instructions:
- Fix each issue listed above
- Do NOT add new features
- Do NOT rewrite working code
- Make minimal targeted changes only
- Preserve all existing functionality"""

        sent = min(len(issues), 10)
        self._append_conv("system", f"Sending {sent} of {len(issues)} diagnostic issues to EVOLVE...")
        threading.Thread(target=self._feature_worker,
                         args=(feature_request,), daemon=True).start()

    # ──────────────────────────────────────────────────────────────────────────
    # DOCUMENT
    # ──────────────────────────────────────────────────────────────────────────

    def _run_documentation(self):
        """Show the DOCUMENT popup — choose a file and add docstrings to it."""
        popup = tk.Toplevel(self.root)
        popup.title("Document Nova")
        popup.geometry("520x240")
        popup.configure(bg=BG_LEFT)
        popup.grab_set()

        popup.update_idletasks()
        x = self.root.winfo_x() + self.root.winfo_width() // 2 - 260
        y = self.root.winfo_y() + self.root.winfo_height() // 2 - 120
        popup.geometry(f"+{x}+{y}")

        tk.Label(popup, text="📝 DOCUMENT NOVA",
                 font=F_RAJ_BIG, bg=BG_LEFT, fg="#00BFFF").pack(pady=(16, 4))
        tk.Label(popup,
                 text="Add docstrings to every undocumented method.\n"
                      "Works on any Python file — pick from list or browse.",
                 font=F_RAJ_SM, bg=BG_LEFT, fg=DIM_TEXT,
                 wraplength=480).pack(pady=(0, 8))

        target_row = tk.Frame(popup, bg=BG_LEFT)
        target_row.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(target_row, text="Target:",
                 font=F_RAJ_SM, bg=BG_LEFT, fg=FG_MAIN).pack(side="left", padx=(0, 8))

        project_root = os.path.dirname(os.path.abspath(__file__))
        try:
            version_files = sorted([
                f for f in os.listdir(project_root)
                if f.endswith(".py") and f != os.path.basename(__file__)
            ])
        except OSError:
            version_files = []
        options = ["current version"] + version_files

        target_var = tk.StringVar(value="current version")
        target_cb = ttk.Combobox(target_row, values=options,
                                 textvariable=target_var,
                                 style="Dark.TCombobox",
                                 state="readonly", width=22)
        target_cb.pack(side="left")

        def _browse():
            from tkinter import filedialog
            path = filedialog.askopenfilename(
                title="Select Python file to document",
                filetypes=[("Python files", "*.py")],
                initialdir=project_root
            )
            if path:
                current_values = list(target_cb["values"])
                if path not in current_values:
                    current_values.append(path)
                    target_cb["values"] = current_values
                target_cb.set(path)

        tk.Button(target_row, text="📂 Browse...", command=_browse,
                  bg="#2A3A5A", fg=FG_MAIN, font=F_RAJ_SM,
                  relief="flat", padx=6).pack(side="left", padx=(6, 0))

        bf = tk.Frame(popup, bg=BG_LEFT)
        bf.pack(pady=12)

        def _go():
            target = target_var.get()
            popup.destroy()
            threading.Thread(target=self._documentation_worker,
                             args=(target,), daemon=True).start()

        def _cancel():
            popup.destroy()

        tk.Button(bf, text="📝 Document", command=_go,
                  bg="#0066AA", fg=WHITE, width=12,
                  font=F_RAJ_BTN).pack(side="left", padx=6)
        tk.Button(bf, text="Cancel", command=_cancel,
                  bg="#7f8c8d", fg=WHITE, width=10,
                  font=F_RAJ_BTN).pack(side="left", padx=6)

    def _documentation_worker(self, target):
        """Background thread — document all undocumented methods in the target file."""
        project_root = os.path.dirname(os.path.abspath(__file__))
        self._append_conv("system", f"📝 Documenting {target}...")

        def _progress(step, total, desc):
            self._append_conv("system", f"  {desc}")

        if target == "current version":
            source_path = os.path.abspath(__file__)
            is_external = False
        elif os.path.isabs(target):
            source_path = target
            is_external = True
        else:
            source_path = os.path.join(project_root, target)
            is_external = not os.path.basename(target).startswith("nova_assistant")

        try:
            with open(source_path, "r", encoding="utf-8") as f:
                source = f.read()
            self.log(f"[DOC] Read {len(source)} chars from {source_path}")
        except Exception as e:
            self._append_conv("assistant", f"❌ Could not read {target}: {e}")
            return

        success, documented_source, summary = self._run_doc_cycle_on_source(source, _progress)

        if not success or not documented_source:
            self._append_conv("assistant", f"❌ Documentation failed: {summary}")
            return

        if is_external:
            base, ext = os.path.splitext(source_path)
            out_path = base + "_documented" + ext
            try:
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(documented_source)
                self.log(f"[DOC] Written external: {out_path}")
                self._append_conv("assistant",
                                  f"📝 {summary}\n\nSaved as {out_path}\nOriginal file untouched.")
            except Exception as e:
                self._append_conv("assistant", f"❌ Could not save: {e}")

        elif target == "current version":
            ver_success, ver = self.self_improver._write_new_version(
                "nova_assistant", documented_source,
                "Added docstrings to undocumented methods")
            if not ver_success:
                self._append_conv("assistant", "❌ Failed to save documented version.")
                return
            fname = self.self_improver._versioned_filename("nova_assistant", ver)
            self.log(f"[DOC] Written: {fname}")
            self._append_conv("assistant",
                              f"📝 {summary}\n\nSaved as {fname}. Restart to use it.")
        else:
            ver_success, ver = self.self_improver._write_new_version(
                "nova_assistant", documented_source,
                f"Added docstrings — from {target}")
            if not ver_success:
                self._append_conv("assistant", "❌ Failed to save documented version.")
                return
            fname = self.self_improver._versioned_filename("nova_assistant", ver)
            self.log(f"[DOC] Written: {fname}")
            self._append_conv("assistant", f"📝 {summary}\n\nSaved as {fname}.")

    def _run_doc_cycle_on_source(self, source, progress_callback=None):
        """Document all undocumented methods in a source string. Returns (success, source, summary)."""
        import ast
        import py_compile
        import tempfile

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return False, None, f"Syntax error in source: {e}"

        parent_map = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parent_map[id(child)] = node

        undocumented = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                parent = parent_map.get(id(node))
                if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                has_docstring = (
                    node.body and
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)
                )
                if not has_docstring:
                    undocumented.append({
                        "name": node.name,
                        "lineno": node.lineno,
                        "end_lineno": node.end_lineno,
                    })

        total = len(undocumented)
        if total == 0:
            return True, source, "All methods already documented"

        self.log(f"[DOC] Found {total} undocumented: {[m['name'] for m in undocumented]}")
        lines = source.splitlines()
        documented_count = 0
        consecutive_failures = 0

        replacements = {
            "\u2014": "-", "\u2013": "-",
            "\u2018": "'", "\u2019": "'",
            "\u201C": '"', "\u201D": '"',
            "\u2026": "...", "\u00d7": "*",
            "\u00f7": "/", "\u2192": "->", "\u2190": "<-",
        }

        original_max_tokens = getattr(self.ai, "max_tokens", 16000)
        # Process in reverse line order so splice offsets remain valid
        undocumented_sorted = sorted(undocumented, key=lambda x: x["lineno"], reverse=True)

        try:
            for i, method_info in enumerate(undocumented_sorted):
                name          = method_info["name"]
                start         = method_info["lineno"] - 1
                end           = method_info["end_lineno"]
                method_lines  = lines[start:end]
                method_source = "\n".join(method_lines)

                if not any(l.strip().startswith("def ") or l.strip().startswith("async def ")
                           for l in method_lines):
                    self.log(f"[DOC] ⚠️ {name} — skipping fragment (no def found)")
                    continue

                method_line_count = len(method_lines)
                if method_line_count > 60:
                    self.ai.max_tokens = 5000
                elif method_line_count > 30:
                    self.ai.max_tokens = 2000
                else:
                    self.ai.max_tokens = 1000

                if progress_callback:
                    progress_callback(i + 1, total, f"Documenting {name} ({i + 1}/{total})...")

                prompt = f"""Add a concise docstring to this Python method.

Rules:
- Return ONLY the complete method with docstring added
- Keep the docstring brief — 1-3 lines maximum
- Describe what the method does, not how
- Do NOT change any logic or code
- Do NOT add inline comments
- ALWAYS use triple double quotes: \"\"\"like this\"\"\"
- ALWAYS preserve the original method indentation exactly
- NEVER return a method at column 0 if the original was indented
- Wrap in ```python ... ``` block

METHOD:
{method_source}
"""
                try:
                    response = self.ai.generate(prompt, use_planning=False)
                    if not response:
                        consecutive_failures += 1
                        if consecutive_failures >= 6:
                            self.log("[DOC] ❌ 6 consecutive failures — aborting")
                            break
                        continue

                    consecutive_failures = 0

                    code_match = re.search(r'```python\s*(.*?)```', response, re.DOTALL)
                    if not code_match:
                        self.log(f"[DOC] ⚠️ {name} — no ```python block in response")
                        continue

                    new_method = code_match.group(1).strip()
                    if not new_method:
                        self.log(f"[DOC] ⚠️ {name} — empty code block")
                        continue

                    new_method = self._fix_bare_docstrings(new_method)

                    for bad, good in replacements.items():
                        new_method = new_method.replace(bad, good)

                    new_method_lines = new_method.splitlines()
                    if not new_method_lines:
                        continue

                    original_indent = len(method_lines[0]) - len(method_lines[0].lstrip()) if method_lines else 0
                    returned_indent = len(new_method_lines[0]) - len(new_method_lines[0].lstrip())

                    if returned_indent != original_indent:
                        delta = original_indent - returned_indent
                        fixed = []
                        for line in new_method_lines:
                            if not line.strip():
                                fixed.append("")
                            elif delta > 0:
                                fixed.append(" " * delta + line)
                            else:
                                strip = min(-delta, len(line) - len(line.lstrip()))
                                fixed.append(line[strip:])
                        new_method_lines = fixed

                    if len(new_method_lines) < len(method_lines) - 2:
                        self.log(f"[DOC] ⚠️ {name} — LLM shortened method suspiciously, skipping")
                        continue
                    if len(new_method_lines) > len(method_lines) + 10:
                        self.log(f"[DOC] ⚠️ {name} — LLM expanded method suspiciously, skipping")
                        continue

                    lines[start:end] = new_method_lines
                    documented_count += 1
                    self.log(f"[DOC] ✅ {name}")

                except Exception as e:
                    self.log(f"[DOC] ⚠️ {name} failed: {e}")
                    continue

        finally:
            self.ai.max_tokens = original_max_tokens

        documented_source = "\n".join(lines)

        for bad, good in replacements.items():
            documented_source = documented_source.replace(bad, good)
        documented_source = documented_source.replace("'''", '"""')

        tmp = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
                f.write(documented_source)
                tmp = f.name
            py_compile.compile(tmp, doraise=True)
        except py_compile.PyCompileError as e:
            return False, None, f"Syntax error after documentation: {e}"
        except OSError as e:
            return False, None, f"File system error during validation: {e}"
        finally:
            if tmp:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

        return True, documented_source, f"Documented {documented_count}/{total} methods."

    def _fix_bare_docstrings(self, source):
        """Wrap any bare docstring lines that are missing triple-quote delimiters."""
        code_keywords = (
            "if ", "for ", "while ", "try:", "return ", "self.",
            "import ", "#", "pass", "raise ", "with ", "assert ",
            "del ", "yield ", "class ", "def ", "async ", '"""', "'''",
            "print(", "super(", "not ", "True", "False", "None",
            "@", "lambda ", "global ", "nonlocal ",
        )
        lines = source.splitlines()
        result = []
        just_after_sig = False
        paren_depth = 0

        for line in lines:
            stripped = line.strip()
            paren_depth += stripped.count("(") - stripped.count(")")
            paren_depth = max(0, paren_depth)

            if stripped.startswith("def ") or stripped.startswith("async def "):
                just_after_sig = False
                result.append(line)
                if paren_depth == 0 and stripped.endswith(":"):
                    just_after_sig = True
                continue

            if paren_depth > 0:
                result.append(line)
                continue

            if not just_after_sig and stripped.endswith(":") and stripped.startswith(")"):
                result.append(line)
                just_after_sig = True
                continue

            if just_after_sig:
                just_after_sig = False
                if stripped and not any(stripped.startswith(k) for k in code_keywords):
                    indent = len(line) - len(line.lstrip())
                    result.append(" " * indent + '"""' + stripped + '"""')
                    self.log(f"[DOC] 🔧 Fixed bare docstring: {stripped[:60]}")
                    continue

            result.append(line)

        return "\n".join(result)