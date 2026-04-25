import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pygame
import sys
import math

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3D Bouncing Ball (Pygame)")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# Ball properties
ball_radius = 30
ball_x, ball_y = WIDTH // 2, HEIGHT // 2
ball_dx, ball_dy = 2, 2
gravity = 0.2
bounce_factor = 0.8

# Camera "3D" effect variables (simulated depth)
camera_angle = 0
zoom = 1.0

# Clock for FPS control
clock = pygame.time.Clock()

def draw_ball(x, y, radius):
    """Draw a ball with perspective scaling (simulated 3D effect)."""
    # Calculate scaling based on "distance" (simulated depth)
    distance = math.sqrt((x - WIDTH/2)**2 + (y - HEIGHT/2)**2)
    scale = max(0.5, 1.0 - distance / (WIDTH * 1.5))  # Scale smaller when "farther"

    # Draw the ball with perspective
    pygame.draw.circle(screen, RED, (x, y), int(radius * scale))
    # Draw a "shadow" to imply depth
    shadow_radius = int(radius * scale * 0.7)
    pygame.draw.circle(screen, (100, 100, 100), (x + 5, y + 5), shadow_radius)

def main():
    global ball_x, ball_y, ball_dx, ball_dy, camera_angle

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # Clear screen
        screen.fill(BLACK)

        # Simulate "3D" camera movement (rotate around ball)
        camera_angle += 0.01

        # Update ball position with gravity and bouncing
        ball_y += ball_dy
        ball_dy += gravity

        # Check for collisions with floor (bottom of screen)
        if ball_y + ball_radius > HEIGHT:
            ball_y = HEIGHT - ball_radius
            ball_dy *= -bounce_factor

        # Check for collisions with ceiling (top of screen)
        if ball_y - ball_radius < 0:
            ball_y = ball_radius
            ball_dy *= -bounce_factor

        # Check for collisions with walls (left/right)
        if ball_x + ball_radius > WIDTH:
            ball_x = WIDTH - ball_radius
            ball_dx *= -1
        if ball_x - ball_radius < 0:
            ball_x = ball_radius
            ball_dx *= -1

        # Update ball velocity
        ball_x += ball_dx

        # Draw everything
        draw_ball(ball_x, ball_y, ball_radius)

        # Draw "ground" and "walls" for context
        pygame.draw.rect(screen, (50, 50, 50), (0, HEIGHT - 20, WIDTH, 20))  # Ground
        pygame.draw.rect(screen, (30, 30, 30), (0, 0, WIDTH, 20))  # Ceiling
        pygame.draw.rect(screen, (30, 30, 30), (0, 0, 20, HEIGHT))  # Left wall
        pygame.draw.rect(screen, (30, 30, 30), (WIDTH - 20, 0, 20, HEIGHT))  # Right wall

        # Display FPS (for debugging)
        font = pygame.font.SysFont(None, 24)
        fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, WHITE)
        screen.blit(fps_text, (10, 10))

        # Update display
        pygame.display.flip()
        clock.tick(60)  # Cap at 60 FPS

if __name__ == "__main__":
    print("3D Bouncing Ball (Pygame) - Press ESC to quit")
    main()