import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# --- System Parameters ---
omega_n = 1.0   # Natural frequency (rad/s)
zeta = 0.3      # Damping ratio

# --- Transfer Function ---
num = [omega_n**2]  # Numerator
den = [1, 2*zeta*omega_n, omega_n**2]  # Denominator
sys = signal.TransferFunction(num, den)

# --- Plot Step Response ---
t, y = signal.step(sys)
plt.figure(figsize=(12, 5))

# Step Response Plot
plt.subplot(1, 2, 1)
plt.plot(t, y, 'b', linewidth=2, label=f'ζ={zeta}')
plt.title('Step Response')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')
plt.grid(True)
plt.legend()

# Pole-Zero Plot
plt.subplot(1, 2, 2)
plt.scatter(sys.zeros.real, sys.zeros.imag, marker='o', color='r', label='Zeros')
plt.scatter(sys.poles.real, sys.poles.imag, marker='o', color='b', label='Poles')
plt.axvline(0, color='k', linestyle='--', alpha=0.3)
plt.axhline(0, color='k', linestyle='--', alpha=0.3)
plt.title('Pole-Zero Plot')
plt.xlabel('Real')
plt.ylabel('Imaginary')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()

# Print system information
print(f"System Poles: {sys.poles}")
print(f"System Zeros: {sys.zeros}")