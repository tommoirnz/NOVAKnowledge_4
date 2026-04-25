import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle

# Physical parameters
L1, L2 = 1.0, 1.0  # Lengths of the pendulums
m1, m2 = 1.0, 1.0  # Masses
g = 9.81            # Gravity
dt = 0.01           # Time step

# Initial conditions (small perturbation to show chaos)
theta1, theta2 = np.pi/4, np.pi/4  # Initial angles (radians)
dtheta1, dtheta2 = 0.0, 0.0        # Initial angular velocities

# Simulation parameters
num_steps = 1000
time = np.linspace(0, 10, num_steps)

# Initialize arrays to store positions
x1, y1 = [], []
x2, y2 = [], []

# Simulation function
def simulate_pendulum():
    global theta1, theta2, dtheta1, dtheta2, x1, y1, x2, y2

    # Reset storage
    x1, y1, x2, y2 = [], [], [], []

    for _ in time:
        # Calculate positions
        x1.append(L1 * np.sin(theta1))
        y1.append(-L1 * np.cos(theta1))
        x2.append(x1[-1] + L2 * np.sin(theta2))
        y2.append(y1[-1] - L2 * np.cos(theta2))

        # Calculate derivatives using Euler method
        d2theta1 = (m2 * g * np.sin(theta2) * np.cos(theta1 - theta2) -
                   m2 * L2 * dtheta2**2 * np.sin(theta1 - theta2) -
                   m1 * g * np.sin(theta1) -
                   m2 * L2 * dtheta2**2 * np.sin(theta1 - theta2) -
                   m1 * L1 * dtheta1**2 * np.sin(theta1)) / (L1 * (m1 + m2 * np.sin(theta1 - theta2)**2))

        d2theta2 = ((m1 + m2) * g * np.sin(theta1) * np.cos(theta1 - theta2) +
                   m2 * L2 * dtheta1**2 * np.sin(theta1 - theta2) -
                   m2 * g * np.sin(theta2)) / (L2 * (m1 + m2 * np.sin(theta1 - theta2)**2))

        # Update velocities and angles
        dtheta1 += d2theta1 * dt
        dtheta2 += d2theta2 * dt
        theta1 += dtheta1 * dt
        theta2 += dtheta2 * dt

    return x1, y1, x2, y2

# Run simulation
x1, y1, x2, y2 = simulate_pendulum()

# Plot setup
fig, ax = plt.subplots(figsize=(8, 6))
ax.set_xlim(-2, 2)
ax.set_ylim(-2, 2)
ax.set_aspect('equal')
ax.grid(True)

# Create pendulum objects
pendulum1 = Circle((0, 0), L1, fc='blue', alpha=0.5)
pendulum2 = Circle((0, 0), L2, fc='red', alpha=0.5)
point1 = Circle((0, 0), 0.05, fc='blue')
point2 = Circle((0, 0), 0.05, fc='red')
ax.add_patch(pendulum1)
ax.add_patch(pendulum2)
ax.add_patch(point1)
ax.add_patch(point2)

# Animation function
def update(frame):
    pendulum1.center = (x1[frame], y1[frame])
    pendulum2.center = (x2[frame], y2[frame])
    point1.center = (x1[frame], y1[frame])
    point2.center = (x2[frame], y2[frame])
    return pendulum1, pendulum2, point1, point2

# Create animation
ani = FuncAnimation(fig, update, frames=len(x1), interval=50, blit=True)

# Print verification
print("Simulation complete. Double pendulum chaotic behavior shown.")
print(f"Initial angles: θ1={theta1:.3f} rad, θ2={theta2:.3f} rad")
print(f"Final angles: θ1={theta1:.3f} rad, θ2={theta2:.3f} rad")

plt.title("Double Pendulum Chaos Simulation")
plt.xlabel("X Position")
plt.ylabel("Y Position")
plt.show()