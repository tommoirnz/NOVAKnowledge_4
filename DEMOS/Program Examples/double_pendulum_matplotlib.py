import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
from scipy.integrate import odeint

# Constants
L1, L2 = 1.0, 1.0  # Lengths of pendulum arms
m1, m2 = 1.0, 1.0  # Masses
g = 9.81  # Gravity

# Initial conditions (theta1, theta2, omega1, omega2)
theta1_0, theta2_0 = np.pi/4, np.pi/4  # Initial angles (radians)
omega1_0, omega2_0 = 0.0, 0.0  # Initial angular velocities
y0 = np.array([theta1_0, theta2_0, omega1_0, omega2_0])

# Time span
t = np.linspace(0, 20, 1000)

# Double pendulum equations (simplified)
def double_pendulum(y, t, L1, L2, m1, m2, g):
    theta1, theta2, omega1, omega2 = y
    dtheta1dt = omega1
    dtheta2dt = omega2
    domega1dt = (
        (m2 * g * np.sin(theta2) * np.cos(theta1 + theta2) - m2 * L2 * omega2**2 * np.sin(theta1 + theta2)
         - m1 * g * np.sin(theta1) - m2 * L1 * omega1**2 * np.sin(theta1)) /
        (L1 * (m1 + m2 * np.sin(theta1)**2))
    )
    domega2dt = (
        (m1 * g * np.sin(theta1) * np.cos(theta1 + theta2) + m1 * L1 * omega1**2 * np.sin(theta1 + theta2)
         + m2 * g * np.sin(theta2) + m2 * L2 * omega2**2 * np.sin(theta2)) /
        (L2 * (m1 + m2 * np.sin(theta1)**2))
    )
    return [dtheta1dt, dtheta2dt, domega1dt, domega2dt]

# Solve ODE
sol = odeint(double_pendulum, y0, t, args=(L1, L2, m1, m2, g))

# Prepare data for plotting
x1 = L1 * np.sin(sol[:, 0])
y1 = -L1 * np.cos(sol[:, 0])
x2 = x1 + L2 * np.sin(sol[:, 1])
y2 = y1 - L2 * np.cos(sol[:, 1])

# Set up figure
fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')

# Initialization function
def init():
    ax.clear()
    ax.set_xlim(-2, 2)
    ax.set_ylim(-2, 2)
    ax.set_zlim(-2, 2)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Double Pendulum Chaos Theory')
    ax.grid(True)

# Animation function
def animate(i):
    ax.clear()
    ax.set_xlim(-2, 2)
    ax.set_ylim(-2, 2)
    ax.set_zlim(-2, 2)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Double Pendulum Chaos Theory')
    ax.grid(True)

    # Plot pendulum arms
    ax.plot([0, x1[i]], [0, y1[i]], [0, 0], 'b-', lw=2)
    ax.plot([x1[i], x2[i]], [y1[i], y2[i]], [0, 0], 'r-', lw=2)

    # Plot pendulum bobs
    ax.scatter([0], [0], [0], c='b', s=100, label='Pivot')
    ax.scatter([x1[i]], [y1[i]], [0], c='b', s=100, label='Bob 1')
    ax.scatter([x2[i]], [y2[i]], [0], c='r', s=100, label='Bob 2')

    ax.legend()

# Create animation
ani = FuncAnimation(fig, animate, frames=len(t), interval=50, init_func=init)
plt.show()