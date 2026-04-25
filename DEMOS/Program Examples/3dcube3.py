import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

# Define the cube vertices and edges
vertices = np.array([
    [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
    [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]
])

edges = [
    [0, 1], [1, 2], [2, 3], [3, 0],  # Bottom face
    [4, 5], [5, 6], [6, 7], [7, 4],  # Top face
    [0, 4], [1, 5], [2, 6], [3, 7]   # Connecting edges
]

# Create figure and 3D axis
fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')

# Initialize the plot
line_objs = []
for edge in edges:
    x, y, z = vertices[edge].T
    line, = ax.plot(x, y, z, 'b-', linewidth=2)
    line_objs.append(line)

# Animation update function
def update(frame):
    # Rotate the cube around all three axes
    rotation_angle = np.radians(frame)
    rotation_matrix = np.array([
        [np.cos(rotation_angle), 0, np.sin(rotation_angle)],
        [0, 1, 0],
        [-np.sin(rotation_angle), 0, np.cos(rotation_angle)]
    ])

    # Apply rotation to vertices
    rotated_vertices = np.dot(vertices, rotation_matrix.T)
    for i, edge in enumerate(edges):
        x, y, z = rotated_vertices[edge].T
        line_objs[i].set_data(x, y)
        line_objs[i].set_3d_properties(z)

    return line_objs

# Create animation
ani = FuncAnimation(fig, update, frames=np.arange(0, 360, 1), interval=50, blit=False)

# Show the plot
plt.title("3D Rotating Cube")
plt.tight_layout()
plt.show()