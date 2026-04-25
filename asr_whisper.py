# asr_whisper.py
from faster_whisper import WhisperModel
import numpy as np

class ASR:
    def __init__(self, model_name="medium.en", device=None, compute_type=None, beam_size=5):
        if device is None:
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"

        if compute_type is None:
            compute_type = "float16" if device == "cuda" else "int8"

        self.model = WhisperModel(model_name, device=device, compute_type=compute_type)
        self.beam_size = beam_size

        # Robust init log (works across versions)
        try:
            print(f"[Whisper Init] {self.model.device} ({self.model.compute_type})")
        except Exception:
            inner = getattr(self.model, "model", None)
            dev = getattr(inner, "device", None)
            # dev may be a string (e.g., "cuda") or an object with .type
            dev_str = getattr(dev, "type", dev)
            ctype = getattr(inner, "compute_type", None) or getattr(inner, "dtype", None)
            print(f"[Whisper Init] {dev_str} ({ctype})")

    def transcribe(self, audio, sample_rate):
        """
        audio: numpy float32 mono (preferred). If not, we coerce.
        """
        # ---- normalize input to float32 mono 16 kHz ----
        if isinstance(audio, bytes):
            audio = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
        elif not isinstance(audio, np.ndarray):
            audio = np.array(audio, dtype=np.float32)
        else:
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)

        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)  # to mono

        if sample_rate != 16000:
            # If your VAD already outputs 16 kHz, this branch won't run.
            # Remove this block if you don't have scipy installed.
            try:
                from scipy.signal import resample_poly
                audio = resample_poly(audio, 16000, sample_rate).astype(np.float32)
            except Exception:
                # Faster-Whisper can accept other rates, but best is 16k.
                pass

        # ---- robust decoding, version-safe ----
        import inspect
        # asr_whisper.py  (only the transcribe() kwargs shown)
        kw = dict(
            audio=audio,
            beam_size=self.beam_size,
            temperature=0.0,
            language="en",  # change to "fr", "de", "es", "ja" etc, or remove for auto-detect
            condition_on_previous_text=False,
            suppress_blank=True,
            no_speech_threshold=0.6,
            log_prob_threshold=-0.2,
            compression_ratio_threshold=2.6,
            word_timestamps=False,
        )

        # only pass if this faster-whisper version supports it
        if "suppress_non_speech_tokens" in inspect.signature(self.model.transcribe).parameters:
            kw["suppress_non_speech_tokens"] = True

        segments, info = self.model.transcribe(**kw)
        #print("[Whisper Info]", info)
       # print(f"[Whisper Device] {self.model.device} ({self.model.compute_type})")
        return "".join(seg.text for seg in segments).strip()
