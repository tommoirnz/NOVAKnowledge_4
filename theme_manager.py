import tkinter as tk

# ─────────────────────────────────────────────
# THEMES
# ─────────────────────────────────────────────
THEMES = {
    "Nova Dark": {
        "BG_ROOT": "#0D0F14", "BG_LEFT": "#111520", "BG_RIGHT": "#0F1318",
        "BG_HEADER": "#0A0C10", "BG_CONSOLE": "#080C12", "BG_INPUT": "#141926",
        "SEAM": "#1E3A5F", "BORDER": "#2A4A7F", "ELECTRIC_BLUE": "#4A9EFF",
        "PLATINUM": "#C8D6E5", "DIM_TEXT": "#6B7A99", "TERMINAL_GREEN": "#39FF14",
        "GREEN_GLOW": "#2ECC71", "FG_MAIN": "#D4E0F7", "FG_DIM": "#3A4A6A",
        "FG_CODE": "#C8D6E5", "CODE_BG": "#1A1F2E", "AMBER": "#F39C12",
        "ACCENT": "#4A9EFF",
    },
    "Midnight Purple": {
        "BG_ROOT": "#0D0B14", "BG_LEFT": "#130F20", "BG_RIGHT": "#100D1A",
        "BG_HEADER": "#0A0810", "BG_CONSOLE": "#08060F", "BG_INPUT": "#1A1530",
        "SEAM": "#3A1F6F", "BORDER": "#5A2FAF", "ELECTRIC_BLUE": "#A070FF",
        "PLATINUM": "#D8C8F0", "DIM_TEXT": "#7A6A99", "TERMINAL_GREEN": "#BB86FC",
        "GREEN_GLOW": "#BB86FC", "FG_MAIN": "#E8D8FF", "FG_DIM": "#4A3A6A",
        "FG_CODE": "#D8C8F0", "CODE_BG": "#1A1530", "AMBER": "#CF6679",
        "ACCENT": "#A070FF",
    },
    "Emerald Terminal": {
        "BG_ROOT": "#020D08", "BG_LEFT": "#041410", "BG_RIGHT": "#030F0A",
        "BG_HEADER": "#020A06", "BG_CONSOLE": "#010806", "BG_INPUT": "#071A10",
        "SEAM": "#0F4A2F", "BORDER": "#1A7A4F", "ELECTRIC_BLUE": "#00FF88",
        "PLATINUM": "#B8E8C8", "DIM_TEXT": "#3A6A4A", "TERMINAL_GREEN": "#39FF14",
        "GREEN_GLOW": "#00FF88", "FG_MAIN": "#C8F0D8", "FG_DIM": "#1A4A2A",
        "FG_CODE": "#B8E8C8", "CODE_BG": "#051208", "AMBER": "#FFD700",
        "ACCENT": "#00FF88",
    },
    "Amber Cockpit": {
        "BG_ROOT": "#100800", "BG_LEFT": "#180C00", "BG_RIGHT": "#120A00",
        "BG_HEADER": "#0C0600", "BG_CONSOLE": "#080400", "BG_INPUT": "#1E1000",
        "SEAM": "#5A3000", "BORDER": "#8A5000", "ELECTRIC_BLUE": "#FFB020",
        "PLATINUM": "#FFE0A0", "DIM_TEXT": "#806020", "TERMINAL_GREEN": "#FFA000",
        "GREEN_GLOW": "#FFC040", "FG_MAIN": "#FFE8B0", "FG_DIM": "#503800",
        "FG_CODE": "#FFE0A0", "CODE_BG": "#160C00", "AMBER": "#FF6020",
        "ACCENT": "#FFB020",
    },
    "Ice Blue": {
        "BG_ROOT": "#08101A", "BG_LEFT": "#0C1825", "BG_RIGHT": "#0A1420",
        "BG_HEADER": "#060C14", "BG_CONSOLE": "#040A10", "BG_INPUT": "#101E30",
        "SEAM": "#1A4A7A", "BORDER": "#2A6AAA", "ELECTRIC_BLUE": "#60C8FF",
        "PLATINUM": "#C0E8FF", "DIM_TEXT": "#5080A0", "TERMINAL_GREEN": "#40FFCC",
        "GREEN_GLOW": "#40FFCC", "FG_MAIN": "#D0F0FF", "FG_DIM": "#2A5070",
        "FG_CODE": "#C0E8FF", "CODE_BG": "#0C1A28", "AMBER": "#FFB060",
        "ACCENT": "#60C8FF",
    },
    "Red Alert": {
        "BG_ROOT": "#100505", "BG_LEFT": "#180808", "BG_RIGHT": "#120606",
        "BG_HEADER": "#0C0404", "BG_CONSOLE": "#080202", "BG_INPUT": "#1E0A0A",
        "SEAM": "#5A1010", "BORDER": "#8A2020", "ELECTRIC_BLUE": "#FF5050",
        "PLATINUM": "#FFD0D0", "DIM_TEXT": "#805050", "TERMINAL_GREEN": "#FF3030",
        "GREEN_GLOW": "#FF6060", "FG_MAIN": "#FFE0E0", "FG_DIM": "#502020",
        "FG_CODE": "#FFD0D0", "CODE_BG": "#160606", "AMBER": "#FFA040",
        "ACCENT": "#FF5050",
    },
"Cyberpunk": {
        "BG_ROOT":        "#0A0015",
        "BG_LEFT":        "#0F0020",
        "BG_RIGHT":       "#0C0018",
        "BG_HEADER":      "#07000F",
        "BG_CONSOLE":     "#050010",
        "BG_INPUT":       "#150025",
        "SEAM":           "#FF00FF",
        "BORDER":         "#CC00CC",
        "ELECTRIC_BLUE":  "#FF00FF",
        "PLATINUM":       "#FFD0FF",
        "DIM_TEXT":       "#996699",
        "TERMINAL_GREEN": "#00FFAA",
        "GREEN_GLOW":     "#00FFAA",
        "FG_MAIN":        "#FFE0FF",
        "FG_DIM":         "#4A1A4A",
        "FG_CODE":        "#FFD0FF",
        "CODE_BG":        "#0F0018",
        "AMBER":          "#FFAA00",
        "ACCENT":         "#FF00FF",
    },
    "Deep Ocean": {
        "BG_ROOT":        "#000A1A",
        "BG_LEFT":        "#000F22",
        "BG_RIGHT":       "#000C1E",
        "BG_HEADER":      "#00070F",
        "BG_CONSOLE":     "#000510",
        "BG_INPUT":       "#001428",
        "SEAM":           "#0077FF",
        "BORDER":         "#0055CC",
        "ELECTRIC_BLUE":  "#00AAFF",
        "PLATINUM":       "#C0E8FF",
        "DIM_TEXT":       "#336688",
        "TERMINAL_GREEN": "#00FFD0",
        "GREEN_GLOW":     "#00FFD0",
        "FG_MAIN":        "#D0F0FF",
        "FG_DIM":         "#0A2A3A",
        "FG_CODE":        "#B0DFFF",
        "CODE_BG":        "#000E20",
        "AMBER":          "#FF9900",
        "ACCENT":         "#0099FF",
    },
    "Ember Forge": {
        "BG_ROOT":        "#120500",
        "BG_LEFT":        "#1A0800",
        "BG_RIGHT":       "#160600",
        "BG_HEADER":      "#0A0300",
        "BG_CONSOLE":     "#080200",
        "BG_INPUT":       "#200A00",
        "SEAM":           "#FF4400",
        "BORDER":         "#CC3300",
        "ELECTRIC_BLUE":  "#FF6600",
        "PLATINUM":       "#FFD8B0",
        "DIM_TEXT":       "#885533",
        "TERMINAL_GREEN": "#FFCC00",
        "GREEN_GLOW":     "#FFCC00",
        "FG_MAIN":        "#FFE8D0",
        "FG_DIM":         "#3A1500",
        "FG_CODE":        "#FFD0A0",
        "CODE_BG":        "#180700",
        "AMBER":          "#FF8800",
        "ACCENT":         "#FF4400",
    },
    "Toxic Wasteland": {
        "BG_ROOT":        "#050F00",
        "BG_LEFT":        "#081500",
        "BG_RIGHT":       "#061200",
        "BG_HEADER":      "#030A00",
        "BG_CONSOLE":     "#020800",
        "BG_INPUT":       "#0A1A00",
        "SEAM":           "#44FF00",
        "BORDER":         "#33CC00",
        "ELECTRIC_BLUE":  "#88FF00",
        "PLATINUM":       "#D0FFB0",
        "DIM_TEXT":       "#447722",
        "TERMINAL_GREEN": "#00FF88",
        "GREEN_GLOW":     "#00FF88",
        "FG_MAIN":        "#E0FFD0",
        "FG_DIM":         "#0F2A00",
        "FG_CODE":        "#CCFF99",
        "CODE_BG":        "#071200",
        "AMBER":          "#AAFF00",
        "ACCENT":         "#44FF00",
    },
    "Void Specter": {
        "BG_ROOT":        "#080808",
        "BG_LEFT":        "#0D0D0D",
        "BG_RIGHT":       "#0A0A0A",
        "BG_HEADER":      "#050505",
        "BG_CONSOLE":     "#030303",
        "BG_INPUT":       "#121212",
        "SEAM":           "#AA88FF",
        "BORDER":         "#7755CC",
        "ELECTRIC_BLUE":  "#BB99FF",
        "PLATINUM":       "#E8E0FF",
        "DIM_TEXT":       "#554477",
        "TERMINAL_GREEN": "#88FFCC",
        "GREEN_GLOW":     "#88FFCC",
        "FG_MAIN":        "#F0EEFF",
        "FG_DIM":         "#1A1030",
        "FG_CODE":        "#D8CCFF",
        "CODE_BG":        "#0C0C14",
        "AMBER":          "#FFBB44",
        "ACCENT":         "#9966FF",
    },
}

# Local font definitions — avoids importing from nova_assistant
_F_TITLE  = ("Rajdhani", 13, "bold")
_F_SMALL  = ("Rajdhani", 10)
_F_TINY   = ("Rajdhani", 9)


# ─────────────────────────────────────────────
# THEME MANAGER
# ─────────────────────────────────────────────
class ThemeManager:
    """Applies themes to a running Nova Assistant instance."""

    def __init__(self, app, target_module):
        self.app = app
        self.module = target_module   # nova_assistant module — so we can update its globals
        self.current = "Nova Dark"

    def apply(self, name):
        if name not in THEMES:
            return
        self.current = name
        t = THEMES[name]

        for key, val in t.items():
            if hasattr(self.module, key):
                setattr(self.module, key, val)

        self._recolour(self.app.root, t)

        # ← ADD: explicitly recolour all registered seam frames
        for frame in getattr(self.app, '_seam_frames', []):
            try:
                frame.configure(bg=t["SEAM"])
            except Exception:
                pass

        try:
            self.app._draw_send_btn(False)
            self.app._draw_clear_btn(False)
            self.app._draw_halt_btn(False)
           # self.app._draw_globe(False)
            self.app._draw_tts_btn()
        except Exception:
            pass


    def _recolour(self, widget, t):
        """Walk every widget and map its colour to the new theme by luminance."""
        try:
            bg = widget.cget("bg")
            if bg and bg.startswith("#"):
                lum = self._luminance(bg)
                if lum < 0.05:
                    widget.configure(bg=t["BG_ROOT"])
                elif lum < 0.10:
                    widget.configure(bg=t["BG_HEADER"])
                elif lum < 0.14:
                    widget.configure(bg=t["BG_LEFT"])
                elif lum < 0.18:
                    widget.configure(bg=t["BG_RIGHT"])
                elif lum < 0.25:
                    widget.configure(bg=t["BG_INPUT"])
                elif lum < 0.35:
                    widget.configure(bg=t["CODE_BG"])
        except Exception:
            pass

        try:
            fg = widget.cget("fg")
            if fg and fg.startswith("#"):
                lum = self._luminance(fg)
                if lum > 0.70:
                    widget.configure(fg=t["FG_MAIN"])
                elif lum > 0.40:
                    widget.configure(fg=t["ELECTRIC_BLUE"])
                elif lum > 0.15:
                    widget.configure(fg=t["DIM_TEXT"])
        except Exception:
            pass

        for child in widget.winfo_children():
            self._recolour(child, t)

    @staticmethod
    def _luminance(hex_colour):
        """Perceptual luminance 0–1 from a hex colour string."""
        try:
            h = hex_colour.lstrip("#")
            if len(h) == 3:
                h = "".join(c * 2 for c in h)
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return (0.299 * r + 0.587 * g + 0.114 * b) / 255
        except Exception:
            return 0.0


# ─────────────────────────────────────────────
# THEME PICKER WINDOW
# ─────────────────────────────────────────────
class ThemePicker(tk.Toplevel):
    """Floating palette picker window."""

    def __init__(self, parent, theme_manager):
        super().__init__(parent)
        self.tm = theme_manager
        self.title("Colour Theme")
        self.configure(bg="#0D0F14")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        tk.Label(
            self, text="COLOUR THEME", font=_F_TITLE,
            bg="#0D0F14", fg="#4A9EFF"
        ).pack(pady=(12, 6))

        grid = tk.Frame(self, bg="#0D0F14")
        grid.pack(padx=16, pady=6)

        col = 0
        row = 0
        for name, colours in THEMES.items():
            self._swatch(grid, name, colours, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

        tk.Button(
            self, text="Close", command=self.destroy,
            bg="#1A2035", fg="#6B7A99",
            relief="flat", font=_F_SMALL,
            padx=12, pady=4
        ).pack(pady=(6, 12))

        # Centre over parent window
        self.update_idletasks()
        px = parent.winfo_x() + parent.winfo_width()  // 2 - self.winfo_width()  // 2
        py = parent.winfo_y() + 60
        self.geometry(f"+{px}+{py}")

    def _swatch(self, parent, name, colours, row, col):
        """Build one theme swatch with a mini preview."""
        frame = tk.Frame(parent, bg="#1A2035", padx=2, pady=2)
        frame.grid(row=row, column=col, padx=6, pady=6)

        preview = tk.Canvas(
            frame, width=160, height=44,
            bg=colours["BG_ROOT"],
            highlightthickness=1,
            highlightbackground=colours["SEAM"]
        )
        preview.grid(row=0, column=0)

        # Mini left panel strip
        preview.create_rectangle(0, 0, 52, 44, fill=colours["BG_LEFT"], outline="")
        # Mini right panel
        preview.create_rectangle(52, 0, 160, 44, fill=colours["BG_RIGHT"], outline="")
        # Accent bar at bottom
        preview.create_rectangle(0, 40, 160, 44, fill=colours["ELECTRIC_BLUE"], outline="")
        # Seam line
        preview.create_line(52, 0, 52, 44, fill=colours["SEAM"])
        # Theme name
        preview.create_text(
            106, 14, text=name,
            fill=colours["FG_MAIN"], font=("Rajdhani", 9, "bold")
        )
        # Accent sample text
        preview.create_text(
            106, 28, text="Nova Assistant",
            fill=colours["ACCENT"], font=("Rajdhani", 8)
        )

        # Active indicator label below swatch
        indicator = tk.Label(
            frame,
            text="✓ Active" if name == self.tm.current else "   ",
            font=_F_TINY,
            bg="#1A2035",
            fg=colours["GREEN_GLOW"],
            width=18
        )
        indicator.grid(row=1, column=0, pady=(2, 0))

        def _select(n=name, ind=indicator):
            self.tm.apply(n)
            # Clear all indicators then set this one
            for cell in parent.winfo_children():
                for child in cell.winfo_children():
                    if isinstance(child, tk.Label):
                        child.config(text="   ")
            ind.config(text="✓ Active")

        preview.bind("<Button-1>", lambda e, fn=_select: fn())
        preview.bind(
            "<Enter>",
            lambda e, p=preview, c=colours:
                p.configure(highlightbackground=c["ELECTRIC_BLUE"], highlightthickness=2)
        )
        preview.bind(
            "<Leave>",
            lambda e, p=preview, c=colours:
                p.configure(highlightbackground=c["SEAM"], highlightthickness=1)
        )