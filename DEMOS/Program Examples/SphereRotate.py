import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

# Create a 3D figure
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Radius and resolution
r = 1.0
theta = np.linspace(0, np.pi, 50)
phi = np.linspace(0, 2 * np.pi, 50)
theta_grid, phi_grid = np.meshgrid(theta, phi)

# Parametric equations for a unit sphere
x = r * np.sin(theta_grid) * np.cos(phi_grid)
y = r * np.sin(theta_grid) * np.sin(phi_grid)
z = r * np.cos(theta_grid)

# Initial plot
surface = ax.plot_surface(x, y, z, color='lightblue', alpha=0.8, edgecolor='navy', rstride=4, cstride=4)

# Set labels and title
ax.set_xlabel('X-axis')
ax.set_ylabel('Y-axis')
ax.set_zlabel('Z-axis')
ax.set_title('Slowly Rotating 3D Sphere (Clockwise)', fontsize=14)
ax.set_box_aspect([1, 1, 1])  # Equal aspect ratio

# Animation update function (opposite direction: azim = 360 - frame)
def update(frame):
    ax.view_init(elev=20, azim=360 - frame)  # Clockwise rotation
    return surface,

# Create animation (slower rotation)
ani = FuncAnimation(fig, update, frames=np.arange(0, 360, 1), interval=100, blit=False)

plt.tight_layout()
plt.show()