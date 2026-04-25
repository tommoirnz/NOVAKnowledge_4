import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

# Physics parameters
gravity = 9.81  # m/s²
bounce_coeff = 0.8  # Energy loss per bounce
air_resistance = 0.99  # Damping factor
dt = 0.05  # Time step

# Initial conditions
x, y, z = 0.0, 0.0, 10.0  # Start at (0,0,10)
vx, vy, vz = 0.0, 0.0, -10.0  # Initial velocity downward

# Simulation bounds
floor_height = 0.0
max_height = 20.0

# Setup figure
fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')
ax.set_xlim(-5, 5)
ax.set_ylim(-5, 5)
ax.set_zlim(0, max_height)
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('Bouncing Sphere Simulation')

# Sphere properties
sphere = ax.scatter([], [], [], c='red', s=100)

def update(frame):
    global x, y, z, vx, vy, vz

    # Update velocity (with air resistance)
    vx *= air_resistance
    vy *= air_resistance
    vz -= gravity * dt * air_resistance

    # Update position
    x += vx * dt
    y += vy * dt
    z += vz * dt

    # Check for collisions
    if z <= floor_height:
        vz = -vz * bounce_coeff  # Bounce
        z = floor_height  # Stop at floor

    # Update sphere position
    sphere._offsets3d = ([x], [y], [z])

    return sphere,

# Create animation
ani = FuncAnimation(fig, update, frames=200, interval=50, blit=False)
plt.tight_layout()
plt.show()