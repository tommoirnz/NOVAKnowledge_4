import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
from datetime import datetime
import os

# ─── Colour palette (matches Nova dark theme) ───────────────────────────────
BG       = "#0D0F14"
BG_PANEL = "#111520"
BG_INPUT = "#141926"
BORDER   = "#2A4A7F"
SEAM     = "#1E3A5F"
BLUE     = "#4A9EFF"
GREEN    = "#2ECC71"
RED      = "#FF4444"
AMBER    = "#F39C12"
VIOLET   = "#9B59B6"
DIM      = "#6B7A99"
FG       = "#D4E0F7"
WHITE    = "#FFFFFF"

TASK_TYPES = [
    "audio_processing", "audio_generation", "control_systems", "plotting",
    "3d_visualization", "machine_learning", "general", "data_processing",
    "web_scraping", "image_processing", "file_handling", "algorithm"
]
ERROR_TYPES = [
    "typeerror", "valueerror", "attributeerror", "keyerror", "indexerror",
    "importerror", "modulenotfounderror", "syntaxerror", "nameerror",
    "runtimeerror", "zerodivisionerror", "filenotfounderror", "overflowerror",
    "best_practice", "warning", "quality_issue", "general"
]


def styled_combo(parent, values, var, width=22):
    s = ttk.Style()
    try:
        s.configure("Dark.TCombobox",
                    fieldbackground=BG_INPUT, background="#2A3A5A",
                    foreground=WHITE, selectbackground="#2A5A9F",
                    selectforeground=WHITE, bordercolor=BLUE,
                    arrowcolor=BLUE, relief="flat")
        s.map("Dark.TCombobox",
              foreground=[("readonly", WHITE)],
              fieldbackground=[("readonly", BG_INPUT)])
    except Exception:
        pass
    cb = ttk.Combobox(parent, textvariable=var, values=values,
                      style="Dark.TCombobox", state="readonly", width=width)
    return cb


class LessonsLearnedManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Lessons Learned Manager")
        self.root.geometry("1200x750")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self._editing_index = None
        self._ignore_listbox = False

        self.load_config()
        self.mistakes_file = os.path.join(self.cache_dir, "mistake_memory.json")
        self.root.title(f"Lessons Learned Manager  —  {self.mistakes_file}")
        self.load_data()
        self._build_ui()
        self._refresh_list()

    # ─── Config / Data ────────────────────────────────────────────────────────

    def load_config(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(script_dir, "config.json"),
            os.path.join(script_dir, "..", "config.json"),
            "C:/Users/OEM/PycharmProjects/AICoder8/config.json",
        ]
        for path in candidates:
            if os.path.exists(path):
                with open(path, "r") as f:
                    cfg = json.load(f)
                self.cache_dir = cfg["cache_directory"]
                return
        messagebox.showerror("Config Not Found", "config.json not found.")
        self.root.destroy()

    def load_data(self):
        try:
            if os.path.exists(self.mistakes_file):
                with open(self.mistakes_file, "r") as f:
                    self.data = json.load(f)
            else:
                self.data = {"mistakes": [], "error_patterns": {}, "last_updated": ""}
        except Exception as e:
            messagebox.showerror("Load Error", str(e))
            self.data = {"mistakes": [], "error_patterns": {}, "last_updated": ""}

    def save_data(self):
        try:
            self.data["last_updated"] = datetime.now().isoformat()
            with open(self.mistakes_file, "w") as f:
                json.dump(self.data, f, indent=2)
            self._set_status(f"Saved — {len(self.data['mistakes'])} lessons total", GREEN)
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    # ─── UI Build ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        hdr = tk.Frame(self.root, bg="#0A0C10", height=36)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="LESSONS LEARNED MANAGER",
                 font=("Consolas", 13, "bold"), bg="#0A0C10", fg=BLUE
                 ).pack(side="left", padx=16, pady=6)
        self.status_lbl = tk.Label(hdr, text="", font=("Consolas", 9),
                                   bg="#0A0C10", fg=GREEN)
        self.status_lbl.pack(side="right", padx=16)

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=10, pady=8)
        body.columnconfigure(0, weight=1, minsize=340)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        self._build_list_panel(body)
        self._build_edit_panel(body)

    # ── LEFT: lesson list ────────────────────────────────────────────────────

    def _build_list_panel(self, parent):
        pnl = tk.Frame(parent, bg=BG_PANEL, bd=1, relief="flat",
                       highlightthickness=1, highlightbackground=SEAM)
        pnl.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        pnl.rowconfigure(1, weight=1)
        pnl.columnconfigure(0, weight=1)

        th = tk.Frame(pnl, bg=BG_PANEL)
        th.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        tk.Label(th, text="ALL LESSONS", font=("Consolas", 10, "bold"),
                 bg=BG_PANEL, fg=BLUE).pack(side="left")
        self.count_lbl = tk.Label(th, text="", font=("Consolas", 9),
                                  bg=BG_PANEL, fg=DIM)
        self.count_lbl.pack(side="right")

        lf = tk.Frame(pnl, bg=BG_PANEL)
        lf.grid(row=1, column=0, sticky="nsew", padx=6, pady=4)
        lf.rowconfigure(0, weight=1)
        lf.columnconfigure(0, weight=1)

        sb = tk.Scrollbar(lf, bg=BG_PANEL)
        sb.grid(row=0, column=1, sticky="ns")

        self.lesson_lb = tk.Listbox(
            lf, yscrollcommand=sb.set,
            bg="#0C1219", fg=FG, selectbackground="#1A4A7F",
            selectforeground=WHITE, font=("Consolas", 9),
            activestyle="none", borderwidth=0, highlightthickness=0,
            relief="flat"
        )
        self.lesson_lb.grid(row=0, column=0, sticky="nsew")
        sb.config(command=self.lesson_lb.yview)
        self.lesson_lb.bind("<<ListboxSelect>>", self._on_select)

        bf = tk.Frame(pnl, bg=BG_PANEL)
        bf.grid(row=2, column=0, sticky="ew", padx=6, pady=6)
        self._btn(bf, "＋  NEW", GREEN,   self._new_lesson).pack(side="left", padx=3)
        self._btn(bf, "✕  DELETE", RED,   self._delete_selected).pack(side="left", padx=3)

    # ── RIGHT: edit panel ────────────────────────────────────────────────────

    def _build_edit_panel(self, parent):
        pnl = tk.Frame(parent, bg=BG_PANEL, bd=1, relief="flat",
                       highlightthickness=1, highlightbackground=SEAM)
        pnl.grid(row=0, column=1, sticky="nsew")
        pnl.columnconfigure(1, weight=1)

        self.panel_title = tk.Label(
            pnl, text="NEW LESSON", font=("Consolas", 10, "bold"),
            bg=BG_PANEL, fg=BLUE, anchor="w"
        )
        self.panel_title.grid(row=0, column=0, columnspan=2,
                              sticky="ew", padx=12, pady=(10, 6))

        row_cfg = dict(sticky="ew", padx=12, pady=3)

        # Task
        self._lbl(pnl, "Task").grid(row=1, column=0, sticky="w", padx=12)
        self.task_var = tk.StringVar()
        self.task_entry = tk.Entry(pnl, textvariable=self.task_var,
                                   bg=BG_INPUT, fg=FG, insertbackground=BLUE,
                                   relief="flat", font=("Consolas", 10))
        self.task_entry.grid(row=1, column=1, **row_cfg)

        # Task Type + Error Type side by side
        combo_row = tk.Frame(pnl, bg=BG_PANEL)
        combo_row.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=3)
        combo_row.columnconfigure(1, weight=1)
        combo_row.columnconfigure(3, weight=1)

        # Task Type + Error Type side by side
        combo_row = tk.Frame(pnl, bg=BG_PANEL)
        combo_row.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=3)
        combo_row.columnconfigure(1, weight=1)
        combo_row.columnconfigure(3, weight=1)

        self._lbl(combo_row, "Task Type").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.task_type_var = tk.StringVar(value="")
        task_menu = tk.OptionMenu(combo_row, self.task_type_var, *TASK_TYPES)
        task_menu.config(bg=BG_INPUT, fg=FG, activebackground=SEAM, activeforeground=WHITE,
                         relief="flat", font=("Consolas", 10), width=22, highlightthickness=0)
        task_menu["menu"].config(bg=BG_INPUT, fg=FG, activebackground="#1A4A7F",
                                 activeforeground=WHITE, font=("Consolas", 9))
        task_menu.grid(row=0, column=1, sticky="w")

        self._lbl(combo_row, "Error Type").grid(row=0, column=2, sticky="w", padx=(16, 6))
        self.error_type_var = tk.StringVar(value="")
        error_menu = tk.OptionMenu(combo_row, self.error_type_var, *ERROR_TYPES)
        error_menu.config(bg=BG_INPUT, fg=FG, activebackground=SEAM, activeforeground=WHITE,
                          relief="flat", font=("Consolas", 10), width=22, highlightthickness=0)
        error_menu["menu"].config(bg=BG_INPUT, fg=FG, activebackground="#1A4A7F",
                                  activeforeground=WHITE, font=("Consolas", 9))
        error_menu.grid(row=0, column=3, sticky="w")

        # Libraries
        self._lbl(pnl, "Libraries  (comma-separated)").grid(
            row=3, column=0, columnspan=2, sticky="w", padx=12, pady=(6, 0))
        self.libs_entry = tk.Entry(pnl, bg=BG_INPUT, fg=FG, insertbackground=BLUE,
                                   relief="flat", font=("Consolas", 10))
        self.libs_entry.grid(row=4, column=0, columnspan=2, **row_cfg)

        # Lesson
        self._lbl(pnl, "Lesson").grid(row=5, column=0, columnspan=2,
                                       sticky="w", padx=12, pady=(6, 0))
        self.lesson_txt = scrolledtext.ScrolledText(
            pnl, height=9, bg=BG_INPUT, fg=FG,
            insertbackground=BLUE, relief="flat",
            font=("Consolas", 10), wrap="word"
        )
        self.lesson_txt.grid(row=6, column=0, columnspan=2, **row_cfg)

        # Error Snippet
        self._lbl(pnl, "Error Snippet  (optional)").grid(
            row=7, column=0, columnspan=2, sticky="w", padx=12, pady=(6, 0))
        self.snippet_txt = scrolledtext.ScrolledText(
            pnl, height=4, bg=BG_INPUT, fg=FG,
            insertbackground=BLUE, relief="flat",
            font=("Consolas", 10), wrap="word"
        )
        self.snippet_txt.grid(row=8, column=0, columnspan=2, **row_cfg)

        # Buttons
        bf = tk.Frame(pnl, bg=BG_PANEL)
        bf.grid(row=9, column=0, columnspan=2, sticky="ew", padx=12, pady=10)
        self._btn(bf, "💾  SAVE", GREEN,  self._save_lesson).pack(side="left", padx=4)
        self._btn(bf, "✕  CLEAR", AMBER, self._clear_form).pack(side="left", padx=4)

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _on_combo_selected(self, _=None):
        self._ignore_listbox = True
        self.root.after(500, lambda: setattr(self, '_ignore_listbox', False))


    def _lbl(self, parent, text):
        return tk.Label(parent, text=text, font=("Rajdhani", 10),
                        bg=BG_PANEL, fg=DIM)

    def _btn(self, parent, text, colour, cmd):
        return tk.Button(
            parent, text=text, command=cmd,
            bg=BG_PANEL, fg=colour, activeforeground=WHITE,
            activebackground=SEAM, relief="flat",
            font=("Rajdhani", 10, "bold"),
            padx=10, pady=4, cursor="hand2",
            highlightthickness=1, highlightbackground=colour
        )

    def _set_status(self, msg, colour=GREEN):
        self.status_lbl.config(text=msg, fg=colour)

    # ─── List management ──────────────────────────────────────────────────────

    def _refresh_list(self, select_index=None):
        self.lesson_lb.delete(0, tk.END)
        mistakes = self.data.get("mistakes", [])
        for i, m in enumerate(mistakes):
            task_type = m.get("task_type", "?")
            error_type = m.get("error_type", "?")
            task = m.get("task", "")[:42]
            label = f"  #{i+1:>2}  [{task_type} / {error_type}]  {task}"
            self.lesson_lb.insert(tk.END, label)
            bg = "#0C1219" if i % 2 == 0 else "#0F1520"
            self.lesson_lb.itemconfig(i, bg=bg)

        count = len(mistakes)
        self.count_lbl.config(text=f"{count} lesson{'s' if count != 1 else ''}")

        if select_index is not None:
            self.lesson_lb.selection_set(select_index)
            self.lesson_lb.see(select_index)
            self._load_into_form(select_index)

    def _on_select(self, _=None):
        if self._ignore_listbox:
            return
        sel = self.lesson_lb.curselection()
        if not sel:
            return
        self._load_into_form(sel[0])

    def _load_into_form(self, index):
        m = self.data["mistakes"][index]
        self._editing_index = index
        self.panel_title.config(text=f"EDITING LESSON #{index + 1}")

        self.task_var.set(m.get("task", ""))
        self.task_type_var.set(m.get("task_type", ""))
        self.error_type_var.set(m.get("error_type", ""))

        self.libs_entry.delete(0, tk.END)
        self.libs_entry.insert(0, ", ".join(m.get("libraries", [])))

        self.lesson_txt.delete("1.0", tk.END)
        self.lesson_txt.insert("1.0", m.get("lesson", ""))

        self.snippet_txt.delete("1.0", tk.END)
        self.snippet_txt.insert("1.0", m.get("error_snippet", ""))

        self._set_status(f"Editing lesson #{index + 1}", AMBER)

    # ─── Actions ──────────────────────────────────────────────────────────────

    def _new_lesson(self):
        self._editing_index = None
        self.lesson_lb.selection_clear(0, tk.END)
        self._clear_form()
        self.panel_title.config(text="NEW LESSON")
        self._set_status("Ready to add a new lesson", BLUE)
        self.task_entry.focus()

    def _clear_form(self):
        self.task_var.set("")
        self.task_type_var.set("")
        self.error_type_var.set("")
        self.libs_entry.delete(0, tk.END)
        self.lesson_txt.delete("1.0", tk.END)
        self.snippet_txt.delete("1.0", tk.END)

    def _save_lesson(self):
        task = self.task_var.get().strip()
        task_type = self.task_type_var.get().strip()
        error_type = self.error_type_var.get().strip()
        lesson = self.lesson_txt.get("1.0", tk.END).strip()

        if not task:
            messagebox.showwarning("Missing", "Task is required."); return
        if not task_type:
            messagebox.showwarning("Missing", "Task Type is required."); return
        if not error_type:
            messagebox.showwarning("Missing", "Error Type is required."); return
        if not lesson:
            messagebox.showwarning("Missing", "Lesson is required."); return

        libs_raw = self.libs_entry.get().strip()
        libraries = [l.strip() for l in libs_raw.split(",") if l.strip()]
        snippet = self.snippet_txt.get("1.0", tk.END).strip()

        entry = {
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "task_type": task_type,
            "error_type": error_type,
            "libraries": libraries,
            "lesson": lesson,
            "error_snippet": snippet,
        }

        if self._editing_index is not None:
            entry["timestamp"] = self.data["mistakes"][self._editing_index].get(
                "timestamp", entry["timestamp"])
            self.data["mistakes"][self._editing_index] = entry
            saved_index = self._editing_index
            self._set_status(f"Lesson #{saved_index + 1} updated", GREEN)
        else:
            self.data["mistakes"].append(entry)
            saved_index = len(self.data["mistakes"]) - 1
            self._set_status(f"Lesson #{saved_index + 1} added", GREEN)

        self.save_data()
        self._refresh_list(select_index=saved_index)

    def _delete_selected(self):
        sel = self.lesson_lb.curselection()
        if not sel:
            messagebox.showinfo("Nothing selected", "Click a lesson in the list first.")
            return
        index = sel[0]
        task = self.data["mistakes"][index].get("task", "")[:60]
        if not messagebox.askyesno("Delete?",
                                   f"Delete lesson #{index + 1}?\n\n{task}"):
            return
        self.data["mistakes"].pop(index)
        self.save_data()
        self._editing_index = None
        self._clear_form()
        self.panel_title.config(text="NEW LESSON")
        self._refresh_list()
        self._set_status(f"Lesson #{index + 1} deleted", RED)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = LessonsLearnedManager(root)
    root.mainloop()