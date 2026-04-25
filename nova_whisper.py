"""
nova_whisper.py — Faster-Whisper ASR handler for Nova Assistant.

Manages microphone recording, faster-whisper model loading,
and transcription, then inserts the result into the input box.

Usage:
    from nova_whisper import WhisperHandler

    self.whisper = WhisperHandler(self, self.log, self._update_whisper_status)
    self.whisper.load_model("medium.en", "cuda")
"""

import threading
import time

import numpy as np
import pyaudio

from asr_whisper import ASR

FG_MAIN = "#D4E0F7"


class WhisperHandler:
    """Handles faster-whisper model loading, audio recording, and transcription."""

    def __init__(self, app, log_callback, status_callback):
        self.app = app
        self.log = log_callback
        self.original_status_callback = status_callback
        self.status_callback = self._wrap

        self.CHUNK    = 1024
        self.FORMAT   = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE     = 16000

        self.is_recording     = False
        self.recording_thread = None
        self.audio_frames     = []
        self.start_time       = None
        self.p                = None
        self.is_processing    = False
        self.asr_model        = None
        self.model_loaded     = False
        self.model_name       = "medium.en"
        self.device           = "cuda"
        self.is_loading       = False

        try:
            self.p = pyaudio.PyAudio()
            self.log("[WHISPER] PyAudio ready")
        except Exception as e:
            self.log(f"[WHISPER] ❌ {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # STATUS
    # ──────────────────────────────────────────────────────────────────────────

    def _wrap(self, status):
        """Route status updates safely back to the tkinter main thread."""
        try:
            self.app.root.after(0, lambda: self.original_status_callback(status))
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────────────
    # MODEL LOADING
    # ──────────────────────────────────────────────────────────────────────────

    def load_model(self, model_name="medium.en", device="cuda"):
        """Load a faster-whisper model in a background thread."""
        if self.is_loading:
            return
        if self.model_loaded and self.model_name == model_name and self.device == device:
            self.status_callback("● READY")
            return

        self.is_loading = True
        self.model_name = model_name
        self.device = device

        def _load():
            try:
                self.status_callback("● LOADING...")
                actual_device = device
                compute_type = "float16" if actual_device == "cuda" else "float32"

                try:
                    self.asr_model = ASR(model_name=model_name,
                                         device=actual_device,
                                         compute_type=compute_type)
                except Exception as cuda_err:
                    if actual_device == "cuda":
                        self.log(f"[WHISPER] ⚠️ CUDA failed ({cuda_err}) — falling back to CPU")
                        actual_device = "cpu"
                        compute_type = "int8"
                        self.asr_model = ASR(model_name=model_name,
                                             device=actual_device,
                                             compute_type=compute_type)
                    else:
                        raise

                self.device = actual_device
                self.model_loaded = True
                self.is_loading = False
                self.status_callback("● READY")
                self.log(f"[WHISPER] ✅ {model_name} loaded on {actual_device}")

            except Exception as e:
                self.log(f"[WHISPER] ❌ {e}")
                self.status_callback("● FAILED")
                self.is_loading = False
                self.model_loaded = False

        threading.Thread(target=_load, daemon=True).start()


    # ──────────────────────────────────────────────────────────────────────────
    # RECORDING
    # ──────────────────────────────────────────────────────────────────────────

    def start_recording(self):
        """Begin capturing audio from the microphone. Returns False if not ready."""
        if not self.model_loaded or self.is_recording or self.is_processing:
            return False
        self.is_recording  = True
        self.audio_frames  = []
        self.start_time    = time.time()
        self.recording_thread = threading.Thread(target=self._record, daemon=True)
        self.recording_thread.start()
        return True

    def _record(self):
        """Background thread that reads microphone chunks until is_recording is False."""
        try:
            stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            while self.is_recording:
                self.audio_frames.append(
                    stream.read(self.CHUNK, exception_on_overflow=False)
                )
            stream.stop_stream()
            stream.close()
        except Exception as e:
            self.log(f"[WHISPER] Record error: {e}")
            self.is_recording = False

    def stop_recording(self):
        """Stop the microphone and start transcription in a background thread."""
        if not self.is_recording:
            return
        self.is_recording = False
        duration = time.time() - self.start_time if self.start_time else 0

        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=1.0)

        if len(self.audio_frames) < 10 or duration < 0.5:
            self.status_callback("● READY")
            return

        self.is_processing = True
        self.status_callback("● PROCESSING...")
        threading.Thread(target=self._transcribe, daemon=True).start()

    # ──────────────────────────────────────────────────────────────────────────
    # TRANSCRIPTION
    # ──────────────────────────────────────────────────────────────────────────

    def _transcribe(self):
        """Convert recorded frames to float32 and run faster-whisper transcription."""
        try:
            audio = (
                np.frombuffer(b"".join(self.audio_frames), dtype=np.int16)
                .astype(np.float32) / 32768.0
            )
            text = self.asr_model.transcribe(audio, self.RATE)
            if text and text.strip():
                self.app.root.after(0, lambda: self._insert(text))
                self.status_callback("● READY")
            else:
                self.status_callback("● NO SPEECH")
        except Exception as e:
            self.log(f"[WHISPER] ❌ {e}")
            self.status_callback("● FAILED")
        finally:
            self.is_processing = False

    def _insert(self, text):
        """Insert transcribed text into the Nova input box on the main thread."""
        try:
            self.app.input_text.delete("1.0", "end")
            self.app.input_text.insert("1.0", text)
            self.app._placeholder_active = False
            self.app.input_text.config(fg=FG_MAIN)
        except Exception as e:
            self.log(f"[WHISPER] Insert error: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # UTILITIES
    # ──────────────────────────────────────────────────────────────────────────

    def get_recording_time(self):
        """Return elapsed recording seconds, or 0 if not currently recording."""
        if self.is_recording and self.start_time:
            return time.time() - self.start_time
        return 0