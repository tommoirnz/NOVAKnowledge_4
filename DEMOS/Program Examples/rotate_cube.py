import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

# Define cube vertices (positions)
vertices = np.array([
    [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
    [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]
])

# Define cube edges (connecting vertices)
edges = np.array([
    [0, 1], [1, 2], [2, 3], [3, 0],
    [4, 5], [5, 6], [6, 7], [7, 4],
    [0, 4], [1, 5], [2, 6], [3, 7]
])

fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')
ax.set_title('Interactive 3D Rotating Cube')
ax.set_xlim([-1.5, 1.5])
ax.set_ylim([-1.5, 1.5])
ax.set_zlim([-1.5, 1.5])
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_axis_off()

# Draw cube edges (initial state)
line_objs = []
for edge in edges:
    x, y, z = vertices[edge].T
    line, = ax.plot(x, y, z, color='black', linewidth=2)
    line_objs.append(line)

# Rotation state (current angle in degrees)
angle_x, angle_y, angle_z = 0, 0, 0

def update(frame):
    global angle_x, angle_y, angle_z
    angle_x += 1
    angle_y += 0.5
    angle_z += 0.75

    # Rotation matrices (degrees)
    rot_x = np.array([
        [1, 0, 0],
        [0, np.cos(np.radians(angle_x)), -np.sin(np.radians(angle_x))],
        [0, np.sin(np.radians(angle_x)), np.cos(np.radians(angle_x))]
    ])

    rot_y = np.array([
        [np.cos(np.radians(angle_y)), 0, np.sin(np.radians(angle_y))],
        [0, 1, 0],
        [-np.sin(np.radians(angle_y)), 0, np.cos(np.radians(angle_y))]
    ])

    rot_z = np.array([
        [np.cos(np.radians(angle_z)), -np.sin(np.radians(angle_z)), 0],
        [np.sin(np.radians(angle_z)), np.cos(np.radians(angle_z)), 0],
        [0, 0, 1]
    ])

    # Apply combined rotation (X → Y → Z)
    rotated_vertices = np.dot(vertices, np.dot(rot_x, rot_y))
    rotated_vertices = np.dot(rotated_vertices, rot_z)

    # Update positions of edges
    for i, edge in enumerate(edges):
        x, y, z = rotated_vertices[edge].T
        line_objs[i].set_data(x, y)
        line_objs[i].set_3d_properties(z)

    return line_objs

# Create animation
ani = FuncAnimation(fig, update, frames=100, interval=50, blit=False)
plt.tight_layout()
plt.show()
