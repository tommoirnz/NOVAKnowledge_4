# code_display.py
import tkinter as tk

# ─────────────────────────────────────────────
# COLOUR PALETTE
# ─────────────────────────────────────────────
BG_ROOT = "#0D0F14"
BG_RIGHT = "#0F1318"
ELECTRIC_BLUE = "#4A9EFF"
DIM_TEXT = "#6B7A99"
WHITE = "#FFFFFF"
FG_CODE = "#C8D6E5"
CODE_BG = "#1A1F2E"
CODE_BORDER = "#2A3A5A"

F_RAJ_SM = ("Rajdhani", 10)
F_RAJ_BTN = ("Rajdhani", 12, "bold")
F_COURIER = ("Courier New", 10)


class CodeDisplay:
    """
    A specialized widget for displaying code with syntax highlighting,
    line numbers, and easy copying. Can be embedded in any tkinter frame.
    """

    def __init__(self, parent, bg_color=BG_RIGHT, **kwargs):
        self.parent = parent
        self.bg_color = bg_color
        self.current_code = ""

        # Outer frame with border
        self.frame = tk.Frame(parent, bg=CODE_BORDER, padx=2, pady=2)

        # Header bar
        self.header = tk.Frame(self.frame, bg=CODE_BG, height=28)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        self.lang_label = tk.Label(
            self.header,
            text="🐍 Python",
            bg=CODE_BG,
            fg=ELECTRIC_BLUE,
            font=F_RAJ_SM
        )
        self.lang_label.pack(side="left", padx=8, pady=4)

        self.copy_btn = tk.Button(
            self.header,
            text="📋 Copy",
            bg="#2A3A5A",
            fg=WHITE,
            font=F_RAJ_SM,
            relief="flat",
            cursor="hand2",
            command=self._copy_code
        )
        self.copy_btn.pack(side="right", padx=8, pady=2)

        # Line number canvas
        self.line_numbers = tk.Canvas(
            self.frame,
            width=45,
            bg=CODE_BG,
            highlightthickness=0
        )
        self.line_numbers.pack(side="left", fill="y")

        # Code text widget
        self.text = tk.Text(
            self.frame,
            bg=CODE_BG,
            fg=FG_CODE,
            font=F_COURIER,
            wrap="none",
            relief="flat",
            borderwidth=0,
            padx=5,
            pady=5,
            height=20,
            **kwargs
        )
        self.text.pack(side="left", fill="both", expand=True)

        # Scrollbars
        self.scrollbar_y = tk.Scrollbar(self.frame, orient="vertical")
        self.scrollbar_y.pack(side="right", fill="y")
        self.scrollbar_x = tk.Scrollbar(self.frame, orient="horizontal")
        self.scrollbar_x.pack(side="bottom", fill="x")

        self.scrollbar_y.config(command=self.text.yview)
        self.scrollbar_x.config(command=self.text.xview)
        self.text.config(
            yscrollcommand=self._on_text_scroll_y,
            xscrollcommand=self.scrollbar_x.set
        )

        # Configure syntax tags
        self._configure_tags()

        # Bindings
        self.text.bind("<MouseWheel>", self._on_mousewheel)
        self.text.bind("<Control-c>", self._copy_selection)
        self.text.bind("<Control-C>", self._copy_selection)
        self.text.bind("<Configure>", lambda e: self._update_line_numbers())
        self.text.bind("<ButtonRelease-1>", lambda e: self._update_line_numbers())
        self.text.bind("<KeyRelease>", lambda e: self._update_line_numbers())

        # Context menu
        self.context_menu = tk.Menu(self.text, tearoff=0, bg=CODE_BG, fg=WHITE)
        self.context_menu.add_command(label="Copy", command=self._copy_code)
        self.context_menu.add_command(label="Copy with line numbers",
                                      command=self._copy_with_line_numbers)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Select All", command=self._select_all)
        self.text.bind("<Button-3>", self._show_context_menu)

    def _configure_tags(self):
        self.text.tag_configure("comment",   foreground="#6A9955")
        self.text.tag_configure("string",    foreground="#CE9178")
        self.text.tag_configure("keyword",   foreground="#569CD6")
        self.text.tag_configure("function",  foreground="#DCDCAA")
        self.text.tag_configure("number",    foreground="#B5CEA8")
        self.text.tag_configure("decorator", foreground="#C586C0")

    def _on_mousewheel(self, event):
        self.text.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _on_text_scroll_y(self, *args):
        self.scrollbar_y.set(*args)
        self._update_line_numbers()

    def _update_line_numbers(self):
        self.line_numbers.delete("all")
        i = self.text.index("@0,0")
        while True:
            dline = self.text.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.line_numbers.create_text(
                40, y, anchor="ne",
                text=linenum,
                fill=DIM_TEXT,
                font=F_COURIER
            )
            i = self.text.index(f"{i}+1line")

    def set_code(self, code, language="python"):
        self.current_code = code

        lang_icons = {
            "python":     "🐍 Python",
            "javascript": "📜 JavaScript",
            "html":       "🌐 HTML",
            "css":        "🎨 CSS",
            "bash":       "🖥️ Bash",
            "default":    "📄 Code"
        }
        self.lang_label.config(
            text=lang_icons.get(language.lower(), lang_icons["default"])
        )

        self.text.config(state="normal")
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", code)
        self._apply_syntax_highlighting()
        self._update_line_numbers()
        self.text.config(state="disabled")

    def get_code(self):
        """Get current code content"""
        return self.text.get("1.0", tk.END).strip()

    def set_editable(self, editable=True):
        """Toggle whether the code can be edited"""
        self.text.config(state="normal" if editable else "disabled")

    def _apply_syntax_highlighting(self):
        keywords = [
            "and", "as", "assert", "async", "await", "break", "class",
            "continue", "def", "del", "elif", "else", "except", "False",
            "finally", "for", "from", "global", "if", "import", "in", "is",
            "lambda", "None", "nonlocal", "not", "or", "pass", "raise",
            "return", "True", "try", "while", "with", "yield"
        ]

        for tag in ["comment", "string", "keyword"]:
            self.text.tag_remove(tag, "1.0", tk.END)

        for keyword in keywords:
            start = "1.0"
            while True:
                pos = self.text.search(
                    r'\m' + keyword + r'\M', start, tk.END, regexp=True
                )
                if not pos:
                    break
                end = f"{pos}+{len(keyword)}c"
                self.text.tag_add("keyword", pos, end)
                start = end

        start = "1.0"
        while True:
            pos = self.text.search(r'^#', start, tk.END, regexp=True)
            if not pos:
                break
            end = f"{pos} lineend"
            self.text.tag_add("comment", pos, end)
            line = int(pos.split('.')[0])
            start = f"{line + 1}.0"

    def _copy_code(self):
        self.parent.clipboard_clear()
        self.parent.clipboard_append(self.current_code)
        self.copy_btn.config(text="✓ Copied!", bg="#27ae60")
        self.parent.after(1500, lambda: self.copy_btn.config(
            text="📋 Copy", bg="#2A3A5A"
        ))

    def _copy_selection(self, event=None):
        try:
            selected = self.text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.parent.clipboard_clear()
            self.parent.clipboard_append(selected)
        except tk.TclError:
            pass
        return "break"

    def _copy_with_line_numbers(self):
        lines = self.current_code.split("\n")
        numbered = "\n".join(f"{i + 1:4d} {l}" for i, l in enumerate(lines))
        self.parent.clipboard_clear()
        self.parent.clipboard_append(numbered)

    def _select_all(self):
        self.text.tag_add(tk.SEL, "1.0", tk.END)
        self.text.mark_set(tk.INSERT, "1.0")
        self.text.see(tk.INSERT)
        return "break"

    def _show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def pack(self, **kwargs):
        kwargs.setdefault("fill", "both")
        kwargs.setdefault("expand", True)
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

    def pack_forget(self):
        self.frame.pack_forget()

    def destroy(self):
        self.frame.destroy()