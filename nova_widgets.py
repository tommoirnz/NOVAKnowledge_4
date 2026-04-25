"""
nova_widgets.py — Reusable UI widgets for Nova Assistant.

Currently contains:
    _CanvasTooltip — lightweight tooltip for tk.Canvas widgets.

Usage:
    from nova_widgets import _CanvasTooltip

    _CanvasTooltip(
        canvas,
        text="Tooltip text here",
        bg="#1A3A2E",
        fg="#FFD700",
        border_colour="#2ECC71",
        font=("Rajdhani", 9),
    )
"""

import tkinter as tk


class _CanvasTooltip:
    """Lightweight tooltip that appears above a tk.Canvas widget on hover."""

    def __init__(self, canvas, text, bg="#1A3A2E", fg="#FFD700",
                 border_colour="#2ECC71", font=None, pad=(8, 6)):
        self._canvas        = canvas
        self._text          = text
        self._bg            = bg
        self._fg            = fg
        self._border_colour = border_colour
        self._font          = font or ("Rajdhani", 9)
        self._pad           = pad
        self._tip_window    = None

        canvas.bind("<Enter>", self._on_enter)
        canvas.bind("<Leave>", self._on_leave)

    def _on_enter(self, event=None):
        """Show the tooltip window just above the canvas widget."""
        if self._tip_window or not self._text:
            return
        try:
            x = self._canvas.winfo_rootx() + self._canvas.winfo_width() // 2
            y = self._canvas.winfo_rooty() - 52

            tip = tk.Toplevel(self._canvas)
            tip.overrideredirect(True)
            tip.attributes("-topmost", True)
            tip.configure(bg=self._border_colour)

            outer = tk.Frame(tip, bg=self._border_colour, padx=1, pady=1)
            outer.pack()
            inner = tk.Frame(outer, bg=self._bg,
                             padx=self._pad[0], pady=self._pad[1])
            inner.pack()
            tk.Label(
                inner,
                text=self._text,
                font=self._font,
                bg=self._bg,
                fg=self._fg,
                justify="left"
            ).pack()

            tip.update_idletasks()
            tw = tip.winfo_width()
            tip.geometry(f"+{x - tw // 2}+{y}")

            self._tip_window = tip
        except Exception:
            self._tip_window = None

    def _on_leave(self, event=None):
        """Destroy the tooltip window when the mouse leaves the canvas."""
        if self._tip_window:
            try:
                self._tip_window.destroy()
            except Exception:
                pass
            self._tip_window = None