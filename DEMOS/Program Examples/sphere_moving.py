import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

# Parameters
theta = np.linspace(0, 2 * np.pi, 50)  # Azimuthal angle
phi = np.linspace(0, np.pi, 50)        # Polar angle
theta_grid, phi_grid = np.meshgrid(theta, phi)

# Sphere coordinates (unit sphere)
x_sphere = np.outer(np.sin(phi_grid), np.cos(theta_grid))
y_sphere = np.outer(np.sin(phi_grid), np.sin(theta_grid))
z_sphere = np.outer(np.cos(phi_grid), np.ones_like(theta_grid))

# Sine-wave motion parameters
amplitude = 1.0
frequency = 0.05
time = 0

# Initialize figure and axis
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Initial sphere position
def update(frame):
    global time
    time = frame * frequency

    # Sine-wave motion along each axis
    x_motion = amplitude * np.sin(time)
    y_motion = amplitude * np.cos(time)
    z_motion = amplitude * np.sin(time * 1.5)  # Slightly different frequency for variety

    # Move sphere along sine waves
    x_pos = x_sphere + x_motion
    y_pos = y_sphere + y_motion
    z_pos = z_sphere + z_motion

    # Clear previous plot
    ax.clear()

    # Plot sphere with sine-wave motion
    ax.plot_surface(x_pos, y_pos, z_pos, cmap='viridis', edgecolor='k', alpha=0.7)

    # Set axis limits to accommodate motion
    ax.set_xlim([-2, 2])
    ax.set_ylim([-2, 2])
    ax.set_zlim([-2, 2])

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Sphere Moving Along Sine-Wave Trajectories')

# Animate the sphere
ani = FuncAnimation(fig, update, frames=np.linspace(0, 20, 200), interval=50)
plt.tight_layout()
plt.show()