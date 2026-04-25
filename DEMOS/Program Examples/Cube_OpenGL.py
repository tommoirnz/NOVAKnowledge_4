import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import sys

# Initialize pygame and OpenGL
def main():
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
    gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -5)

    # Cube vertices (8 corners)
    vertices = (
        (1, -1, -1),
        (1, 1, -1),
        (-1, 1, -1),
        (-1, -1, -1),
        (1, -1, 1),
        (1, 1, 1),
        (-1, -1, 1),
        (-1, 1, 1)
    )

    # Cube edges (12 lines)
    edges = (
        (0,1), (0,3), (0,4), (2,1), (2,3), (2,7),
        (6,3), (6,4), (6,7), (5,1), (5,4), (5,7)
    )

    # Rotation variables
    rotation_x = 0
    rotation_y = 0
    rotation_z = 0
    rotation_speed = 0.5

    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Clear the screen
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

        # Draw the cube with rotation
        glPushMatrix()
        glRotatef(rotation_x, 1, 0, 0)
        glRotatef(rotation_y, 0, 1, 0)
        glRotatef(rotation_z, 0, 0, 1)

        # Draw edges
        glBegin(GL_LINES)
        glColor3f(1, 0, 0)  # Red edges
        for edge in edges:
            for vertex in edge:
                glVertex3fv(vertices[vertex])
        glEnd()

        glPopMatrix()

        # Update rotation
        rotation_x += rotation_speed
        rotation_y += rotation_speed
        rotation_z += rotation_speed

        # Update display
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have PyGame and PyOpenGL installed:")
        print("pip install pygame PyOpenGL")