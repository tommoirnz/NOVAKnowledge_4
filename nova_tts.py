"""
nova_tts.py — TTS mixin for Nova Assistant.

Provides all text-to-speech functionality (SAPI5 and Edge TTS),
voice selection, chime playback, and the TTS UI panel.

Usage:
    from nova_tts import NovaTTS

    class NovaAssistant(NovaTTS):
        def __init__(self):
            self._init_tts_state()   # call before _build_ui
            self._init_tts_engine()  # call before _build_ui
            ...
"""

import queue
import re
import threading
import time

import numpy as np
import tkinter as tk
from tkinter import ttk

from math_speech import MathSpeechConverter

# ── Colour / font constants (mirrors nova_assistant.py) ───────────────────────
BG_RIGHT       = "#0F1318"
SEAM           = "#1E3A5F"
DIM_TEXT       = "#6B7A99"
GREEN_GLOW     = "#2ECC71"
ELECTRIC_BLUE  = "#4A9EFF"
AMBER          = "#F39C12"
WHITE          = "#FFFFFF"

F_RAJ_SM       = ("Rajdhani", 10)
F_RAJ_BTN      = ("Rajdhani", 12, "bold")


class NovaTTS:
    """Mixin that adds all TTS capabilities to NovaAssistant."""

    # ──────────────────────────────────────────────────────────────────────────
    # INITIALISATION
    # ──────────────────────────────────────────────────────────────────────────

    def _init_tts_state(self):
        """Initialise TTS state variables. Call once in NovaAssistant.__init__."""
        self._tts_queue = queue.Queue()
        self._tts_stop  = False
        self._tts_on    = False
        self.math_speech = MathSpeechConverter()

    def _init_tts_engine(self):
        """Start the background COM-apartment worker thread for SAPI5/Edge TTS."""
        SVSFlagsAsync        = 1
        SVSFPurgeBeforeSpeak = 2

        def _worker():
            try:
                import pythoncom
                import win32com.client

                pythoncom.CoInitialize()
                try:
                    sp = win32com.client.Dispatch("SAPI.SpVoice")
                    vs = sp.GetVoices()
                    self._tts_engine = sp

                    while True:
                        try:
                            cmd = self._tts_queue.get(timeout=0.1)
                        except queue.Empty:
                            continue

                        if cmd is None:
                            break

                        if cmd == "STOP":
                            sp.Speak("", SVSFlagsAsync | SVSFPurgeBeforeSpeak)
                            continue

                        # 4-tuple: (engine_type, text, voice_name, rate)
                        if isinstance(cmd, tuple) and len(cmd) == 4:
                            engine_type, text, voice_name, rate = cmd
                            if not text.strip():
                                continue

                            if engine_type == "edge":
                                self._speak_edge(text, voice_name, rate)
                            else:
                                # SAPI5
                                for i in range(vs.Count):
                                    if vs.Item(i).GetDescription() == voice_name:
                                        sp.Voice = vs.Item(i)
                                        break
                                sp.Rate   = rate
                                sp.Volume = 100
                                sp.Speak(text, SVSFlagsAsync)
                                while sp.Status.RunningState != 0:
                                    time.sleep(0.05)
                                    if self._tts_stop:
                                        sp.Speak("", SVSFlagsAsync | SVSFPurgeBeforeSpeak)
                                        break

                        # Legacy 3-tuple: (text, voice_name, rate)  — kept for safety
                        elif isinstance(cmd, tuple) and len(cmd) == 3:
                            text, voice_name, rate = cmd
                            if not text.strip():
                                continue
                            for i in range(vs.Count):
                                if vs.Item(i).GetDescription() == voice_name:
                                    sp.Voice = vs.Item(i)
                                    break
                            sp.Rate   = rate
                            sp.Volume = 100
                            sp.Speak(text, SVSFlagsAsync)
                            while sp.Status.RunningState != 0:
                                time.sleep(0.05)
                                if self._tts_stop:
                                    sp.Speak("", SVSFlagsAsync | SVSFPurgeBeforeSpeak)
                                    break

                finally:
                    pythoncom.CoUninitialize()

            except Exception as e:
                self.log(f"[TTS] Initialization error: {e}")
                self._tts_engine = None

        threading.Thread(target=_worker, daemon=True).start()

    # ──────────────────────────────────────────────────────────────────────────
    # UI PANEL
    # ──────────────────────────────────────────────────────────────────────────

    def _build_tts_panel(self, parent):
        """Build the VOICE OUTPUT panel and pack it into *parent*."""


        outer = tk.Frame(parent, bg=SEAM, padx=1, pady=1)
        outer.pack(fill="x", padx=10, pady=6)
        if hasattr(self, "_seam_frames"):
            self._seam_frames.append(outer)

        sec = tk.Frame(outer, bg=BG_RIGHT)
        sec.pack(fill="both")

        tk.Label(sec, text="VOICE OUTPUT", font=F_RAJ_SM,
                 bg=BG_RIGHT, fg=ELECTRIC_BLUE).pack(anchor="w", padx=6, pady=(4, 0))

        row = tk.Frame(sec, bg=BG_RIGHT)
        row.pack(fill="x", padx=6, pady=4)

        # TTS toggle
        self.tts_btn = tk.Canvas(row, width=120, height=30,
                                 bg=BG_RIGHT, highlightthickness=0)
        self.tts_btn.pack(side="left", padx=4)
        self._draw_tts_btn()
        self.tts_btn.bind("<Button-1>", self._toggle_tts)

        # Stop button
        self.stop_btn = tk.Canvas(row, width=80, height=30,
                                  bg=BG_RIGHT, highlightthickness=0)
        self.stop_btn.pack(side="left", padx=4)
        self._draw_stop_c(self.stop_btn, False)
        self.stop_btn.bind("<Enter>",    lambda e: self._draw_stop_c(self.stop_btn, True))
        self.stop_btn.bind("<Leave>",    lambda e: self._draw_stop_c(self.stop_btn, False))
        self.stop_btn.bind("<Button-1>", lambda e: self._stop_speaking())

        # LaTeX toggle
        latex_c = tk.Canvas(row, width=80, height=30,
                            bg=BG_RIGHT, highlightthickness=0)
        latex_c.pack(side="left", padx=4)
        latex_c.create_rectangle(1, 1, 79, 29, fill="#1A1F2E", outline="#F39C12")
        latex_c.create_text(40, 15, text="∑ LaTeX", font=F_RAJ_BTN, fill=AMBER)
        latex_c.bind("<Button-1>", lambda e: self._toggle_latex())

        # Engine selector
        tk.Label(row, text="Engine:", font=F_RAJ_SM,
                 bg=BG_RIGHT, fg=DIM_TEXT).pack(side="left", padx=(8, 2))
        self.tts_engine_combo = self._styled_combo(row, ["sapi5", "edge"])
        self.tts_engine_combo.pack(side="left", padx=4)
        self.tts_engine_combo.set("sapi5")
        self.tts_engine_combo.bind("<<ComboboxSelected>>", self._on_tts_engine_change)

        # SAPI5 voice selector
        self.tts_voice_combo = self._styled_combo(row, [])
        self.tts_voice_combo.pack(side="left", padx=4)
        self._populate_voices()

        # Edge voice selector (hidden initially)
        self.edge_voice_combo = self._styled_combo(row, [])
        self.edge_voice_combo.pack(side="left", padx=4)
        self.edge_voice_combo.pack_forget()
        self._populate_edge_voices()

        # Speed slider
        tk.Label(row, text="Speed:", font=F_RAJ_SM,
                 bg=BG_RIGHT, fg=DIM_TEXT).pack(side="left", padx=(8, 2))
        self.tts_rate_var = tk.IntVar(value=2)
        tk.Scale(row, from_=-5, to=5, orient="horizontal",
                 variable=self.tts_rate_var, length=80,
                 bg=BG_RIGHT, fg=DIM_TEXT, highlightthickness=0,
                 troughcolor="#1A2035", sliderrelief="flat").pack(side="left", padx=4)

    # ──────────────────────────────────────────────────────────────────────────
    # DRAWING HELPERS
    # ──────────────────────────────────────────────────────────────────────────

    def _draw_tts_btn(self):
        """Redraw the TTS toggle button to reflect the current on/off state."""
        c = self.tts_btn
        c.delete("all")
        if self._tts_on:
            c.create_rectangle(1, 1, 119, 29, fill="#1A4A2E", outline=GREEN_GLOW)
            c.create_text(60, 15, text="VOICE ON",  font=F_RAJ_BTN, fill="#AAFFCC")
        else:
            c.create_rectangle(1, 1, 119, 29, fill="#2A3040", outline="#3A4A5A")
            c.create_text(60, 15, text="VOICE OFF", font=F_RAJ_BTN, fill=DIM_TEXT)

    def _draw_stop_c(self, c, hover):
        """Redraw the STOP button in its hover or idle state."""
        c.delete("all")
        c.create_rectangle(1, 1, 59, 29,
                           fill="#E74C3C" if hover else "#3A1515",
                           outline="#E74C3C" if hover else "#FF6B6B")
        c.create_text(30, 15, text="STOP", font=F_RAJ_BTN, fill="#FF6B6B")

    # ──────────────────────────────────────────────────────────────────────────
    # VOICE POPULATION
    # ──────────────────────────────────────────────────────────────────────────

    def _populate_voices(self):
        """Populate the SAPI5 voice dropdown from the installed system voices."""
        try:
            import pythoncom
            import win32com.client
            pythoncom.CoInitialize()
            try:
                sp    = win32com.client.Dispatch("SAPI.SpVoice")
                vs    = sp.GetVoices()
                names = [vs.Item(i).GetDescription() for i in range(vs.Count)]
                self.tts_voice_combo["values"] = names
                for n in names:
                    if "Linda" in n:
                        self.tts_voice_combo.set(n)
                        break
                else:
                    if names:
                        self.tts_voice_combo.set(names[0])
            finally:
                pythoncom.CoUninitialize()
        except Exception:
            self.tts_voice_combo["values"] = ["Microsoft David Desktop"]
            self.tts_voice_combo.set("Microsoft David Desktop")

    def _populate_edge_voices(self):
        """Populate the Edge TTS voice dropdown with all available neural voices."""
        voices = [
            # ── English ──────────────────────────────────────────────────────
            "en-US-AriaNeural",    "en-US-GuyNeural",     "en-US-JennyNeural",
            "en-US-DavisNeural",   "en-US-AmberNeural",   "en-US-AnaNeural",
            "en-US-AshleyNeural",  "en-US-BrandonNeural", "en-US-ChristopherNeural",
            "en-US-CoraNeural",    "en-US-ElizabethNeural","en-US-EricNeural",
            "en-US-JacobNeural",   "en-US-MichelleNeural","en-US-MonicaNeural",
            "en-US-NancyNeural",   "en-US-RogerNeural",   "en-US-SaraNeural",
            "en-US-SteffanNeural", "en-US-TonyNeural",
            "en-GB-LibbyNeural",   "en-GB-MaisieNeural",  "en-GB-RyanNeural",
            "en-GB-SoniaNeural",   "en-GB-ThomasNeural",
            "en-AU-NatashaNeural", "en-AU-WilliamNeural",
            "en-CA-ClaraNeural",   "en-CA-LiamNeural",
            "en-IN-NeerjaNeural",  "en-IN-PrabhatNeural",
            "en-IE-ConnorNeural",  "en-IE-EmilyNeural",
            "en-NZ-MitchellNeural","en-NZ-MollyNeural",
            "en-PH-JamesNeural",   "en-PH-RosaNeural",
            # ── Chinese ───────────────────────────────────────────────────────
            "zh-CN-XiaoxiaoNeural","zh-CN-XiaoyiNeural",  "zh-CN-YunjianNeural",
            "zh-CN-YunxiNeural",   "zh-CN-YunxiaNeural",  "zh-CN-YunyangNeural",
            "zh-CN-liaoning-XiaobeiNeural","zh-CN-shaanxi-XiaoniNeural",
            "zh-TW-HsiaoChenNeural","zh-TW-HsiaoYuNeural","zh-TW-YunJheNeural",
            "zh-HK-HiuGaaiNeural", "zh-HK-HiuMaanNeural","zh-HK-WanLungNeural",
            # ── Japanese / Korean ─────────────────────────────────────────────
            "ja-JP-NanamiNeural",  "ja-JP-KeitaNeural",
            "ko-KR-InJoonNeural",  "ko-KR-SunHiNeural",
            # ── Spanish ───────────────────────────────────────────────────────
            "es-ES-AlvaroNeural",  "es-ES-ElviraNeural",
            "es-MX-DaliaNeural",   "es-MX-JorgeNeural",
            "es-US-AlonsoNeural",  "es-US-PalomaNeural",
            # ── French ────────────────────────────────────────────────────────
            "fr-FR-DeniseNeural",  "fr-FR-HenriNeural",
            "fr-CA-AntoineNeural", "fr-CA-JeanNeural",    "fr-CA-SylvieNeural",
            # ── German ────────────────────────────────────────────────────────
            "de-DE-AmalaNeural",   "de-DE-ConradNeural",
            "de-DE-KatjaNeural",   "de-DE-KillianNeural",
            # ── Italian ───────────────────────────────────────────────────────
            "it-IT-DiegoNeural",   "it-IT-ElsaNeural",    "it-IT-IsabellaNeural",
            # ── Portuguese ────────────────────────────────────────────────────
            "pt-BR-AntonioNeural", "pt-BR-FranciscaNeural",
            "pt-PT-DuarteNeural",  "pt-PT-RaquelNeural",
            # ── Other major languages ─────────────────────────────────────────
            "ru-RU-DariyaNeural",  "ru-RU-SvetlanaNeural",
            "ar-AE-FatimaNeural",  "ar-AE-HamdanNeural",
            "ar-SA-HamedNeural",   "ar-SA-ZariyahNeural",
            "hi-IN-MadhurNeural",  "hi-IN-SwaraNeural",
            "nl-NL-ColetteNeural", "nl-NL-FennaNeural",   "nl-NL-MaartenNeural",
            "pl-PL-AgnieszkaNeural","pl-PL-MarekNeural",  "pl-PL-ZofiaNeural",
            "tr-TR-AhmetNeural",   "tr-TR-EmelNeural",
            "vi-VN-HoaiMyNeural",  "vi-VN-NamMinhNeural",
            "th-TH-AcharaNeural",  "th-TH-NiwatNeural",   "th-TH-PremwadeeNeural",
            "id-ID-ArdiNeural",    "id-ID-GadisNeural",
            "ms-MY-OsmanNeural",   "ms-MY-YasminNeural",
            "sv-SE-MattiasNeural", "sv-SE-SofieNeural",
            "da-DK-ChristelNeural","da-DK-JeppeNeural",
            "nb-NO-FinnNeural",    "nb-NO-PernilleNeural",
            "fi-FI-HarriNeural",   "fi-FI-NooraNeural",
            "el-GR-AthinaNeural",  "el-GR-NestorasNeural",
            "he-IL-AvriNeural",    "he-IL-HilaNeural",
            "cs-CZ-AntoninNeural", "cs-CZ-VlastaNeural",
            "hu-HU-NoemiNeural",   "hu-HU-TamasNeural",
            "ro-RO-AlinaNeural",   "ro-RO-EmilNeural",
            "uk-UA-OstapNeural",   "uk-UA-PolinaNeural",
            "ca-ES-JoanaNeural",   "ca-ES-EnricNeural",
            "eu-ES-AinhoaNeural",  "eu-ES-AnderNeural",
            "gl-ES-SabelaNeural",  "gl-ES-RoiNeural",
            "cy-GB-AledNeural",    "cy-GB-NiaNeural",
            "ga-IE-ColmNeural",    "ga-IE-OrlaNeural",
        ]
        self.edge_voice_combo["values"] = voices
        self.edge_voice_combo.set("en-US-AriaNeural")

    # ──────────────────────────────────────────────────────────────────────────
    # CONTROLS
    # ──────────────────────────────────────────────────────────────────────────

    def _toggle_tts(self, _=None):
        """Toggle voice output on or off and redraw the button."""
        self._tts_on = not self._tts_on
        self._draw_tts_btn()
        self.log(f"[TTS] {'Enabled' if self._tts_on else 'Disabled'}")

    def _on_tts_engine_change(self, _=None):
        """Switch between SAPI5 and Edge TTS voice selectors."""
        engine = self.tts_engine_combo.get()
        if engine == "edge":
            self.tts_voice_combo.pack_forget()
            self.edge_voice_combo.pack(side="left", padx=4)
            self.log("[TTS] Engine → Edge TTS")
        else:
            self.edge_voice_combo.pack_forget()
            self.tts_voice_combo.pack(side="left", padx=4)
            self.log("[TTS] Engine → SAPI5")

    def speak_text(self, text, is_math=False):
        """Speak *text* through the active TTS engine, converting LaTeX if needed."""
        if not self._tts_on or not text:
            return

        if is_math or re.search(r'\$|\\\[|\\\(|\\frac|\\int|\\sum', text):
            clean = self.math_speech.make_speakable_text(text, speak_math=True)
        else:
            clean = text.encode("ascii", "ignore").decode("ascii")
            clean = re.sub(r"[^\w\s\.,!?;:\-\(\)\/]", " ", clean)

        clean = re.sub(r"\s+", " ", clean).strip()
        if not clean:
            return

        engine = getattr(self, "tts_engine_combo", None)
        engine = engine.get() if engine else "sapi5"
        rate   = self.tts_rate_var.get() if hasattr(self, "tts_rate_var") else 2

        if engine == "edge":
            voice = self.edge_voice_combo.get() if hasattr(self, "edge_voice_combo") else "en-US-AriaNeural"
            self._tts_queue.put(("edge", clean, voice, rate))
        else:
            voice = self.tts_voice_combo.get() if hasattr(self, "tts_voice_combo") else "Microsoft David Desktop"
            self._tts_queue.put(("sapi5", clean, voice, rate))

    def _stop_speaking(self):
        """Immediately stop all queued and active speech."""
        self._tts_stop = True

        while not self._tts_queue.empty():
            try:
                self._tts_queue.get_nowait()
            except queue.Empty:
                break

        self._tts_queue.put("STOP")

        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass

        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.stop()
        except Exception:
            pass

        self._draw_stop_c(self.stop_btn, False)
        self.log("[TTS] ⏹ Stopped")
        self.root.after(500, lambda: setattr(self, "_tts_stop", False))

    # ──────────────────────────────────────────────────────────────────────────
    # EDGE TTS RUNNER
    # ──────────────────────────────────────────────────────────────────────────

    def _speak_edge(self, text, voice, rate):
        """Run Edge TTS synthesis and play the audio via sounddevice."""
        try:
            import asyncio
            import edge_tts
            import io
            import soundfile as sf
            import sounddevice as sd

            rate_pct = rate * 10
            rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"

            async def _run():
                communicate   = edge_tts.Communicate(text, voice, rate=rate_str)
                audio_chunks  = []
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_chunks.append(chunk["data"])
                return b"".join(audio_chunks)

            loop       = asyncio.new_event_loop()
            audio_data = loop.run_until_complete(_run())
            loop.close()

            if self._tts_stop or not audio_data:
                return

            data, samplerate = sf.read(io.BytesIO(audio_data))
            sd.play(data, samplerate)

            while sd.get_stream().active:
                time.sleep(0.05)
                if self._tts_stop:
                    sd.stop()
                    break

        except ImportError as e:
            self.log(f"[TTS] Edge TTS missing dependency: {e} — install edge-tts, soundfile, sounddevice")
        except Exception as e:
            self.log(f"[TTS] Edge TTS error: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # CHIME
    # ──────────────────────────────────────────────────────────────────────────

    def _play_chime(self, freq=880, ms=140, vol=0.20):
        """Play a short sine-wave chime to signal internet search activity."""
        try:
            import sounddevice as sd
            fs = 16000
            n  = int(fs * (ms / 1000.0))
            t  = np.linspace(0, ms / 1000.0, n, endpoint=False)
            s  = np.sin(2 * np.pi * freq * t).astype(np.float32)
            fade = np.linspace(0.0, 1.0, min(16, n), dtype=np.float32)
            s[:fade.size]  *= fade
            s[-fade.size:] *= fade[::-1]
            sd.play((vol * s).reshape(-1, 1), fs, blocking=False)
        except Exception as e:
            self.log(f"[CHIME] {e}")
