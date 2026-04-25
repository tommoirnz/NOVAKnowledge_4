import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
PADDLE_WIDTH, PADDLE_HEIGHT = 100, 10
BALL_SIZE = 10
BRICK_WIDTH, BRICK_HEIGHT = 75, 30
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
COLORS = [RED, GREEN, BLUE, (255, 255, 0), (255, 0, 255), (0, 255, 255)]

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Breakout Game")
clock = pygame.time.Clock()

# Game objects
paddle = pygame.Rect(WIDTH // 2 - PADDLE_WIDTH // 2, HEIGHT - 30, PADDLE_WIDTH, PADDLE_HEIGHT)
ball = pygame.Rect(WIDTH // 2 - BALL_SIZE // 2, HEIGHT // 2, BALL_SIZE, BALL_SIZE)
ball_speed_x, ball_speed_y = 4 * random.choice((1, -1)), -4
bricks = []

# Create bricks
for row in range(5):
    for col in range(WIDTH // BRICK_WIDTH):
        brick = pygame.Rect(col * BRICK_WIDTH, row * BRICK_HEIGHT + 50, BRICK_WIDTH, BRICK_HEIGHT)
        if brick.width > 0 and brick.height > 0:
            bricks.append((brick, COLORS[row % len(COLORS)]))

# Score
score = 0
font = pygame.font.SysFont(None, 36)

def reset_ball():
    ball.center = (WIDTH // 2, HEIGHT // 2)
    return 4 * random.choice((1, -1)), -4

def draw_objects():
    screen.fill(BLACK)
    for brick, color in bricks:
        pygame.draw.rect(screen, color, brick)
    pygame.draw.rect(screen, WHITE, paddle)
    pygame.draw.ellipse(screen, WHITE, ball)
    text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(text, (10, 10))

def check_collision():
    global ball_speed_x, ball_speed_y, score

    # Wall collision (left/right)
    if ball.left <= 0 or ball.right >= WIDTH:
        ball_speed_x *= -1

    # Ceiling collision (top)
    if ball.top <= 0:
        ball_speed_y *= -1

    # Paddle collision
    if ball.colliderect(paddle):
        # Calculate angle based on where ball hits paddle
        relative_intersect_x = (paddle.left + paddle.width / 2) - ball.centerx
        ball_speed_x = -2 * (relative_intersect_x / (paddle.width / 2))
        if abs(relative_intersect_x) < 5:
            ball_speed_x = 0
        ball_speed_y *= -1

    # Brick collision
    for i, (brick, color) in enumerate(bricks[:]):
        if ball.colliderect(brick):
            ball_speed_y *= -1
            bricks.pop(i)
            score += 10
            break

    # Bottom wall (game over)
    if ball.bottom >= HEIGHT:
        return False

    return True

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and paddle.left > 0:
        paddle.x -= 7
    if keys[pygame.K_RIGHT] and paddle.right < WIDTH:
        paddle.x += 7

    if not check_collision():
        ball_speed_x, ball_speed_y = reset_ball()

    ball.x += ball_speed_x
    ball.y += ball_speed_y

    draw_objects()
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()