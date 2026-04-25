import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

# Define cube vertices (8 corners)
vertices = np.array([
    [1, 1, 1], [-1, 1, 1], [-1, -1, 1], [1, -1, 1],
    [1, 1, -1], [-1, 1, -1], [-1, -1, -1], [1, -1, -1]
])

# Define edges (12 edges of a cube)
edges = [
    [0, 1], [0, 3], [0, 4], [1, 5], [2, 3], [2, 6], [3, 7],
    [4, 5], [4, 7], [5, 6], [6, 7], [0, 2]
]

# Initialize figure and 3D axis
fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')

# Plot edges (no faces for wireframe)
ax.plot_trisurf(
    [v[0] for v in vertices],
    [v[1] for v in vertices],
    [v[2] for v in vertices],
    linewidth=3, color='black', alpha=0.5, edgecolors='cyan', lw=2
)

# Create rotation functions
def rotate_x(angle):
    return np.array([
        [1, 0, 0],
        [0, np.cos(angle), -np.sin(angle)],
        [0, np.sin(angle), np.cos(angle)]
    ])

def rotate_y(angle):
    return np.array([
        [np.cos(angle), 0, np.sin(angle)],
        [0, 1, 0],
        [-np.sin(angle), 0, np.cos(angle)]
    ])

def rotate_z(angle):
    return np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle), np.cos(angle), 0],
        [0, 0, 1]
    ])

# Initialize rotation angles
theta_x, theta_y, theta_z = 0, 0, 0

# Animation update function
def update(frame):
    global theta_x, theta_y, theta_z
    theta_x += frame * 0.05
    theta_y += frame * 0.03
    theta_z += frame * 0.07

    # Apply rotations (order matters: X-Y-Z)
    R_x = rotate_x(np.deg2rad(theta_x))
    R_y = rotate_y(np.deg2rad(theta_y))
    R_z = rotate_z(np.deg2rad(theta_z))

    # Combine rotations: vertices = R_z @ R_y @ R_x @ original_vertices
    rotated_vertices = np.dot(R_z, np.dot(R_y, np.dot(R_x, vertices.T))).T

    # Clear previous plot
    ax.clear()
    ax.set_xlim([-1.5, 1.5])
    ax.set_ylim([-1.5, 1.5])
    ax.set_zlim([-1.5, 1.5])
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.grid(True)

    # Plot rotated cube
    ax.plot_trisurf(
        [v[0] for v in rotated_vertices],
        [v[1] for v in rotated_vertices],
        [v[2] for v in rotated_vertices],
        linewidth=3, color='black', alpha=0.5, edgecolors='cyan', lw=2
    )

# Create animation
ani = FuncAnimation(fig, update, frames=np.arange(0, 360, 1), interval=50)
plt.title("3D Rotating Cube (X-Y-Z Axes)")
plt.tight_layout()
plt.show()