import numpy as np
import matplotlib.pyplot as plt

# Define frequency response components
def H_freq_response(w):
    numerator = 1
    denominator = 1 - 0.5 * np.exp(-1j * w)
    return numerator / denominator

# Frequency range (0 to 2π, normalized to Nyquist)
w = np.linspace(0, 2 * np.pi, 1000)

# Compute frequency response
H = H_freq_response(w)

# Magnitude and phase
magnitude = np.abs(H)
phase = np.angle(H, deg=False)  # Phase in radians

# Plot magnitude and phase (stacked vertically)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

# Magnitude response (top)
ax1.plot(w / np.pi, magnitude)  # Normalize by π for readability
ax1.set_title("Magnitude Response")
ax1.set_xlabel("Normalized Frequency ($\omega / \pi$ rad/sample)")
ax1.set_ylabel("Magnitude")
ax1.grid(True)

# Phase response (bottom)
ax2.plot(w / np.pi, phase)
ax2.set_title("Phase Response")
ax2.set_xlabel("Normalized Frequency ($\omega / \pi$ rad/sample)")
ax2.set_ylabel("Phase (radians)")
ax2.grid(True)

plt.tight_layout()
plt.show()