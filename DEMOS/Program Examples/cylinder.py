import numpy as np
import matplotlib.pyplot as plt

# Define cylinder parameters
r = 2  # Radius
z_max = 5  # Height of the cylinder

# Create grid for x, y, z
theta = np.linspace(0, 2 * np.pi, 100)  # Angle parameter
z = np.linspace(-z_max, z_max, 50)      # Height parameter
x = r * np.outer(np.cos(theta), np.ones_like(z))  # x = r*cos(θ)
y = r * np.outer(np.sin(theta), np.ones_like(z))  # y = r*sin(θ)
z = np.outer(np.ones_like(theta), z)  # z = z (linear height)

# Plot the cylinder
fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')
ax.plot_surface(x, y, z, cmap='viridis', edgecolor='k', linewidth=0.5, alpha=0.7)

# Set labels and title
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title(f'3D Right Circular Cylinder ($x^2 + y^2 = {r}^2$)')

plt.tight_layout()
plt.show()