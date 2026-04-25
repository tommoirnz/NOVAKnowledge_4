import pygame
import math
import time

def simulate_analogue_clock():
    # Initialize pygame
    pygame.init()

    # Screen dimensions
    width, height = 400, 400
    center = (width // 2, height // 2)

    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    GRAY = (150, 150, 150)

    # Create the display
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Analogue Clock")
    clock = pygame.time.Clock()

    # Background color
    screen.fill(WHITE)

    # Main loop
    running = True
    current_hour, current_minute, current_second = 12, 0, 0  # Initialize to 12:00:00

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(WHITE)

        # Draw the clock face
        pygame.draw.circle(screen, BLACK, center, 180)
        pygame.draw.circle(screen, WHITE, center, 175)

        # Draw the clock ticks
        for minute in range(60):
            if minute % 5 == 0:
                length = 15
                color = BLACK
            else:
                length = 10
                color = GRAY

            angle = math.radians((minute * 6) - 90)
            end_point = (
                center[0] + length * math.cos(angle),
                center[1] + length * math.sin(angle)
            )
            pygame.draw.line(screen, color, center, end_point, 2)

        # Draw hands based on current time
        hours = (current_minute / 60) + current_hour
        seconds_angle = math.radians((current_second * 6) - 90)
        minutes_angle = math.radians((current_minute * 6) - 90)
        hours_angle = math.radians((hours * 30) - 90)

        # Seconds hand
        pygame.draw.line(screen, RED,
                        center,
                        (
                            center[0] + 140 * math.cos(seconds_angle),
                            center[1] + 140 * math.sin(seconds_angle)
                        ), 2)

        # Minute hand
        pygame.draw.line(screen, BLUE,
                        center,
                        (
                            center[0] + 120 * math.cos(minutes_angle),
                            center[1] + 120 * math.sin(minutes_angle)
                        ), 3)

        # Hour hand
        pygame.draw.line(screen, BLACK,
                        center,
                        (
                            center[0] + 80 * math.cos(hours_angle),
                            center[1] + 80 * math.sin(hours_angle)
                        ), 4)

        # Update time
        current_second += 1
        if current_second >= 60:
            current_second = 0
            current_minute += 1
            if current_minute >= 60:
                current_minute = 0
                current_hour += 1
                if current_hour >= 24:
                    current_hour = 0

        pygame.display.flip()
        clock.tick(30)  # Run at 30 FPS

    pygame.quit()

# Run the simulation
simulate_analogue_clock()