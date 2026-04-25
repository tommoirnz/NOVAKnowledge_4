# Generated: 2026-04-09 14:02:33
# ============================================================

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import quad

# Define the function to integrate
def f(x):
    return x**2 * np.sin(x)**3 + np.cos(np.log(x))

# Define the integral function
def integral_func(a, b):
    result, _ = quad(f, a, b)
    return result

# Create x values for plotting
x = np.linspace(0.1, 10, 1000)

# Calculate the integral from 0.1 to x for each x value
integral_values = []
for xi in x:
    integral_values.append(integral_func(0.1, xi))

# Plot the integral
plt.figure(figsize=(10, 6))
plt.plot(x, integral_values, 'b-', linewidth=2)
plt.xlabel('x')
plt.ylabel('Integral of x²sin³(x) + cos(ln(x))')
plt.title('Integral of x²sin³(x) + cos(ln(x))')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()