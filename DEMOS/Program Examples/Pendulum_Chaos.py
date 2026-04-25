import pygame
import math
import sys
import time

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
GRAVITY = 9.81
LENGTH1, LENGTH2 = 200, 150  # Lengths of pendulum arms
MASS1, MASS2 = 1.0, 1.0     # Masses (arbitrary units for visualization)
TIME_STEP = 0.01            # Simulation time step
DAMPING = 0.99              # Energy dissipation factor

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Double Pendulum Simulation")
clock = pygame.time.Clock()

# Font for labels
font = pygame.font.SysFont('Arial', 16)

class Pendulum:
    def __init__(self):
        self.theta1 = math.pi / 4  # Initial angle for first pendulum (45 degrees)
        self.theta2 = math.pi / 4  # Initial angle for second pendulum (45 degrees)
        self.theta1_dot = 0.0      # Angular velocity for first pendulum
        self.theta2_dot = 0.0      # Angular velocity for second pendulum
        self.t = 0                 # Time counter

    def update(self):
        """Update pendulum state using Euler integration"""
        # Calculate time step
        dt = TIME_STEP

        # Calculate forces and torques (simplified double pendulum equations)
        # θ1'' = (g*(2*sin(θ1) - sin(θ1-2θ2)))/(L1*(2 - cos(θ1-θ2)))
        # θ2'' = (g*(2*sin(θ2) - sin(θ1-2θ2)))/(L2*(2 - cos(θ1-θ2)))

        # Simplified version with damping
        # θ1'' = - (G/L1) * sin(θ1) + (M2*L2/L1) * sin(θ1-2θ2) * sin(θ2)
        # θ2'' = (2*M1*M2*g/(M1+M2)) * (sin(θ1)/L1 - sin(θ2)/L2) / (L2*(2 - cos(θ1-θ2)))

        # Using more accurate numerical approach
        # We'll use a simplified version for visualization
        # θ1'' = - (G/L1) * sin(θ1) + (M2*L2/L1) * sin(θ1-2θ2) * sin(θ2)
        # θ2'' = (2*M1*M2*g/(M1+M2)) * (sin(θ1)/L1 - sin(θ2)/L2) / (L2*(2 - cos(θ1-θ2)))

        # Calculate accelerations
        sin1 = math.sin(self.theta1)
        sin2 = math.sin(self.theta2)
        cos1 = math.cos(self.theta1)
        cos2 = math.cos(self.theta2)
        sin_diff = math.sin(self.theta1 - self.theta2)

        # Numerator for θ1''
        num1 = -GRAVITY * (2 * sin1 - sin_diff)
        # Denominator for θ1''
        denom1 = LENGTH1 * (2 - cos1 * cos2)
        # Numerator for θ2''
        num2 = GRAVITY * (2 * sin2 - sin_diff)
        # Denominator for θ2''
        denom2 = LENGTH2 * (2 - cos1 * cos2)

        # Update angular accelerations
        theta1_ddot = num1 / denom1 if denom1 != 0 else 0
        theta2_ddot = num2 / denom2 if denom2 != 0 else 0

        # Update angular velocities using Euler integration
        self.theta1_dot += theta1_ddot * dt
        self.theta2_dot += theta2_ddot * dt

        # Apply damping
        self.theta1_dot *= DAMPING
        self.theta2_dot *= DAMPING

        # Update angles
        self.theta1 += self.theta1_dot * dt
        self.theta2 += self.theta2_dot * dt

        # Update time
        self.t += dt

    def draw(self, surface):
        """Draw the pendulum on the given surface"""
        # Calculate positions
        x1 = WIDTH // 2 + LENGTH1 * math.sin(self.theta1)
        y1 = HEIGHT // 2 + LENGTH1 * math.cos(self.theta1)
        x2 = x1 + LENGTH2 * math.sin(self.theta2)
        y2 = y1 + LENGTH2 * math.cos(self.theta2)

        # Draw pendulum arms
        pygame.draw.line(surface, BLACK, (WIDTH // 2, HEIGHT // 2), (x1, y1), 3)
        pygame.draw.line(surface, BLACK, (x1, y1), (x2, y2), 3)

        # Draw pendulum bobs
        pygame.draw.circle(surface, RED, (int(x1), int(y1)), 15)
        pygame.draw.circle(surface, BLUE, (int(x2), int(y2)), 15)

        # Draw pivot point
        pygame.draw.circle(surface, BLACK, (WIDTH // 2, HEIGHT // 2), 5)

        # Draw axes for reference
        pygame.draw.line(surface, GREEN, (WIDTH // 2, HEIGHT // 2), (WIDTH, HEIGHT // 2), 1)
        pygame.draw.line(surface, GREEN, (WIDTH // 2, HEIGHT // 2), (WIDTH // 2, 0), 1)

    def draw_labels(self, surface):
        """Draw labels for angles and velocities"""
        # Draw angle labels
        angle_text1 = font.render(f"θ1: {math.degrees(self.theta1):.1f}°", True, BLACK)
        angle_text2 = font.render(f"θ2: {math.degrees(self.theta2):.1f}°", True, BLACK)
        surface.blit(angle_text1, (10, 20))
        surface.blit(angle_text2, (10, 40))

        # Draw velocity labels
        vel_text1 = font.render(f"ω1: {self.theta1_dot:.2f} rad/s", True, BLACK)
        vel_text2 = font.render(f"ω2: {self.theta2_dot:.2f} rad/s", True, BLACK)
        surface.blit(vel_text1, (10, 60))
        surface.blit(vel_text2, (10, 80))

        # Draw time label
        time_text = font.render(f"Time: {self.t:.2f}s", True, BLACK)
        surface.blit(time_text, (10, 100))

        # Draw chaotic behavior warning
        chaotic_text = font.render("Chaotic System - Small Changes Cause Large Effects!", True, RED)
        surface.blit(chaotic_text, (10, HEIGHT - 30))

def main():
    pendulum = Pendulum()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Reset pendulum
                    pendulum.theta1 = math.pi / 4
                    pendulum.theta2 = math.pi / 4
                    pendulum.theta1_dot = 0.0
                    pendulum.theta2_dot = 0.0
                    pendulum.t = 0
                elif event.key == pygame.K_q:
                    running = False

        # Update pendulum state
        pendulum.update()

        # Draw everything
        screen.fill(WHITE)
        pendulum.draw(screen)
        pendulum.draw_labels(screen)

        # Display chaotic behavior information
        chaotic_info = font.render("Double Pendulum: A Classic Chaotic System", True, BLACK)
        screen.blit(chaotic_info, (WIDTH // 2 - 150, 10))

        # Display parameters
        param_text = font.render(f"L1: {LENGTH1}px | L2: {LENGTH2}px | G: {GRAVITY}m/s²", True, BLACK)
        screen.blit(param_text, (WIDTH // 2 - 150, 30))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    print("Starting double pendulum simulation...")
    print("Controls:")
    print("  - Press 'Q' to quit")
    print("  - Press 'R' to reset the pendulum")
    print("  - The simulation shows chaotic behavior over time")
    main()