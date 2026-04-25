import pygame
import sys
import math

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3D Animated Cube")

# Colors
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
MAGENTA = (255, 0, 255)
CYAN = (0, 255, 255)

# Cube vertices (8 corners)
vertices = [
    [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],  # Back face
    [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]       # Front face
]

# Cube edges (12 edges)
edges = [
    [0, 1], [1, 2], [2, 3], [3, 0],  # Back face
    [4, 5], [5, 6], [6, 7], [7, 4],  # Front face
    [0, 4], [1, 5], [2, 6], [3, 7]   # Connecting edges
]

# Cube colors (one per vertex)
colors = [RED, GREEN, BLUE, CYAN, MAGENTA, YELLOW, RED, GREEN]

# Rotation angles
angle_x, angle_y, angle_z = 0, 0, 0

# Projection matrix (perspective)
def project(vertex, angle_x, angle_y, angle_z):
    # Rotate X
    x = vertex[0]
    y = vertex[1] * math.cos(angle_x) - vertex[2] * math.sin(angle_x)
    z = vertex[1] * math.sin(angle_x) + vertex[2] * math.cos(angle_x)

    # Rotate Y
    x = x * math.cos(angle_y) + z * math.sin(angle_y)
    z = -x * math.sin(angle_y) + z * math.cos(angle_y)

    # Rotate Z
    y = y * math.cos(angle_z) - x * math.sin(angle_z)
    x = y * math.sin(angle_z) + x * math.cos(angle_z)

    # Perspective projection
    factor = 10 / (z + 10)
    x_proj = int(x * factor * WIDTH / 2 + WIDTH / 2)
    y_proj = int(y * factor * HEIGHT / 2 + HEIGHT / 2)
    return (x_proj, y_proj)

# Main loop
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear screen
    screen.fill(BLACK)

    # Rotate the cube
    angle_x += 0.01
    angle_y += 0.005
    angle_z += 0.008

    # Draw edges
    for edge in edges:
        start = project(vertices[edge[0]], angle_x, angle_y, angle_z)
        end = project(vertices[edge[1]], angle_x, angle_y, angle_z)

        pygame.draw.line(screen, (255, 255, 255), start, end, 1)

    # Draw vertices
    for vertex in vertices:
        projected = project(vertex, angle_x, angle_y, angle_z)
        pygame.draw.circle(screen, colors[vertices.index(vertex)], projected, 3)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()