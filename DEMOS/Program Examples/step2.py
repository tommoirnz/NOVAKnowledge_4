import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# Define system parameters
omega_n = 2.0      # Natural frequency (rad/s)
zeta = 0.3        # Damping ratio
t_final = 10.0    # Final time

# Create second-order system
sys = signal.TransferFunction([omega_n**2], [1, 2*zeta*omega_n, omega_n**2])

# Generate time vector
t = np.linspace(0, t_final, 500)

# Compute step response
t_step, y_step = signal.step(sys, T=t)

# Create figure
plt.figure(figsize=(10, 6))
plt.plot(t_step, y_step, 'b-', linewidth=2)
plt.title(f'Step Response of Second-Order System\nωₙ={omega_n:.1f} rad/s, ζ={zeta:.1f}')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')
plt.grid(True, alpha=0.7)
plt.axhline(1, color='k', linestyle='--', alpha=0.5)  # Steady-state reference

# Add key features to plot
if zeta < 1:  # Underdamped system
    # Calculate peak time and overshoot
    t_p = np.pi/(omega_n*np.sqrt(1-zeta**2))
    y_p = np.exp(-zeta*omega_n*t_p)
    plt.scatter(t_p, y_p, color='r', zorder=5)
    plt.annotate(f'Peak at {t_p:.2f}s\n{100*y_p:.1f}% overshoot',
                 xy=(t_p, y_p), xytext=(t_p-1, y_p+0.1),
                 arrowprops=dict(facecolor='black', shrink=0.05))

# Add legend and formatting
plt.legend(['Step Response', 'Steady-state (1)'])
plt.tight_layout()
plt.show()

# Print system parameters
print(f"System Parameters:\nNatural Frequency (ωₙ) = {omega_n:.3f} rad/s")
print(f"Damping Ratio (ζ) = {zeta:.3f}")
print(f"Time Constant (τ) = 1/(ζωₙ) = {1/(zeta*omega_n):.3f} s")