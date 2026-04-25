import numpy as np
import matplotlib.pyplot as plt

# Define the functions
def f(x):
    return x**2 * np.sin(x)

def integral(x):
    return -x**2 * np.cos(x) + 2*x*np.sin(x) + 2*np.cos(x)

# Generate x values
x = np.linspace(-2*np.pi, 2*np.pi, 1000)

# Compute function values
y = f(x)
y_int = integral(x) + 2  # Shift for better visualization

# Create plot
plt.figure(figsize=(10, 6))

# Plot the original function
plt.plot(x, y, label=r'$x^2 \sin(x)$', color='blue')

# Plot the integral
plt.plot(x, y_int, label=r'$\int x^2 \sin(x) dx + C$', color='red', linestyle='--')

# Add vertical lines at x=0 for reference
plt.axvline(x=0, color='gray', linestyle=':', alpha=0.5)

# Add labels and legend
plt.title('Graph of $x^2 \sin(x)$ and its Integral')
plt.xlabel('x')
plt.ylabel('y')
plt.legend()
plt.grid(True)

# Show the plot
plt.show()