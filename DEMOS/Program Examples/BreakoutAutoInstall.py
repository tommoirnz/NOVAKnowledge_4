import pygame
import sys
import random

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
PADDLE_WIDTH, PADDLE_HEIGHT = 100, 15
BALL_SIZE = 10
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BROWN = (139, 69, 19)
FPS = 60

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Breakout Game")
clock = pygame.time.Clock()

# Game objects
class Paddle:
    def __init__(self):
        self.width = PADDLE_WIDTH
        self.height = PADDLE_HEIGHT
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT - self.height - 10
        self.speed = 8
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def move(self, direction):
        if direction == "left" and self.x > 0:
            self.x -= self.speed
        if direction == "right" and self.x < WIDTH - self.width:
            self.x += self.speed
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

class Ball:
    def __init__(self):
        self.size = BALL_SIZE
        self.reset()
        self.speed_x = 4 * random.choice((1, -1))
        self.speed_y = -4
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)

    def reset(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)

    def move(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)

        # Wall collision
        if self.x <= 0 or self.x >= WIDTH - self.size:
            self.speed_x *= -1
        if self.y <= 0:
            self.speed_y *= -1

# Create game objects
paddle = Paddle()
ball = Ball()

# Bricks setup
brick_rows = 5
brick_cols = WIDTH // 80
bricks = []
brick_width = 80
brick_height = 30
brick_spacing = 5
brick_row_spacing = 15

for row in range(brick_rows):
    bricks.append([])
    for col in range(brick_cols):
        brick_x = col * (brick_width + brick_spacing) + brick_spacing
        brick_y = row * (brick_height + brick_row_spacing) + brick_row_spacing
        bricks[row].append({
            'rect': pygame.Rect(brick_x, brick_y, brick_width, brick_height),
            'alive': True,
            'color': (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        })

# Score
score = 0

# Game loop
running = True
game_over = False

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_over:
                # Reset game
                paddle = Paddle()
                ball = Ball()
                bricks = []
                for row in range(brick_rows):
                    bricks.append([])
                    for col in range(brick_cols):
                        brick_x = col * (brick_width + brick_spacing) + brick_spacing
                        brick_y = row * (brick_height + brick_row_spacing) + brick_row_spacing
                        bricks[row].append({
                            'rect': pygame.Rect(brick_x, brick_y, brick_width, brick_height),
                            'alive': True,
                            'color': (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                        })
                score = 0
                game_over = False

    if not game_over:
        # Move paddle
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            paddle.move("left")
        if keys[pygame.K_RIGHT]:
            paddle.move("right")

        # Move ball
        ball.move()

        # Ball-paddle collision
        if ball.rect.colliderect(paddle.rect) and ball.speed_y > 0:
            ball.speed_y *= -1
            # Add some angle based on where the ball hits the paddle
            relative_intersect_x = (paddle.x + paddle.width/2) - ball.x
            normalized_intersect_x = relative_intersect_x / (paddle.width/2)
            ball.speed_x = -10 * normalized_intersect_x

        # Ball-brick collision
        for row in bricks:
            for brick in row:
                if brick['alive'] and ball.rect.colliderect(brick['rect']):
                    brick['alive'] = False
                    ball.speed_y *= -1
                    score += 10

        # Check if ball went out of bounds
        if ball.y > HEIGHT:
            game_over = True

    # Check if all bricks are destroyed
    all_bricks_destroyed = True
    for row in bricks:
        for brick in row:
            if brick['alive']:
                all_bricks_destroyed = False
                break
        if not all_bricks_destroyed:
            break

    if all_bricks_destroyed and not game_over:
        game_over = True
        # You win!
        ball.speed_y = 0
        ball.speed_x = 0

    # Draw everything
    screen.fill(BROWN)

    # Draw bricks
    for row in bricks:
        for brick in row:
            if brick['alive']:
                pygame.draw.rect(screen, brick['color'], brick['rect'])
                pygame.draw.rect(screen, WHITE, brick['rect'], 1)

    # Draw paddle
    pygame.draw.rect(screen, WHITE, paddle.rect)

    # Draw ball
    pygame.draw.ellipse(screen, WHITE, ball.rect)

    # Draw score
    font = pygame.font.SysFont(None, 36)
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    # Game over message
    if game_over:
        font = pygame.font.SysFont(None, 72)
        if all_bricks_destroyed:
            message = "You Win!"
        else:
            message = "Game Over!"

        text_surface = font.render(message, True, WHITE)
        text_rect = text_surface.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
        screen.blit(text_surface, text_rect)

        font = pygame.font.SysFont(None, 36)
        restart_text = font.render("Press R to restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
        screen.blit(restart_text, restart_rect)

    pygame.display.flip()

pygame.quit()
sys.exit()