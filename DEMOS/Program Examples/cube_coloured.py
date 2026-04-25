import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pygame
import math
import sys

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rotating 3D Cube")

# Colors for cube faces
colors = [
    (255, 0, 0),    # Red
    (0, 255, 0),    # Green
    (0, 0, 255),    # Blue
    (255, 255, 0),  # Yellow
    (255, 0, 255),  # Magenta
    (0, 255, 255)   # Cyan
]

# Cube vertices (3D coordinates)
vertices = [
    [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],  # Back face
    [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]       # Front face
]

# Cube faces (indices of vertices)
faces = [
    [0, 1, 2, 3],  # Back
    [4, 5, 6, 7],  # Front
    [0, 1, 5, 4],  # Bottom
    [2, 3, 7, 6],  # Top
    [0, 3, 7, 4],  # Left
    [1, 2, 6, 5]   # Right
]

# Rotation angles
angle_x, angle_y, angle_z = 0, 0, 0

# Projection function (orthographic)
def project(vertices):
    projected = []
    for vertex in vertices:
        # Apply rotation
        x, y, z = vertex
        # Rotate around X-axis
        y_new = y * math.cos(math.radians(angle_x)) - z * math.sin(math.radians(angle_x))
        z_new = y * math.sin(math.radians(angle_x)) + z * math.cos(math.radians(angle_x))
        # Rotate around Y-axis
        x_new = x * math.cos(math.radians(angle_y)) + z_new * math.sin(math.radians(angle_y))
        z_new = -x * math.sin(math.radians(angle_y)) + z_new * math.cos(math.radians(angle_y))
        # Rotate around Z-axis
        x_new = x_new * math.cos(math.radians(angle_z)) - y_new * math.sin(math.radians(angle_z))
        y_new = x_new * math.sin(math.radians(angle_z)) + y_new * math.cos(math.radians(angle_z))

        # Project to 2D (orthographic)
        x_proj = x_new * 50 + WIDTH // 2
        y_proj = -z_new * 50 + HEIGHT // 2
        projected.append((x_proj, y_proj))
    return projected

# Main loop
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear screen
    screen.fill((0, 0, 0))

    # Project vertices
    projected_vertices = project(vertices)

    # Draw cube faces
    for i, face in enumerate(faces):
        face_vertices = [projected_vertices[v] for v in face]
        pygame.draw.polygon(screen, colors[i], face_vertices)

    # Update angles
    angle_x += 1
    angle_y += 0.5
    angle_z += 0.75

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()