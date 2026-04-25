import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import sounddevice as sd

# Parameters
fs = 44100
duration = 5.0
f_start = 100
f_end = 2000
t = np.linspace(0, duration, int(fs * duration), endpoint=False)

# Generate frequency sweep
freq_sweep = np.linspace(f_start, f_end, len(t))

# Create time array
t = t

# Generate sine wave
tone = np.sin(2 * np.pi * freq_sweep * t) * 0.5

# Plot the frequency sweep
plt.figure(figsize=(10, 4))
plt.plot(t, freq_sweep, label='Frequency Sweep (Hz)')
plt.xlabel('Time (s)')
plt.ylabel('Frequency (Hz)')
plt.title('Sine Wave Frequency Sweep: 100Hz → 2kHz')
plt.grid(True)
plt.ylim(0, 2500)
plt.legend()

# Play sound using sounddevice (cross-platform, recommended)
print("Playing sine sweep... Press Ctrl+C to stop.")
try:
    sd.play(tone, fs)
    sd.wait()
except KeyboardInterrupt:
    print("\nStopped by user.")
finally:
    plt.show()