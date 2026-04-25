import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
from matplotlib import cm

# Create figure and 3D axis
fig = plt.figure(figsize=(8, 8))
ax = fig.add_subplot(111, projection='3d')

# Define sphere parameters
u = np.linspace(0, 2 * np.pi, 100)
v = np.linspace(0, np.pi, 50)
x = 1.5 * np.outer(np.cos(u), np.sin(v))
y = 1.5 * np.outer(np.sin(u), np.sin(v))
z = 1.5 * np.outer(np.ones(np.size(u)), np.cos(v))

# Initialize sphere data and color map
sphere = ax.plot_surface(x, y, z, cmap=cm.coolwarm, rstride=4, cstride=4)

# Rotation angles (initialized to 0)
theta = 0
phi = 0

def update(frame):
    global theta, phi
    theta += 0.01
    phi += 0.01
    ax.view_init(elev=20 + 10 * np.sin(frame * 0.1), azim=30 + 30 * np.sin(frame * 0.2))
    sphere.set_facecolor(plt.cm.coolwarm((frame / 100) % 1))
    return sphere,

# Create animation
ani = FuncAnimation(fig, update, frames=100, interval=50, blit=False)

plt.tight_layout()
plt.show()