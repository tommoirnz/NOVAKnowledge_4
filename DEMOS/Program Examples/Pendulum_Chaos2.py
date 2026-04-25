import pygame
import math
import sys
import time
from pygame.locals import *

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
GRAVITY = 0.1
LENGTH1, LENGTH2 = 200, 150  # Lengths of pendulum arms
MASS_RADIUS = 10
BACKGROUND_COLOR = (0, 0, 0)
LINE_COLOR = (255, 255, 255)
MARKER_COLOR = (255, 0, 0)  # Red for chaotic behavior markers
FONT_COLOR = (255, 255, 255)
TEXT_COLOR = (200, 200, 200)

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Double Pendulum Chaos Simulation")
clock = pygame.time.Clock()

# Physics parameters
theta1 = math.pi / 4  # Initial angle for first pendulum (45 degrees)
theta2 = math.pi / 4  # Initial angle for second pendulum (45 degrees)
dtheta1 = 0  # Initial angular velocity
dtheta2 = 0
time_step = 0.01  # Time step for simulation
total_time = 0

# Colors for visualization
pendulum_color = (100, 200, 255)
fixed_point_color = (255, 100, 100)
trajectory_color = (50, 200, 50)
marker_color = (255, 0, 0)

# Create trajectory points list
trajectory_points = []

def calculate_energy():
    """Calculate and return the total energy of the system"""
    x1 = LENGTH1 * math.sin(theta1)
    y1 = LENGTH1 * math.cos(theta1)
    x2 = x1 + LENGTH2 * math.sin(theta2)
    y2 = y1 + LENGTH2 * math.cos(theta2)

    # Potential energy (simplified)
    potential = - (y1 + y2) * 9.81

    # Kinetic energy
    v1x = dtheta1 * LENGTH1 * math.cos(theta1)
    v1y = dtheta1 * LENGTH1 * math.sin(theta1)
    v2x = dtheta2 * LENGTH2 * math.cos(theta2) + v1x
    v2y = dtheta2 * LENGTH2 * math.sin(theta2) + v1y

    kinetic = 0.5 * (v1x**2 + v1y**2 + v2x**2 + v2y**2)

    return potential + kinetic

def update_angles():
    """Update angles using Euler integration"""
    global theta1, theta2, dtheta1, dtheta2

    # Calculate forces (simplified double pendulum equations)
    alpha1 = (-3 * math.sin(theta1) - math.sin(theta1 - 2 * theta2) - math.sin(theta1) * math.cos(theta1) * math.cos(theta2) * dtheta2**2) / 2
    alpha2 = (2 * math.cos(theta1 - theta2) * (dtheta1**2 * LENGTH1 + dtheta2**2 * LENGTH2) - GRAVITY * (2 * math.sin(theta2 - theta1) + math.sin(theta2))) / LENGTH2

    # Update angular velocities
    dtheta1 += alpha1 * time_step
    dtheta2 += alpha2 * time_step

    # Update angles
    theta1 += dtheta1 * time_step
    theta2 += dtheta2 * time_step

    # Keep angles within -pi to pi range
    theta1 = (theta1 + math.pi) % (2 * math.pi) - math.pi
    theta2 = (theta2 + math.pi) % (2 * math.pi) - math.pi

def draw_pendulum():
    """Draw the double pendulum and its trajectory"""
    screen.fill(BACKGROUND_COLOR)

    # Calculate positions
    x1 = WIDTH // 2 + LENGTH1 * math.sin(theta1)
    y1 = HEIGHT // 2 - LENGTH1 * math.cos(theta1)
    x2 = x1 + LENGTH2 * math.sin(theta2)
    y2 = y1 - LENGTH2 * math.cos(theta2)

    # Draw fixed point
    pygame.draw.circle(screen, fixed_point_color, (WIDTH // 2, HEIGHT // 2), MASS_RADIUS * 2)

    # Draw pendulum arms
    pygame.draw.line(screen, pendulum_color, (WIDTH // 2, HEIGHT // 2), (x1, y1), 5)
    pygame.draw.line(screen, pendulum_color, (x1, y1), (x2, y2), 5)

    # Draw pendulum bobs
    pygame.draw.circle(screen, (200, 200, 255), (int(x1), int(y1)), MASS_RADIUS)
    pygame.draw.circle(screen, (150, 150, 255), (int(x2), int(y2)), MASS_RADIUS)

    # Draw trajectory points
    for point in trajectory_points:
        pygame.draw.circle(screen, trajectory_color, point, 2)

    # Draw current position marker
    pygame.draw.circle(screen, marker_color, (int(x2), int(y2)), MASS_RADIUS * 2)

    # Display energy information
    energy = calculate_energy()
    font = pygame.font.SysFont(None, 24)
    energy_text = font.render(f"Energy: {energy:.2f}", True, TEXT_COLOR)
    screen.blit(energy_text, (10, 10))

    # Display chaotic behavior indicator
    if abs(dtheta1) > 5 or abs(dtheta2) > 5:
        chaotic_text = font.render("CHAOTIC BEHAVIOR DETECTED!", True, (255, 0, 0))
        screen.blit(chaotic_text, (WIDTH - 300, 10))

def main():
    global theta1, theta2, dtheta1, dtheta2, total_time, trajectory_points

    # Initial trajectory point
    x1 = WIDTH // 2 + LENGTH1 * math.sin(theta1)
    y1 = HEIGHT // 2 - LENGTH1 * math.cos(theta1)
    trajectory_points.append((int(x1), int(y1)))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_r:
                    # Reset simulation
                    theta1 = math.pi / 4
                    theta2 = math.pi / 4
                    dtheta1 = 0
                    dtheta2 = 0
                    trajectory_points = []
                    x1 = WIDTH // 2 + LENGTH1 * math.sin(theta1)
                    y1 = HEIGHT // 2 - LENGTH1 * math.cos(theta1)
                    trajectory_points.append((int(x1), int(y1)))

        update_angles()

        # Calculate current position for trajectory
        x1 = WIDTH // 2 + LENGTH1 * math.sin(theta1)
        y1 = HEIGHT // 2 - LENGTH1 * math.cos(theta1)
        x2 = x1 + LENGTH2 * math.sin(theta2)
        y2 = y1 - LENGTH2 * math.cos(theta2)

        # Add current position to trajectory (limit to last 500 points)
        trajectory_points.append((int(x2), int(y2)))
        if len(trajectory_points) > 500:
            trajectory_points.pop(0)

        draw_pendulum()
        pygame.display.flip()
        clock.tick(FPS)
        total_time += time_step

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    print("Starting double pendulum chaos simulation...")
    print("Controls:")
    print("  ESC - Quit")
    print("  R - Reset simulation")
    main()