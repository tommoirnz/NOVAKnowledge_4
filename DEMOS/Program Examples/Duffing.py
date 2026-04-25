import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# Parameters
alpha = 0.2    # Linear damping coefficient
beta = -1.0    # Linear spring constant
gamma = 0.3    # Nonlinear stiffness coefficient
F = 1.0        # External forcing amplitude
omega = 1.0    # Forcing frequency

def duffing_equation(t, y):
    # State variables: y[0] = position, y[1] = velocity
    x = y[0]
    v = y[1]

    # Derivatives
    dxdt = v
    dvdt = -alpha * v - beta * x - gamma * x**3 + F * np.cos(omega * t)

    return [dxdt, dvdt]

# Initial conditions [position, velocity]
y0 = [0.5, 0.0]

# Time span and evaluation points
t_span = (0, 20)
t_eval = np.linspace(t_span[0], t_span[1], 1000)

# Solve ODE
sol = solve_ivp(duffing_equation, t_span, y0, t_eval=t_eval, method='RK45')

# Plotting
plt.figure(figsize=(12, 6))

plt.subplot(2, 1, 1)
plt.plot(sol.t, sol.y[0], label='Position')
plt.plot(sol.t, sol.y[1], label='Velocity', linestyle='--')
plt.title('Duffing Oscillator Response')
plt.xlabel('Time')
plt.ylabel('Amplitude')
plt.legend()
plt.grid(True)

plt.subplot(2,1,2)
plt.plot(sol.y[0], sol.y[1], 'b-')
plt.title('Phase Portrait')
plt.xlabel('Position')
plt.ylabel('Velocity')
plt.grid(True)

plt.tight_layout()
plt.show()