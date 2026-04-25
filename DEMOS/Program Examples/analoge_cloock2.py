import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pygame
import math
import sys
import time

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 800
CENTER = (WIDTH // 2, HEIGHT // 2)
RADIUS = min(WIDTH, HEIGHT) * 0.4
HOUR_HAND_LENGTH = RADIUS * 0.5
MINUTE_HAND_LENGTH = RADIUS * 0.7
SECOND_HAND_LENGTH = RADIUS * 0.85
CLOCK_RADIUS = RADIUS * 0.9

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GOLD = (212, 175, 55)
DARK_GOLD = (150, 120, 50)

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Analog Clock")
clock = pygame.time.Clock()

def draw_clock():
    # Draw clock face
    screen.fill(BLACK)
    pygame.draw.circle(screen, WHITE, CENTER, CLOCK_RADIUS + 20, 2)
    pygame.draw.circle(screen, WHITE, CENTER, CLOCK_RADIUS, 2)

    # Draw clock numbers
    for i in range(1, 13):
        angle = math.radians(i * 30 - 90)
        x = CENTER[0] + CLOCK_RADIUS * 0.8 * math.cos(angle)
        y = CENTER[1] + CLOCK_RADIUS * 0.8 * math.sin(angle)
        pygame.draw.circle(screen, WHITE, (int(x), int(y)), 8)

        # Draw number text
        font = pygame.font.SysFont(None, 30)
        text = font.render(str(i), True, WHITE)
        text_rect = text.get_rect(center=(x, y))
        screen.blit(text, text_rect)

    # Draw center circle
    pygame.draw.circle(screen, WHITE, CENTER, 15)

def draw_hands(hour, minute, second):
    # Hour hand
    hour_angle = math.radians((hour % 12) * 30 - 90)
    hour_x = CENTER[0] + HOUR_HAND_LENGTH * 0.8 * math.cos(hour_angle)
    hour_y = CENTER[1] + HOUR_HAND_LENGTH * 0.8 * math.sin(hour_angle)
    pygame.draw.line(screen, GOLD, CENTER, (hour_x, hour_y), 10)

    # Minute hand
    minute_angle = math.radians(minute * 6 - 90)
    minute_x = CENTER[0] + MINUTE_HAND_LENGTH * 0.7 * math.cos(minute_angle)
    minute_y = CENTER[1] + MINUTE_HAND_LENGTH * 0.7 * math.sin(minute_angle)
    pygame.draw.line(screen, GREEN, CENTER, (minute_x, minute_y), 8)

    # Second hand
    second_angle = math.radians(second * 6 - 90)
    second_x = CENTER[0] + SECOND_HAND_LENGTH * 0.6 * math.cos(second_angle)
    second_y = CENTER[1] + SECOND_HAND_LENGTH * 0.6 * math.sin(second_angle)
    pygame.draw.line(screen, RED, CENTER, (second_x, second_y), 4)

def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Get current time
        current_time = time.localtime()
        hour = current_time.tm_hour % 12
        minute = current_time.tm_min
        second = current_time.tm_sec

        # Draw everything
        draw_clock()
        draw_hands(hour, minute, second)

        pygame.display.flip()
        clock.tick(60)  # 60 FPS

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    print("Starting analog clock...")
    main()
    print("Clock closed.")