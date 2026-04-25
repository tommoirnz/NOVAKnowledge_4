import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.animation as animation

# Define cube vertices (8 corners)
vertices = np.array([
    [-1, -1, -1],
    [1, -1, -1],
    [1, 1, -1],
    [-1, 1, -1],
    [-1, -1, 1],
    [1, -1, 1],
    [1, 1, 1],
    [-1, 1, 1]
])

# Define cube faces (6 faces, each with 4 vertices)
faces = [
    [vertices[0], vertices[1], vertices[2], vertices[3]],
    [vertices[4], vertices[5], vertices[6], vertices[7]],
    [vertices[0], vertices[1], vertices[5], vertices[4]],
    [vertices[2], vertices[3], vertices[7], vertices[6]],
    [vertices[1], vertices[2], vertices[6], vertices[5]],
    [vertices[0], vertices[3], vertices[7], vertices[4]]
]

# Create figure and 3D axis
fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')

# Initialize cube
cube = Poly3DCollection(faces, alpha=0.5, linewidths=1, edgecolor='k')
cube.set_facecolor('cyan')
ax.add_collection3d(cube)

# Set axis limits
ax.set_xlim(-2, 2)
ax.set_ylim(-2, 2)
ax.set_zlim(-2, 2)
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('3D Rotating Cube')

# Animation function
def animate(i):
    ax.view_init(elev=15, azim=i)

# Create animation
ani = animation.FuncAnimation(fig, animate, frames=np.arange(0, 360, 2),
                               interval=50, blit=False)

# Show plot
plt.tight_layout()
plt.show()