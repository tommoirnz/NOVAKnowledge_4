import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def plot_3d_elliptical_disk(a, b, c):
    # Create theta and phi grids
    theta = np.linspace(0, 2 * np.pi, 100)
    phi = np.linspace(0, np.pi, 50)

    # Parametric equations for an elliptical disk
    x = a * np.outer(np.cos(theta), np.sin(phi))
    y = b * np.outer(np.sin(theta), np.sin(phi))
    z = c * np.outer(np.ones_like(theta), np.cos(phi))

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Plot the surface with correct syntax
    ax.plot_surface(x, y, z, cmap='viridis', alpha=0.8)

    # Set labels
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title(f'3D Elliptical Disk (a={a}, b={b}, c={c})')
    plt.tight_layout()
    plt.show()

def plot_3d_ellipsoid(a, b, c):
    # Create theta and phi grids
    theta = np.linspace(0, 2 * np.pi, 100)
    phi = np.linspace(0, np.pi, 50)

    # Parametric equations for an ellipsoid
    x = a * np.outer(np.sin(theta), np.sin(phi))
    y = b * np.outer(np.cos(theta), np.sin(phi))
    z = c * np.outer(np.ones_like(theta), np.cos(phi))

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Plot the surface with correct syntax
    ax.plot_surface(x, y, z, cmap='plasma', alpha=0.8)

    # Set labels
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title(f'3D Ellipsoid (a={a}, b={b}, c={c})')
    plt.tight_layout()
    plt.show()

# Example usage:
if __name__ == "__main__":
    print("Creating 3D visualizations...")
    plot_3d_elliptical_disk(a=2, b=1, c=0.5)
    plot_3d_ellipsoid(a=3, b=2, c=1)