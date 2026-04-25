import numpy as np
import matplotlib.pyplot as plt

# Define the quartic polynomial coefficients [a, b, c, d, e]
coefficients = [2, -3, 1, -4, 1]  # For f(x) = 2x⁴ - 3x³ + x² - 4x + 1

# Find roots using numpy's roots function
roots = np.roots(coefficients)

# Separate real and complex roots
real_roots = roots[np.isclose(np.imag(roots), 0)]
complex_roots = roots[~np.isclose(np.imag(roots), 0)]

print("Polynomial roots:")
for root in np.round(real_roots, 4):
    print(f"Real root: {root:.4f}")
for root in complex_roots:
    real_part = np.round(root.real, 4)
    imag_part = np.round(root.imag, 4)
    print(f"Complex root: {real_part:.4f} + {imag_part:.4f}i")

# Plot the polynomial and its roots
x_vals = np.linspace(-2, 2, 400)
y_vals = np.polyval(coefficients, x_vals)

plt.figure(figsize=(10, 6))
plt.plot(x_vals, y_vals, label=r'$f(x) = 2x^4 - 3x^3 + x^2 - 4x + 1$', color='blue')

# Plot roots as vertical lines (real roots only)
for root in real_roots:
    plt.axvline(x=root, color='red', linestyle='--', label=f'Root at x={root:.2f}')

plt.title("Quartic Polynomial with Roots")
plt.xlabel("x")
plt.ylabel("f(x)")
plt.legend()
plt.grid(True)
plt.axhline(0, color='black', linewidth=0.5)
plt.show()