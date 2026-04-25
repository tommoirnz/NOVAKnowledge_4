# latex_window.py — Nova styled LaTeX preview window

import tkinter as tk
import tkinter.font as tkfont
from io import BytesIO
import re
from PIL import Image, ImageTk

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")
matplotlib.rcParams["figure.max_open_warning"] = 0


class LatexWindow(tk.Toplevel):

    SCALE_MIN  = 0.3
    SCALE_MAX  = 3.0
    SCALE_STEP = 0.1
    BASE_W     = 900
    BASE_H     = 700

    def __init__(self, master, log_fn=None,
                 text_family="Segoe UI", text_size=12, math_pt=12):

        super().__init__(master)

        self.title("LaTeX Preview")
        self.protocol("WM_DELETE_WINDOW", self.hide)

        self.colors = {
            "bg":      "#0F1318",
            "panel":   "#0C1219",
            "accent":  "#4A9EFF",
            "text":    "#D4E0F7",
            "border":  "#1E3A5F",
            "toolbar": "#0A0C10",
            "button":  "#1A2035",
        }

        self.configure(bg=self.colors["bg"])
        self.resizable(True, True)

        self.text_family = text_family
        self.text_size   = int(text_size)
        self.math_pt     = int(math_pt)

        self._scale_factor = 1.0
        self._last_text    = ""
        self._img_refs     = []

        # drag state — only used on the toolbar, NOT the whole window
        self._drag_data = {"x": 0, "y": 0}

        self._text_font = tkfont.Font(family=self.text_family, size=self.text_size)

        self._build_toolbar()
        self._build_body()

        self.geometry(f"{self.BASE_W}x{self.BASE_H}")
        self.center_on_screen()

    # ─────────────────────────────────────────────
    # Toolbar
    # ─────────────────────────────────────────────
    def _build_toolbar(self):

        bar = tk.Frame(self, bg=self.colors["toolbar"], height=32)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        bar.bind("<ButtonPress-1>", self._start_drag)
        bar.bind("<B1-Motion>", self._do_drag)

        def btn(text, cmd, side="left", fg=None):
            b = tk.Button(bar, text=text, command=cmd,
                          bg=self.colors["button"],
                          fg=fg or self.colors["text"],
                          relief="flat", padx=8, pady=2)
            b.pack(side=side, padx=3, pady=3)
            return b

        btn("Clear", self.clear)
        btn("Copy", self.copy_raw_latex)
        btn("Refresh", self.refresh_document, fg=self.colors["accent"])

        # Text size
        tk.Label(bar, text="Text:", bg=self.colors["toolbar"],
                 fg=self.colors["text"]).pack(side="left", padx=(10, 2))
        self.text_var = tk.IntVar(value=self.text_size)
        tk.Spinbox(bar, from_=8, to=48, width=4,
                   textvariable=self.text_var,
                   command=self._on_text_size_change).pack(side="left")

        # Math size
        tk.Label(bar, text="Math:", bg=self.colors["toolbar"],
                 fg=self.colors["text"]).pack(side="left", padx=(10, 2))
        self.math_var = tk.IntVar(value=self.math_pt)
        tk.Spinbox(bar, from_=6, to=60, width=4,
                   textvariable=self.math_var,
                   command=self._on_math_size_change).pack(side="left")

        # ── NEW: image padding controls ───────────────────────
        tk.Label(bar, text="Pad:", bg=self.colors["toolbar"],
                 fg=self.colors["text"]).pack(side="left", padx=(10, 2))

        # pad_inches — whitespace inside the PNG itself (0.00 = none, 0.20 = lots)
        self.pad_inches_var = tk.DoubleVar(value=0.02)
        tk.Spinbox(bar, from_=0.0, to=0.30, increment=0.01, width=5,
                   format="%.2f",
                   textvariable=self.pad_inches_var,
                   command=self.refresh_document).pack(side="left")

        # pady — gap between image and surrounding text lines (pixels)
        tk.Label(bar, text="Gap:", bg=self.colors["toolbar"],
                 fg=self.colors["text"]).pack(side="left", padx=(6, 2))
        self.gap_var = tk.IntVar(value=2)
        tk.Spinbox(bar, from_=0, to=20, width=3,
                   textvariable=self.gap_var,
                   command=self.refresh_document).pack(side="left")

        # zoom label
        self.zoom_lbl = tk.Label(bar, text="100%",
                                 bg=self.colors["toolbar"],
                                 fg=self.colors["accent"],
                                 font=("Consolas", 9))
        self.zoom_lbl.pack(side="right", padx=8)

        tk.Label(bar, text="Ctrl+Wheel=zoom",
                 bg=self.colors["toolbar"],
                 fg="#3A4A6A",
                 font=("Segoe UI", 8)).pack(side="right", padx=4)


    # ─────────────────────────────────────────────
    # Body — text widget + scrollbar
    # ─────────────────────────────────────────────
    def _build_body(self):

        # outer border frame
        border = tk.Frame(self, bg=self.colors["border"], padx=1, pady=1)
        border.pack(fill="both", expand=True, padx=6, pady=6)

        inner = tk.Frame(border, bg=self.colors["bg"])
        inner.pack(fill="both", expand=True)

        # scrollbar first so it is always visible
        self._scrollbar = tk.Scrollbar(inner, orient="vertical",
                                        bg=self.colors["button"],
                                        troughcolor=self.colors["bg"],
                                        activebackground=self.colors["accent"])
        self._scrollbar.pack(side="right", fill="y")

        self.textview = tk.Text(
            inner,
            bg=self.colors["panel"],
            fg=self.colors["text"],
            wrap="word",
            relief="flat",
            padx=16,
            pady=12,
            spacing1=4,   # space above each line
            spacing2=6,   # space between wrapped lines
            spacing3=8,   # space below each paragraph
            cursor="arrow",
            insertbackground=self.colors["accent"],
            yscrollcommand=self._scrollbar.set,
        )
        self.textview.pack(side="left", fill="both", expand=True)

        self._scrollbar.config(command=self.textview.yview)

        # configure text tags
        self.textview.tag_configure(
            "body",
            font=self._text_font,
            foreground=self.colors["text"],
            spacing1=2,
            spacing3=6,
        )
        self.textview.tag_configure(
            "math_block",
            justify="center",
            spacing1=10,
            spacing3=10,
        )
        self.textview.tag_configure(
            "math_inline",
            spacing1=2,
            spacing3=2,
        )

        # block editing but allow selection / copy
        self.textview.bind("<Key>",        lambda e: "break")
        self.textview.bind("<MouseWheel>", self._on_mouse_wheel)
        self.textview.bind("<Button-4>",   self._on_mouse_wheel)
        self.textview.bind("<Button-5>",   self._on_mouse_wheel)

    # ─────────────────────────────────────────────
    # Window drag  (toolbar only)
    # ─────────────────────────────────────────────
    def _start_drag(self, e):
        self._drag_data["x"] = e.x_root - self.winfo_x()
        self._drag_data["y"] = e.y_root - self.winfo_y()

    def _do_drag(self, e):
        self.geometry(f"+{e.x_root - self._drag_data['x']}"
                      f"+{e.y_root - self._drag_data['y']}")

    # ─────────────────────────────────────────────
    # Scroll / zoom
    # ─────────────────────────────────────────────
    def _on_mouse_wheel(self, event):
        ctrl = event.state & 0x4
        if ctrl:
            if event.delta > 0 or event.num == 4:
                self._scale_factor = min(self.SCALE_MAX,
                                         self._scale_factor + self.SCALE_STEP)
            else:
                self._scale_factor = max(self.SCALE_MIN,
                                         self._scale_factor - self.SCALE_STEP)
            w = int(self.BASE_W * self._scale_factor)
            h = int(self.BASE_H * self._scale_factor)
            self.geometry(f"{w}x{h}")
            pct = int(self._scale_factor * 100)
            self.zoom_lbl.config(text=f"{pct}%")
            return "break"

        delta = -3 if (event.delta > 0 or event.num == 4) else 3
        self.textview.yview_scroll(delta, "units")
        return "break"

    # ─────────────────────────────────────────────
    # Font / size controls
    # ─────────────────────────────────────────────
    def _on_text_size_change(self):
        self.text_size = self.text_var.get()
        self._text_font.config(size=self.text_size)
        self.textview.tag_configure("body", font=self._text_font)
        # keep math roughly proportional
        self.math_pt = max(8, int(self.text_size * 0.95))
        self.math_var.set(self.math_pt)
        self.refresh_document()

    def _on_math_size_change(self):
        self.math_pt = self.math_var.get()
        self.refresh_document()

    def set_text_font(self, family=None, size=None):
        if family: self.text_family = family
        if size:   self.text_size   = int(size)
        self._text_font.config(family=self.text_family, size=self.text_size)

    def set_math_pt(self, pt):
        self.math_pt = int(pt)

    def refresh_document(self):
        if self._last_text:
            self.show_document(self._last_text)

    # ─────────────────────────────────────────────
    # Rendering engine
    # ─────────────────────────────────────────────
    def render_png_bytes(self, latex, fontsize=None, dpi=180, display=False):
        fontsize = fontsize or self.math_pt
        expr = latex.strip()

        # strip outer delimiters
        for delim in [("$$", "$$"), ("$", "$"), (r"\[", r"\]")]:
            if expr.startswith(delim[0]) and expr.endswith(delim[1]):
                expr = expr[len(delim[0]):-len(delim[1])].strip()
                break

        expr = self._sanitize_latex(expr)  # ← sanitize before rendering

        needs_tex = bool(re.search(
            r"\\boxed|\\begin\{|\\text\{|\\overset|\\underset", expr
        ))

        try:
            return self._render_expr(expr, fontsize, dpi,
                                     use_usetex=needs_tex, display=display)
        except Exception:
            return self._render_expr(expr, fontsize, dpi,
                                     use_usetex=False, display=display)


    def _render_expr(self, latex, fontsize, dpi, use_usetex, display):

        # use the spinbox value — same for block and inline, user controls it
        pad = self.pad_inches_var.get()

        rc = {"text.usetex": bool(use_usetex), "text.color": "white"}
        if use_usetex:
            rc["text.latex.preamble"] = r"\usepackage{amsmath,amssymb}"

        fig = plt.figure(figsize=(1, 1), dpi=dpi, facecolor="none")
        try:
            with matplotlib.rc_context(rc):
                ax = fig.add_axes([0, 0, 1, 1])
                ax.axis("off")
                ax.text(0.5, 0.5, f"${latex}$",
                        ha="center", va="center",
                        fontsize=fontsize, color="white")
                buf = BytesIO()
                fig.savefig(buf, format="png",
                            bbox_inches="tight",
                            pad_inches=pad,
                            transparent=True)
                return buf.getvalue()
        finally:
            plt.close(fig)


    # ─────────────────────────────────────────────
    # Text / math parsing
    # ─────────────────────────────────────────────
    def split_text_math(self, text):
        if not text:
            return []

        # order matters — longer delimiters first
        pattern = re.compile(
            r"""
            (\\begin\{.*?\}.*?\\end\{.*?\}) |   # environments
            \$\$(.+?)\$\$                    |   # $$ display $$
            \\\[(.+?)\\\]                    |   # \[ display \]
            \$(.+?)\$                            # $ inline $
            """,
            re.DOTALL | re.VERBOSE,
        )

        out = []
        idx = 0

        for m in pattern.finditer(text):
            s, e = m.span()
            if s > idx:
                out.append(("text", text[idx:s]))

            raw    = m.group(0)
            expr   = next(g for g in m.groups() if g is not None)
            is_blk = raw.startswith("$$") or raw.startswith(r"\[") \
                     or raw.startswith(r"\begin")

            out.append(("math_block" if is_blk else "math_inline",
                        expr.strip()))
            idx = e

        if idx < len(text):
            out.append(("text", text[idx:]))

        return out

    # ─────────────────────────────────────────────
    # Display
    # ─────────────────────────────────────────────
    def clear(self):
        self.textview.config(state="normal")
        self.textview.delete("1.0", "end")
        self._img_refs.clear()

    def copy_raw_latex(self):
        if self._last_text.strip():
            self.clipboard_clear()
            self.clipboard_append(self._last_text)

    def show_document(self, text):
        self.deiconify()
        self.lift()
        self._last_text = text or ""
        self.clear()
        if not text:
            return
        self._render_blocks(self.split_text_math(text))
        self.textview.see("end")

    def _render_blocks(self, blocks):

        for kind, content in blocks:

            if kind == "text":
                content = re.sub(r'\n{3,}', '\n\n', content)
                self.textview.insert("end", content, "body")

            elif kind == "math_block":
                try:
                    png = self.render_png_bytes(content,
                                                fontsize=self.math_pt + 4,
                                                display=True)
                    img = Image.open(BytesIO(png))
                    photo = ImageTk.PhotoImage(img)
                    self._img_refs.append(photo)
                    gap = self.gap_var.get()
                    self.textview.insert("end", "\n")
                    self.textview.image_create("end", image=photo,
                                               padx=0, pady=gap)
                    self.textview.insert("end", "\n", "math_block")
                except Exception as ex:
                    self._log(f"[latex] block render error: {ex}")
                    self.textview.insert("end", f"\n{content}\n", "body")

            else:
                try:
                    png = self.render_png_bytes(content,
                                                fontsize=self.math_pt,
                                                display=False)
                    img = Image.open(BytesIO(png))
                    photo = ImageTk.PhotoImage(img)
                    self._img_refs.append(photo)
                    gap = max(0, self.gap_var.get() - 2)  # inline needs less
                    self.textview.image_create("end", image=photo,
                                               padx=2, pady=gap)
                except Exception as ex:
                    self._log(f"[latex] inline render error: {ex}")
                    self.textview.insert("end", content, "body")


    def append_document(self, text):
        if not text:
            return
        self._last_text = (self._last_text + "\n" + text) if self._last_text else text
        self.show_document(self._last_text)

    def show(self):
        self.deiconify()
        self.lift()

    def hide(self):
        self.withdraw()

    # ─────────────────────────────────────────────
    def center_on_screen(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _log(self, msg):
        print(msg)

    def _sanitize_latex(self, expr):
        """Fix/strip commands matplotlib mathtext does not support."""

        # Replacements — valid LaTeX but unsupported, swap for equivalent
        replacements = {
            r'\tfrac': r'\frac',
            r'\dfrac': r'\frac',
            r'\textrm': r'\mathrm',
            r'\textit': r'\mathit',
            r'\textbf': r'\mathbf',
        }
        for bad, good in replacements.items():
            expr = expr.replace(bad, good)

        # Strips — commands that have no equivalent, just remove
        strips = [
            r'\displaystyle', r'\textstyle',
            r'\scriptstyle', r'\scriptscriptstyle',
            r'\normalsize', r'\large', r'\small',
            r'\bf', r'\rm', r'\it',
            r'\mathlarger', r'\vspace', r'\hspace',
            r'\noindent', r'\centering',
        ]
        for cmd in strips:
            expr = expr.replace(cmd, '')

        return expr.strip()
