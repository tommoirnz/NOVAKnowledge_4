import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

def generate_sphere(n_points=50):
    """Generate vertices of a sphere with n_points along each axis."""
    theta = np.linspace(0, 2 * np.pi, n_points)
    phi = np.linspace(0, np.pi, n_points)
    theta_grid, phi_grid = np.meshgrid(theta, phi)

    x = np.outer(np.sin(phi_grid), np.cos(theta_grid))
    y = np.outer(np.sin(phi_grid), np.sin(theta_grid))
    z = np.outer(np.cos(phi_grid), np.ones_like(theta_grid))
    return x, y, z

class RotatingSphereApp:
    def __init__(self, root):
        self.fig = plt.figure(figsize=(8, 6))
        self.ax = self.fig.add_subplot(111, projection='3d')

        # Generate sphere vertices (fixed n_points=50)
        self.x, self.y, self.z = generate_sphere(n_points=50)

        # Plot initial sphere (non-animated)
        self.sphere = self.ax.plot_surface(
            self.x, self.y, self.z,
            cmap='viridis',
            edgecolor='k',
            linewidth=0.5,
            alpha=0.7
        )

        # Initialize rotation variables
        self.theta = np.linspace(0, 2 * np.pi, 50)
        self.phi = np.linspace(0, np.pi, 50)
        self.rotation_angle = 0

        # Set view angle
        self.ax.view_init(elev=20, azim=30)

        # Create animation
        self.ani = FuncAnimation(
            self.fig,
            self.update_sphere,
            frames=100,
            interval=50,
            blit=False
        )
        plt.title("Rotating 3D Sphere")
        plt.tight_layout()
        plt.show()

    def update_sphere(self, frame):
        """Rotate the sphere around its center."""
        self.rotation_angle += 0.05

        # Apply rotation matrices (simplified for clarity)
        x_rotated = (
            self.x * np.cos(self.rotation_angle) +
            self.y * np.sin(self.rotation_angle)
        )
        y_rotated = (
            -self.x * np.sin(self.rotation_angle) +
            self.y * np.cos(self.rotation_angle)
        )

        # Update surface
        self.sphere.remove()
        self.sphere = self.ax.plot_surface(
            x_rotated, y_rotated, self.z,
            cmap='viridis',
            edgecolor='k',
            linewidth=0.5,
            alpha=0.7
        )
        return self.sphere

if __name__ == "__main__":
    app = RotatingSphereApp(None)