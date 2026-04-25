import matplotlib.pyplot as plt

def newton_sqrt(a, tolerance=1e-10, max_iterations=100):
    """
    Compute the square root of 'a' using Newton's method and track convergence.

    Parameters:
    - a: The number to compute the square root of.
    - tolerance: The desired precision (default: 1e-10).
    - max_iterations: Maximum number of iterations (default: 100).

    Returns:
    - x: The square root of 'a'.
    - history: List of iterates (for plotting).
    """
    if a < 0:
        raise ValueError("Cannot compute the square root of a negative number.")

    x = a  # Initial guess
    history = [x]  # Track all iterates for plotting

    for _ in range(max_iterations):
        x_next = (x + a / x) / 2
        history.append(x_next)  # Record the new iterate
        if abs(x_next - x) < tolerance:
            return x_next, history
        x = x_next

    return x, history  # Return best approximation and history if max_iterations reached

# Compute the square root of 4 and get convergence history
a = 4
result, history = newton_sqrt(a)

# Plot the convergence over iterations
iterations = range(len(history))
plt.figure(figsize=(8, 4))
plt.plot(iterations, history, 'b-o', label='Newton Iterates')
plt.axhline(y=2, color='r', linestyle='--', label='True Value (√4 = 2)')
plt.xlabel('Iteration')
plt.ylabel('Approximation to √4')
plt.title('Convergence of Newton’s Method for √4')
plt.legend()
plt.grid(True)
plt.show()

print(f"The square root of {a} is approximately {result}")