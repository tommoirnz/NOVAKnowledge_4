import pygame
import math
import sys
import numpy as np

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rotating 3D Cube")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Cube vertices (right-handed coordinate system)
# Front face (z=1)
vertices = [
    [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1],  # Bottom face
    [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1]  # Back face
]

# Cube edges (indices)
edges = [
    (0, 1), (1, 2), (2, 3), (3, 0),  # Bottom face
    (4, 5), (5, 6), (6, 7), (7, 4),  # Top face
    (0, 4), (1, 5), (2, 6), (3, 7)   # Connecting edges
]

# Cube colors for each face
face_colors = [
    RED,    # Front (z=1)
    GREEN,  # Back (z=-1)
    BLUE,   # Left (x=-1)
    BLUE,   # Right (x=1)
    GREEN,  # Bottom (y=-1)
    RED     # Top (y=1)
]

# Projection parameters
PROJ_DIST = 5  # Distance from camera to cube center
FOV = 60       # Field of view in degrees

# Rotation angles
angle_x, angle_y, angle_z = 0, 0, 0

# Initialize clock
clock = pygame.time.Clock()

def project_point(point):
    """Project 3D point to 2D screen coordinates"""
    x, y, z = point
    # Perspective projection
    scale = PROJ_DIST / (PROJ_DIST + z)
    proj_x = x * scale
    proj_y = y * scale
    # Convert to screen coordinates
    screen_x = WIDTH // 2 + proj_x * 200
    screen_y = HEIGHT // 2 - proj_y * 200
    return (screen_x, screen_y)

def rotate_point(point, angle_x, angle_y, angle_z):
    """Rotate 3D point around x, y, z axes"""
    x, y, z = point

    # Convert to radians
    rad_x = math.radians(angle_x)
    rad_y = math.radians(angle_y)
    rad_z = math.radians(angle_z)

    # Rotation matrices
    # Rotate around Z
    x_rot = x * math.cos(rad_z) - y * math.sin(rad_z)
    y_rot = x * math.sin(rad_z) + y * math.cos(rad_z)

    # Rotate around Y
    z_rot = z * math.cos(rad_y) - y_rot * math.sin(rad_y)
    y_rot = y_rot * math.cos(rad_y) + z * math.sin(rad_y)

    # Rotate around X
    y_final = y_rot * math.cos(rad_x) - z_rot * math.sin(rad_x)
    z_final = y_rot * math.sin(rad_x) + z_rot * math.cos(rad_x)

    return (x_rot, y_final, z_final)

def draw_cube():
    """Draw the 3D cube with perspective"""
    # Clear screen
    screen.fill(BLACK)

    # Store vertices after rotation and projection
    projected_vertices = []
    for vertex in vertices:
        rotated = rotate_point(vertex, angle_x, angle_y, angle_z)
        projected = project_point(rotated)
        projected_vertices.append(projected)

    # Draw edges
    for edge in edges:
        start = projected_vertices[edge[0]]
        end = projected_vertices[edge[1]]
        pygame.draw.line(screen, WHITE, start, end, 2)

    # Draw faces (simple shading)
    # Front face (z=1)
    pygame.draw.polygon(screen, RED, [
        projected_vertices[0],
        projected_vertices[1],
        projected_vertices[2],
        projected_vertices[3]
    ])

    # Back face (z=-1)
    pygame.draw.polygon(screen, GREEN, [
        projected_vertices[4],
        projected_vertices[5],
        projected_vertices[6],
        projected_vertices[7]
    ])

    # Left face (x=-1)
    pygame.draw.polygon(screen, BLUE, [
        projected_vertices[0],
        projected_vertices[3],
        projected_vertices[7],
        projected_vertices[4]
    ])

    # Right face (x=1)
    pygame.draw.polygon(screen, BLUE, [
        projected_vertices[1],
        projected_vertices[2],
        projected_vertices[6],
        projected_vertices[5]
    ])

    # Bottom face (y=-1)
    pygame.draw.polygon(screen, GREEN, [
        projected_vertices[0],
        projected_vertices[1],
        projected_vertices[5],
        projected_vertices[4]
    ])

    # Top face (y=1)
    pygame.draw.polygon(screen, RED, [
        projected_vertices[3],
        projected_vertices[2],
        projected_vertices[6],
        projected_vertices[7]
    ])

def main():
    global angle_x, angle_y, angle_z
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Update rotation angles
        angle_x += 0.5
        angle_y += 0.3
        angle_z += 0.7

        # Draw cube
        draw_cube()

        # Display FPS
        font = pygame.font.SysFont(None, 24)
        fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, WHITE)
        screen.blit(fps_text, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()