import numpy as np
import matplotlib.pyplot as plt

def newtons_method_for_cube_root(target=27, initial_guess=2, tolerance=1e-6, max_iterations=100):
    """
    Implement Newton's method to find the cube root of target.
    Returns the converged value and iteration history.
    """
    def f(x):
        return x**3 - target

    def f_prime(x):
        return 3 * x**2

    x = initial_guess
    history = []

    for n in range(max_iterations):
        x_new = x - f(x) / f_prime(x)
        history.append(x)  # Store previous x value

        if abs(f(x_new)) < tolerance:
            history.append(x_new)  # Store final converged value
            return x_new, history

        x = x_new

    return x, history

# Main execution
target = 27
initial_guess = 2
converged_value, iterations = newtons_method_for_cube_root(target, initial_guess)

# Create data for plotting
x_vals = np.linspace(0.5, 4, 400)
f_vals = x_vals**3 - target

# Prepare iteration data
x_vals_iters = []
x_new_vals = []
for i, x in enumerate(iterations):
    x_vals_iters.append(x)
    if i > 0:  # Don't plot tangent from first point
        x_new_vals.append(iterations[i])

# Ensure we have at least 2 points for plotting
if len(x_new_vals) < 2:
    x_new_vals.append(x_new_vals[-1] + 0.01)

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
fig.suptitle('Newton\'s Method for Finding Cube Root of 27', fontsize=16)

# Plot 1: Function and iteration path
ax1.plot(x_vals, f_vals, label='f(x) = x³ - 27', color='blue')
ax1.axhline(y=0, color='red', linestyle='--', label='Solution')
ax1.scatter(x_new_vals, np.zeros_like(x_new_vals), color='green', label='Newton Iterations', zorder=5)

# Plot tangent lines only if we have enough points
if len(x_new_vals) > 1:
    for i in range(min(len(x_new_vals)-1, 3)):  # Only plot first few for clarity
        x_prev = x_new_vals[i]
        x_curr = x_new_vals[i+1]

        # Calculate tangent line
        f_val = x_prev**3 - target
        slope = 3 * x_prev**2
        tangent_y = f_val - slope * (x_prev - x_curr)

        ax1.plot([x_prev, x_curr], [f_val, tangent_y], 'r-', alpha=0.7)
        ax1.plot([x_prev, x_curr], [f_val, 0], 'r--', alpha=0.7)

ax1.set_xlabel('x')
ax1.set_ylabel('f(x)')
ax1.legend()
ax1.grid(True)
ax1.set_ylim(-5, 30)

# Plot 2: Iteration convergence
ax2.plot(range(len(iterations)), iterations, 'bo-', label='Iteration path')
ax2.axhline(y=converged_value, color='red', linestyle='--', label='Converged value')
ax2.set_xlabel('Iteration number')
ax2.set_ylabel('x_n')
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.show()

# Print results
print("Newton's Method for Cube Root of", target)
print("=" * 40)
print(f"Initial guess: {initial_guess}")
print(f"Converged to: {converged_value:.10f}")
print(f"Actual cube root: {27**(1/3):.10f}")
print("\nConvergence achieved in", len(iterations), "iterations")
print("\nIteration details:")
for i, x_val in enumerate(iterations):
    print(f"Iteration {i+1}: {x_val:.10f} (error: {abs(x_val**3 - target):.2e})")