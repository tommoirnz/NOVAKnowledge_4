import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import pygame
import sys

# Initialize pygame for potential future use (though not needed for this specific task)
pygame.init()

def G(s):
    """Transfer function G(s) = 1/(s^2 + 5s + 100)"""
    return 1 / (s**2 + 5*s + 100)

def magnitude_response(s):
    """Calculate magnitude of G(s) = |G(s)|"""
    return np.abs(G(s))

def bode_plot():
    """Generate Bode plot (magnitude and phase)"""
    # Frequency range (ω from 0 to 100 rad/s)
    omega = np.linspace(0.1, 100, 1000)
    s = 1j * omega  # s = jω

    # Calculate magnitude and phase
    mag = magnitude_response(s)
    phase = np.angle(G(s), deg=True)

    # Plot magnitude (dB)
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.semilogx(omega, 20 * np.log10(mag))
    plt.title('Magnitude Response (dB)')
    plt.xlabel('Frequency (rad/s)')
    plt.ylabel('Magnitude (dB)')
    plt.grid(True)

    # Plot phase
    plt.subplot(1, 2, 2)
    plt.semilogx(omega, phase)
    plt.title('Phase Response (degrees)')
    plt.xlabel('Frequency (rad/s)')
    plt.ylabel('Phase (degrees)')
    plt.grid(True)

    plt.tight_layout()
    plt.show()

def plot_3d_surface():
    """Plot 3D surface of |G(s)| where s = x + iy"""
    # Create grid of complex numbers
    x = np.linspace(-20, 20, 100)
    y = np.linspace(-20, 20, 100)
    X, Y = np.meshgrid(x, y)
    S = X + 1j * Y

    # Calculate magnitude
    Z = magnitude_response(S)

    # Plot 3D surface
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Plot surface
    surf = ax.plot_surface(X, Y, Z, cmap=cm.viridis,
                          linewidth=0, antialiased=False)

    # Add labels and title
    ax.set_xlabel('Re(s)')
    ax.set_ylabel('Im(s)')
    ax.set_zlabel('|G(s)|')
    ax.set_title('3D Magnitude Response of G(s) = 1/(s² + 5s + 100)')

    # Add color bar
    fig.colorbar(surf, shrink=0.5, aspect=5)

    plt.tight_layout()
    plt.show()

def main():
    print("Generating plots for G(s) = 1/(s² + 5s + 100)...")

    # Generate 3D surface plot
    print("Creating 3D surface plot...")
    plot_3d_surface()

    # Generate Bode plot
    print("Creating Bode plot...")
    bode_plot()

    print("All plots generated successfully!")

if __name__ == "__main__":
    main()