import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.patches import Circle
from matplotlib.collections import PatchCollection
from matplotlib.colors import Normalize

# Parameters (physical units for intuition)
mass = 1.0      # Mass parameter (e.g., Sun-like mass)
G = 1.0         # Gravitational constant (simplified)
c = 1.0         # Speed of light (simplified)
x_max = 6.0     # Wider view for lensing effects
steps = 200     # High resolution for smooth paths
num_light_rays = 30  # Number of light paths to draw

# Create grid
x = np.linspace(-x_max, x_max, steps)
y = np.linspace(-x_max, x_max, steps)
X, Y = np.meshgrid(x, y)
r = np.sqrt(X**2 + Y**2 + 1e-6)  # Avoid division by zero

# Spacetime curvature (simplified metric perturbation)
Z = -mass / (r**2 + 0.1)  # Depression in the "well"
Z = Z * 5  # Scale for visibility

# Create figure
fig = plt.figure(figsize=(14, 8))
ax = fig.add_subplot(111, projection='3d')

# Plot the warped spacetime surface
surf = ax.plot_surface(X, Y, Z,
                      cmap='plasma',
                      alpha=0.7,
                      linewidth=0,
                      antialiased=True,
                      vmin=Z.min(),
                      vmax=Z.max())

# Add mass at origin (red sphere)
mass_center = 0.3
mass_color = 'red'
mass_alpha = 0.8

# Create a transparent red circle at the bottom of the well
u = np.linspace(0, 2 * np.pi, 100)
v = np.linspace(0, np.pi, 2)
u, v = np.meshgrid(u, v)
x_mass = mass_center * np.cos(u) * np.sin(v)
y_mass = mass_center * np.sin(u) * np.sin(v)
z_mass = np.ones_like(x_mass) * Z[steps//2, steps//2]

ax.plot_surface(x_mass, y_mass, z_mass, color=mass_color, alpha=mass_alpha, linewidth=0)

# Label mass
ax.text(0, 0, Z.min() - 0.1, 'Massive Object', ha='center', va='bottom',
        color=mass_color, fontsize=12, weight='bold')

# --- Lensing Effects: Light Paths ---
# Background "galaxy" (light source)
galaxy_radius = 0.8
galaxy_color = 'cyan'
galaxy_alpha = 0.6

u_galaxy = np.linspace(0, 2 * np.pi, 100)
v_galaxy = np.linspace(0, np.pi, 2)
u_galaxy, v_galaxy = np.meshgrid(u_galaxy, v_galaxy)
x_galaxy = 3 + galaxy_radius * np.cos(u_galaxy) * np.sin(v_galaxy)
y_galaxy = 3 + galaxy_radius * np.sin(u_galaxy) * np.sin(v_galaxy)
z_galaxy = np.ones_like(x_galaxy) * Z[steps//2, steps//2]

ax.plot_surface(x_galaxy, y_galaxy, z_galaxy, color=galaxy_color, alpha=galaxy_alpha, linewidth=0)

# Light rays (follow curved spacetime)
for i in range(num_light_rays):
    # Start at random point behind the mass (e.g., at (3,3))
    start_x = 3 + np.random.uniform(-0.5, 0.5)
    start_y = 3 + np.random.uniform(-0.5, 0.5)

    # Path is a "straight line" in the warped spacetime (geodesic)
    path_x = np.linspace(start_x, -1.5, 100)  # End near the mass
    path_y = np.linspace(start_y, -1.5, 100)
    path_z = []
    for x, y in zip(path_x, path_y):
        x_idx = int((x + x_max) * steps / (2 * x_max))
        y_idx = int((y + x_max) * steps / (2 * x_max))
        path_z.append(Z[x_idx, y_idx])

    # Draw the path
    ax.plot(path_x, path_y, path_z, color='yellow', linewidth=1.5, alpha=0.7)

# Lens arcs (simplified)
for angle in np.linspace(0, 2*np.pi, 8):
    # Circular path around the mass
    radius = np.linspace(0.5, 2, 50)
    path_x = radius * np.cos(angle)
    path_y = radius * np.sin(angle)
    path_z = []
    for x, y in zip(path_x, path_y):
        x_idx = int((x + x_max) * steps / (2 * x_max))
        y_idx = int((y + x_max) * steps / (2 * x_max))
        path_z.append(Z[x_idx, y_idx])

    ax.plot(path_x, path_y, path_z, color='white', linewidth=1.5, alpha=0.5)

# Labels and title
ax.set_title("3D Spacetime Curvature + Gravitational Lensing", pad=20)
ax.set_xlabel("X Coordinate")
ax.set_ylabel("Y Coordinate")
ax.set_zlabel("Curvature Depth (Z)")

# Create a colorbar for curvature strength
norm = Normalize(vmin=Z.min(), vmax=Z.max())
sm = plt.cm.ScalarMappable(norm=norm, cmap='plasma')
sm.set_array([])  # Dummy array, since we don't have a figure for the colorbar
fig.colorbar(sm, ax=ax, shrink=0.5, aspect=5, label='Curvature Strength')

plt.tight_layout()
plt.show()
