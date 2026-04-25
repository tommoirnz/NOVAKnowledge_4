import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D  # For potential 3D exploration (though 2D is standard for double pendulum)

# Constants
g = 9.81  # Acceleration due to gravity
L1, L2 = 1.0, 0.5  # Lengths of the two pendulum arms
m1, m2 = 1.0, 1.0  # Masses of the two pendulum bobs
dt = 0.01  # Time step
total_time = 30.0  # Simulation time in seconds

# Initialize pendulum angles and velocities
theta1, theta2 = np.radians(10), np.radians(-10)  # Initial angles in radians
dtheta1, dtheta2 = 0.0, 0.0  # Initial angular velocities

# Initialize lists to store trajectory data
traj1_x, traj1_y = [], []
traj2_x, traj2_y = [], []
times = []

# Function to calculate the positions of the pendulum bobs
def get_positions(theta1, theta2, L1, L2):
    x1 = L1 * np.sin(theta1)
    y1 = -L1 * np.cos(theta1)
    x2 = x1 + L2 * np.sin(theta2)
    y2 = y1 - L2 * np.cos(theta2)
    return x1, y1, x2, y2

# Function to update the pendulum state using Euler integration
def update_state(theta1, theta2, dtheta1, dtheta2, dt):
    # Calculate torques (simplified for double pendulum)
    torque1 = -(m2 * g * np.sin(theta2) * np.sin(theta1 + theta2) +
                m2 * L2 * dtheta2**2 * np.sin(theta1 + theta2) +
                m1 * g * np.sin(theta1))
    torque2 = (m2 * L2 * dtheta2**2 * np.sin(theta1 + theta2) * np.cos(theta2) -
               m2 * g * np.sin(theta2) * np.cos(theta1 + theta2) +
               m1 * L1 * dtheta1**2 * np.sin(theta1) * np.cos(theta1 + theta2))

    # Update angular accelerations
    d2theta1 = (torque1 / (L1 * (m1 + m2 * np.sin(theta1)**2))) - (m2 * L2 * dtheta2**2 * np.cos(theta1 + theta2)) / L1
    d2theta2 = (torque2 / (L2 * (m1 + m2 * np.sin(theta1)**2))) + (m1 * L1 * d2theta1 * np.cos(theta1 + theta2) / L2)

    # Update velocities and angles using Euler method
    dtheta1 += d2theta1 * dt
    dtheta2 += d2theta2 * dt
    theta1 += dtheta1 * dt
    theta2 += dtheta2 * dt

    return theta1, theta2, dtheta1, dtheta2

# Initialize figure and axis for plotting
fig, ax = plt.subplots(figsize=(8, 6))
ax.set_xlim(-2.5, 2.5)
ax.set_ylim(-2.5, 2.5)
ax.set_aspect('equal')
ax.grid(True)

# Create pendulum lines and bob markers
line1, = ax.plot([], [], 'o-', lw=2, markersize=8, color='blue')
line2, = ax.plot([], [], 'o-', lw=2, markersize=6, color='red')
fixed_point, = ax.plot([], [], 'o', markersize=10, color='black')

# Initialize trajectory lines
traj1, = ax.plot([], [], 'b--', alpha=0.5)
traj2, = ax.plot([], [], 'r--', alpha=0.5)

# Animation update function
def update(frame):
    global theta1, theta2, dtheta1, dtheta2, traj1_x, traj1_y, traj2_x, traj2_y, times

    # Update pendulum state
    theta1, theta2, dtheta1, dtheta2 = update_state(theta1, theta2, dtheta1, dtheta2, dt)

    # Store current positions for trajectory
    x1, y1, x2, y2 = get_positions(theta1, theta2, L1, L2)
    traj1_x.append(x1)
    traj1_y.append(y1)
    traj2_x.append(x2)
    traj2_y.append(y2)
    times.append(frame * dt)

    # Update plot data
    x1, y1, x2, y2 = get_positions(theta1, theta2, L1, L2)

    # Update pendulum lines
    line1.set_data([0, x1], [0, y1])
    line2.set_data([x1, x2], [y1, y2])
    fixed_point.set_data([0], [0])

    # Update trajectory lines (show last 500 points)
    traj1.set_data(traj1_x[-500:], traj1_y[-500:])
    traj2.set_data(traj2_x[-500:], traj2_y[-500:])

    # Print current state for verification
    print(f"Frame {frame}: θ1={theta1:.3f} rad, θ2={theta2:.3f} rad")

    return line1, line2, traj1, traj2

# Create animation
ani = FuncAnimation(fig, update, frames=int(total_time/dt), interval=20, blit=False)

# Add title and labels
ax.set_title("Double Pendulum Chaotic Motion", fontsize=14)
ax.set_xlabel("X Position")
ax.set_ylabel("Y Position")

# Show plot
plt.tight_layout()
print("Double pendulum simulation started. Chaotic behavior will be visible in the animation.")
plt.show()