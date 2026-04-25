import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bouncing Sphere")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# Sphere properties
radius = 30
x, y = WIDTH // 2, HEIGHT // 2
dx, dy = 3, -3  # Initial velocity (x, y)
gravity = 0.2   # Gravity strength

clock = pygame.time.Clock()

def draw_sphere():
    """Draw a 2D circle representing the sphere."""
    pygame.draw.circle(screen, RED, (int(x), int(y)), radius)

def update_position():
    """Update sphere position with gravity and collision."""
    global dx, dy, x, y

    # Apply gravity (increase downward velocity)
    dy += gravity

    # Update position
    x += dx
    y += dy

    # Wall collision (left/right)
    if x - radius <= 0 or x + radius >= WIDTH:
        dx *= -0.8  # Bounce with energy loss

    # Wall collision (top/bottom)
    if y - radius <= 0 or y + radius >= HEIGHT:
        dy *= -0.8  # Bounce with energy loss

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear screen
    screen.fill(BLACK)

    # Update and draw
    update_position()
    draw_sphere()

    # Draw floor (optional)
    pygame.draw.line(screen, WHITE, (0, HEIGHT - radius), (WIDTH, HEIGHT - radius), 2)

    pygame.display.flip()
    clock.tick(60)  # Cap at 60 FPS

pygame.quit()
sys.exit()