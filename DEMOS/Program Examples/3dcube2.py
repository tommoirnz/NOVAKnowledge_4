import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

# Define the cube vertices (8 corners)
vertices = np.array([
    [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, -1],
    [1, -1, 1], [1, 1, 1], [-1, 1, 1], [-1, -1, 1]
])

# Define the cube edges (12 edges as line segments)
edges = np.array([
    [0, 1], [0, 3], [0, 4], [1, 5], [1, 2], [2, 3],
    [3, 7], [4, 5], [4, 7], [5, 6], [6, 7], [2, 6]
])

# Set up the figure and 3D axis
fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')

# Initialize empty lines for edges and vertices
edge_lines = []
for edge in edges:
    x, y, z = [], [], []
    for vertex in [edge[0], edge[1]]:
        x.append(vertices[vertex, 0])
        y.append(vertices[vertex, 1])
        z.append(vertices[vertex, 2])
    line, = ax.plot(x, y, z, lw=2, color='blue')
    edge_lines.append(line)

# Initialize vertex markers
vertex_markers = []
for vertex in vertices:
    marker, = ax.plot(vertex[0], vertex[1], vertex[2], 'ro', markersize=6)
    vertex_markers.append(marker)

# Rotation angle (in radians)
angle = 0

def update(angle):
    global edge_lines, vertex_markers
    # Rotate vertices around the z-axis
    rotation_matrix = np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle), np.cos(angle), 0],
        [0, 0, 1]
    ])
    rotated_vertices = np.dot(vertices, rotation_matrix.T)

    # Update edge lines
    for i, edge in enumerate(edges):
        x, y, z = [], [], []
        for vertex in [edge[0], edge[1]]:
            x.append(rotated_vertices[vertex, 0])
            y.append(rotated_vertices[vertex, 1])
            z.append(rotated_vertices[vertex, 2])
        edge_lines[i].set_data(x, y)
        edge_lines[i].set_3d_properties(z)

    # Update vertex markers
    for i, marker in enumerate(vertex_markers):
        marker.set_data([rotated_vertices[i, 0]], [rotated_vertices[i, 1]])
        marker.set_3d_properties([rotated_vertices[i, 2]])

    angle += 0.05
    return edge_lines + vertex_markers

# Create animation
ani = FuncAnimation(fig, update, frames=100, interval=50, blit=False)

# Set axis limits and labels
ax.set_xlim([-2, 2])
ax.set_ylim([-2, 2])
ax.set_zlim([-2, 2])
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('3D Rotating Cube')

plt.tight_layout()
plt.show()