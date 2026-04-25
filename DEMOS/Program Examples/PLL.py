import numpy as np
import matplotlib.pyplot as plt

class SecondOrderPLL:
    def __init__(self, k1=1.0, k2=1.0, dt=0.01):
        """
        Initialize PLL parameters:
        - k1: Proportional gain (k_p)
        - k2: Integral gain (k_i)
        - dt: Time step for numerical integration
        """
        self.k1 = k1
        self.k2 = k2
        self.dt = dt
        self.state = {'phi': 0.0, 'phi_dot': 0.0, 'phi_hat': 0.0}  # State: phase, phase rate, estimated phase
        self.integral_error = 0.0

    def update(self, phase_error):
        """
        Update the PLL state given the phase error (phi_error = phi_in - phi_hat).
        """
        # Phase error (input phase - estimated phase)
        e = phase_error

        # Proportional-integral control law
        control_signal = self.k1 * e + self.k2 * self.integral_error * self.dt

        # Update integral error (numerical integration)
        self.integral_error += e

        # Update phase rate (numerical differentiation)
        self.state['phi_dot'] = control_signal

        # Update estimated phase (numerical integration)
        self.state['phi_hat'] += self.state['phi_dot'] * self.dt

    def get_phase_estimate(self):
        """Return the estimated phase."""
        return self.state['phi_hat']

# Simulation parameters
dt = 0.01  # Time step
T = 10.0   # Total simulation time
t = np.arange(0, T, dt)

# Frequency of the input signal (rad/s)
freq = 2.0 * np.pi  # 1 Hz input signal
phi_in = freq * t   # Input phase (noise-free)

# Simulate phase noise (e.g., due to communication delays)
phase_noise = 0.1 * np.sin(2 * np.pi * 10 * t)
phi_in_noisy = phi_in + phase_noise

# Initialize PLL
pll = SecondOrderPLL(k1=1.0, k2=0.1)

# Simulate PLL convergence
estimated_phi = np.zeros_like(t)
for i in range(len(t)):
    phase_error = phi_in_noisy[i] - pll.get_phase_estimate()
    pll.update(phase_error)
    estimated_phi[i] = pll.get_phase_estimate()

# Plot results
plt.figure(figsize=(12, 6))
plt.plot(t, phi_in, label='True Phase (no noise)', linewidth=2, alpha=0.7)
plt.plot(t, phi_in_noisy, label='Noisy Phase (input)', linewidth=2, alpha=0.7)
plt.plot(t, estimated_phi, label='PLL Phase Estimate', linewidth=2, color='red')
plt.xlabel('Time (s)')
plt.ylabel('Phase (rad)')
plt.title('PLL Phase Locking Example')
plt.legend()
plt.grid(True)
plt.show()