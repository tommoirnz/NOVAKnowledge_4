import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Define the quadratic function: f(x, y) = x^2 + 4y^2
def f(x, y):
    return x**2 + 4*y**2

# Gradient of the function: ∇f = [2x, 8y]
def gradient(x, y):
    return np.array([2*x, 8*y])

# Steepest descent algorithm
def steepest_descent(start_point, learning_rate=0.1, max_iter=100, tol=1e-6):
    x, y = start_point
    path = [start_point.copy()]

    for i in range(max_iter):
        grad = gradient(x, y)
        x_new = x - learning_rate * grad[0]
        y_new = y - learning_rate * grad[1]

        # Check convergence
        if np.linalg.norm(np.array([x_new - x, y_new - y])) < tol:
            print(f"Converged in {i} iterations.")
            break

        x, y = x_new, y_new
        path.append([x, y])

    return np.array(path)

# Generate a grid for plotting the function
x = np.linspace(-2, 2, 100)
y = np.linspace(-1, 1, 100)
X, Y = np.meshgrid(x, y)
Z = f(X, Y)

# Find the start point in the grid (using nearest neighbor)
start = np.array([1.5, 0.5])
# Calculate distance to all grid points
distances = (X - start[0])**2 + (Y - start[1])**2
start_idx = np.unravel_index(np.argmin(distances), distances.shape)
start_point_grid = np.array([X[start_idx], Y[start_idx]])

# Run steepest descent from the exact start point (not the grid point)
path = steepest_descent(start, learning_rate=0.1)

# Create a figure with two subplots
fig = plt.figure(figsize=(12, 5))

# 3D plot of the function
ax1 = fig.add_subplot(121, projection='3d')
surf = ax1.plot_surface(X, Y, Z, alpha=0.7, color='blue', rstride=5, cstride=5)
ax1.scatter(X[start_idx], Y[start_idx], Z[start_idx], color='red', s=100, label='Start')
ax1.plot(path[:, 0], path[:, 1], f(path[:, 0], path[:, 1]), 'r-', label='Descent Path')
ax1.set_xlabel('x')
ax1.set_ylabel('y')
ax1.set_zlabel('f(x, y)')
ax1.legend()

# 2D contour plot
ax2 = fig.add_subplot(122)
contour = ax2.contour(X, Y, Z, levels=20, cmap='viridis')
ax2.plot(path[:, 0], path[:, 1], 'ro-', label='Descent Path')
ax2.scatter(start[0], start[1], color='red', s=100, label='Start')
ax2.clabel(contour, inline=True, fontsize=8)
ax2.set_xlabel('x')
ax2.set_ylabel('y')
ax2.legend()

plt.tight_layout()
plt.show()