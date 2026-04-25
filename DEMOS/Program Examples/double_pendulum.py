import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.integrate import odeint

# Physical parameters (standard values for visualization)
L1, L2 = 1.0, 1.0
m1, m2 = 1.0, 1.0
g = 9.81

# Initial conditions (theta1, theta2, dtheta1/dt, dtheta2/dt)
y0 = [np.pi/4, 0.0, 0.0, 0.0]

# Time span for simulation
t_span = (0, 10)
t = np.linspace(t_span[0], t_span[1], 1000)

# Double pendulum equations (normalized)
def double_pendulum(y, t, L1, L2, m1, m2, g):
    theta1, theta2, omega1, omega2 = y

    # Calculate derivatives
    dydt = np.zeros(4)

    # Denominator terms
    denom = (m1 + m2) * L1
    denom2 = (m1 + m2 * np.cos(theta1 - theta2)**2)

    # First pendulum derivatives
    dydt[0] = omega1
    dydt[1] = omega2

    # Angular accelerations
    dydt[2] = (-g*(2*m1 + m2)*np.sin(theta1) -
                m2*g*np.sin(theta1-2*theta2) -
                2*np.sin(theta1-theta2)*m2*(omega2**2*L2 +
                omega1**2*L1*np.cos(theta1-theta2))) / denom

    dydt[3] = (2*np.sin(theta1-theta2)*(omega1**2*L1*(m1+m2) +
                g*(m1+m2)*np.cos(theta1) + omega2**2*L2*m2*np.cos(theta1-theta2))) / denom2

    return dydt

# Solve ODE
solution = odeint(double_pendulum, y0, t, args=(L1, L2, m1, m2, g))

# Extract trajectories
theta1 = solution[:, 0]
theta2 = solution[:, 1]

# Create figure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Phase space plot (theta1 vs theta2)
ax1.plot(theta1, theta2, 'b-', lw=1, alpha=0.6)
ax1.set_xlabel(r'$\theta_1$ (radians)')
ax1.set_ylabel(r'$\theta_2$ (radians)')
ax1.set_title('Phase Space Trajectory')
ax1.grid(True)

# Angle vs time plots
ax2.plot(t, theta1, 'r-', lw=1, label=r'$\theta_1$')
ax2.plot(t, theta2, 'b-', lw=1, label=r'$\theta_2$')
ax2.set_xlabel('Time (s)')
ax2.set_ylabel('Angle (radians)')
ax2.set_title('Angular Position vs Time')
ax2.legend()
ax2.grid(True)

# Show initial condition marker
ax1.plot(theta1[0], theta2[0], 'ro')
ax2.plot(t[0], theta1[0], 'ro')
ax2.plot(t[0], theta2[0], 'bo')

plt.tight_layout()
plt.show()

# Animation function
def update(frame):
    ax.clear()
    ax.set_xlim(-2, 2)
    ax.set_ylim(-2, 2)
    ax.set_aspect('equal')
    ax.axis('off')

    # Calculate positions
    x1 = L1 * np.sin(theta1[frame])
    y1 = -L1 * np.cos(theta1[frame])
    x2 = x1 + L2 * np.sin(theta2[frame])
    y2 = y1 - L2 * np.cos(theta2[frame])

    # Plot pendulum arms
    ax.plot([0, x1], [0, y1], 'b-', lw=3)
    ax.plot([x1, x2], [y1, y2], 'b-', lw=2)
    ax.plot(x1, y1, 'ro')
    ax.plot(x2, y2, 'ro')

    # Show current angles
    ax.text(0.1, -0.1, f'θ₁={theta1[frame]:.2f} rad', fontsize=10)
    ax.text(x1+0.2, y1-0.2, f'θ₂={theta2[frame]:.2f} rad', fontsize=10)

fig = plt.figure(figsize=(6, 6))
ax = plt.axes()
ani = FuncAnimation(fig, update, frames=len(t), interval=50, blit=False)

plt.show()