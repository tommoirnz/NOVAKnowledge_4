import numpy as np
import matplotlib.pyplot as plt

def plot_log_function():
    # Define the function with domain restrictions
    def f(x):
        return np.log(np.abs((x + 1)/(x + 2)))

    # Safe x range avoiding singularities
    x = np.linspace(-1.9, 10, 400)
    x = x[(x + 1) != 0]  # Remove x = -1 (zero in numerator)
    x = x[(x + 2) != 0]  # Remove x = -2 (zero in denominator)

    # Evaluate function only on safe points
    y = f(x)

    # Create plot
    plt.figure(figsize=(10, 6))
    plt.plot(x, y, 'b-', linewidth=2, label=r'$y = \ln\left|\frac{x+1}{x+2}\right|$')

    # Add asymptotes
    plt.axvline(x=-2, color='r', linestyle='--', linewidth=1, label='Vertical asymptote (x=-2)')
    plt.axvline(x=-1, color='g', linestyle='--', linewidth=1, label='Zero (x=-1)')

    # Formatting
    plt.ylim(-2, 3)
    plt.xlabel('x', fontsize=12)
    plt.ylabel('y', fontsize=12)
    plt.title('Plot of Logarithmic Function with Asymptotes', fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)

    # Show plot
    plt.show()

# Execute the function
plot_log_function()