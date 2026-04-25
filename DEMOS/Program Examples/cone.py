import math
import numpy as np
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

def generate_cone_vertices(radius=1.0, height=2.0, num_segments=50):
    """
    Generate vertices for a cone with optimized calculations to prevent timeout.
    Uses pre-calculated values and vectorized operations where possible.
    """
    # Pre-calculate constants
    top_radius = radius
    bottom_radius = radius
    height = height
    num_segments = num_segments

    # Create theta array once and reuse
    theta = np.linspace(0, 2 * np.pi, num_segments, endpoint=False)

    # Pre-compute trigonometric values
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)

    # Generate vertices
    vertices = []

    # Top vertex (apex)
    apex = np.array([0, 0, height])

    # Bottom circle vertices
    bottom_circle = np.column_stack([
        top_radius * cos_theta,
        top_radius * sin_theta,
        np.zeros_like(theta)
    ])

    # Generate side vertices (optimized)
    for i in range(num_segments):
        # Current bottom vertex
        current_bottom = bottom_circle[i]

        # Current height position (linear interpolation)
        current_height = height * (i / (num_segments - 1))

        # Current radius (linear interpolation from top to bottom)
        current_radius = top_radius * (1 - i/(num_segments-1)) + bottom_radius * (i/(num_segments-1))

        # Create side vertices by interpolating between apex and current bottom point
        side_vertices = []
        for j in range(10):  # 10 divisions per side segment for smoothness
            t = j / 9
            x = t * current_bottom[0] + (1-t) * 0
            y = t * current_bottom[1] + (1-t) * 0
            z = t * current_bottom[2] + (1-t) * height
            side_vertices.append([x, y, z])

        vertices.extend(side_vertices)

    # Add apex and bottom circle
    vertices.append(apex.tolist())
    vertices.extend(bottom_circle.tolist())

    return np.array(vertices)

def create_cone_faces(num_segments=50):
    """Generate cone faces (triangles) for optimized rendering"""
    faces = []

    # Bottom faces (triangles)
    for i in range(num_segments):
        faces.append([i+1, i+2, 0])  # Connecting to apex

    # Side faces (quads)
    for i in range(1, num_segments):
        bottom1 = i+1
        bottom2 = i+2
        side1 = 1 + (i-1)*10  # First side vertex
        side2 = 1 + i*10      # Next side vertex
        faces.append([bottom1, side1, side2])
        faces.append([side1, bottom1, bottom2])

    return faces

def main():
    try:
        # Generate vertices with optimized parameters
        vertices = generate_cone_vertices(radius=1.0, height=2.0, num_segments=30)

        # Create faces
        faces = create_cone_faces(30)

        # Create figure
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        # Plot vertices
        ax.scatter(vertices[:, 0], vertices[:, 1], vertices[:, 2], c='b')

        # Plot edges (connect vertices)
        edges = []
        for face in faces:
            edges.append(face[0])
            edges.append(face[1])
            edges.append(face[2])

        ax.plot(vertices[edges, 0], vertices[edges, 1], vertices[edges, 2], 'r-')

        # Set limits
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)
        ax.set_zlim(0, 2.5)
        ax.set_title('Optimized Cone Visualization')

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Error during execution: {str(e)}")

if __name__ == "__main__":
    main()