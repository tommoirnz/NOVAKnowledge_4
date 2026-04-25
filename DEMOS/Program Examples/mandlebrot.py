import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def mandelbrot(c, max_iter):
    z = c
    for n in range(max_iter):
        if abs(z) > 2:
            return n
        z = z*z + c
    return max_iter

def plot_mandelbrot(width=800, height=800, max_iter=100, x_min=-2.0, x_max=1.0, y_min=-1.5, y_max=1.5):
    x = np.linspace(x_min, x_max, width)
    y = np.linspace(y_min, y_max, height)
    mandelbrot_set = np.zeros((height, width))

    for i in range(width):
        for j in range(height):
            mandelbrot_set[j, i] = mandelbrot(complex(x[i], y[j]), max_iter)

    return mandelbrot_set

def visualize_mandelbrot(mandelbrot_data):
    plt.figure(figsize=(10, 10))
    plt.imshow(mandelbrot_data, extent=[-2, 1, -1.5, 1.5], cmap='viridis')
    plt.colorbar(label='Iterations')
    plt.title('Mandelbrot Set (Artistic Fractal)')
    plt.xlabel('Re(c)')
    plt.ylabel('Im(c)')
    plt.show()

# Generate and plot the Mandelbrot set
mandelbrot_data = plot_mandelbrot(max_iter=256)  # Higher max_iter = more detail
visualize_mandelbrot(mandelbrot_data)