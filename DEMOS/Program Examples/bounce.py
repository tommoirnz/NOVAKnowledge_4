import pygame
import sys

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Create the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame Ball Collision")
clock = pygame.time.Clock()

# Global variables for ball properties
ball_radius = 30
ball_x = WIDTH // 2
ball_y = HEIGHT // 2
ball_speed_x = 4
ball_speed_y = 3

def detect_collision():
    global ball_x, ball_y, ball_speed_x, ball_speed_y

    # Vertical collision detection
    if ball_y + ball_radius >= HEIGHT or ball_y - ball_radius <= 0:
        ball_speed_y *= -1

    # Horizontal collision detection
    if ball_x + ball_radius >= WIDTH or ball_x - ball_radius <= 0:
        ball_speed_x *= -1

def draw_ball():
    pygame.draw.circle(screen, WHITE, (int(ball_x), int(ball_y)), ball_radius)

def main():
    global ball_x, ball_y, ball_speed_x, ball_speed_y

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update ball position
        ball_x += ball_speed_x
        ball_y += ball_speed_y

        # Check collisions
        detect_collision()

        # Clear screen
        screen.fill(BLACK)

        # Draw ball
        draw_ball()

        # Update display
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
