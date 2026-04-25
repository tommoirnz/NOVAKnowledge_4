import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# Parameters for AM signal
fc = 5  # Carrier frequency (Hz)
fm = 1   # Modulating frequency (Hz)
t = np.linspace(0, 5, 10000)  # Time vector

# Modulating signal (low frequency)
m_t = 0.5 * np.sin(2 * np.pi * fm * t)

# Carrier signal
c_t = np.sin(2 * np.pi * fc * t)

# AM signal: (1 + m_t) * c_t
am_signal = (1 + m_t) * c_t

# Add some white noise to simulate real-world conditions
np.random.seed(42)
noise = 0.1 * np.random.normal(size=len(t))

# Transmitted signal (noisy)
transmitted_signal = am_signal + noise

# Synchronous demodulator: multiply by carrier and low-pass filter
demodulated = transmitted_signal * c_t

# Apply low-pass filter to remove high-frequency components
b, a = signal.butter(4, 0.3, 'low')  # Cutoff at 0.3*fc
demodulated = signal.filtfilt(b, a, demodulated)

# Extract the baseband signal
baseband = demodulated - 0.5  # Remove DC offset

# Plot results
plt.figure(figsize=(12, 8))

plt.subplot(4, 1, 1)
plt.plot(t, m_t)
plt.title('Modulating Signal (Low Frequency)')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')

plt.subplot(4, 1, 2)
plt.plot(t, c_t)
plt.title('Carrier Signal')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')

plt.subplot(4, 1, 3)
plt.plot(t, am_signal)
plt.title('AM Signal (Before Transmission)')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')

plt.subplot(4, 1, 4)
plt.plot(t, baseband)
plt.title('Demodulated Signal (After Synchronous Demodulation)')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')

plt.tight_layout()
plt.show()