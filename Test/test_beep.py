import numpy as np
import sounddevice as sd
import time

def play_chime(freq=880, ms=140, vol=0.20):
    fs = 16000
    n = int(fs * (ms / 1000.0))
    t = np.linspace(0, ms / 1000.0, n, endpoint=False)
    s = np.sin(2 * np.pi * freq * t).astype(np.float32)
    fade = np.linspace(0.0, 1.0, min(16, n), dtype=np.float32)
    s[:fade.size] *= fade
    s[-fade.size:] *= fade[::-1]
    sd.play((vol * s).reshape(-1, 1), fs, blocking=False)

print("Test 1: 880Hz default")
play_chime()
time.sleep(0.5)

print("Test 2: 1200Hz higher")
play_chime(freq=1200)
time.sleep(0.5)

print("Test 3: double ping")
play_chime(freq=1000, ms=80)
time.sleep(0.15)
play_chime(freq=1200, ms=80)
time.sleep(0.5)

print("Test 4: softer")
play_chime(freq=880, ms=200, vol=0.10)
time.sleep(0.5)

print("Done")