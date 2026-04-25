# Generated: 2026-04-25 14:13:15
# ============================================================

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

# Define grid
x = np.linspace(-2, 2, 300)
y = np.linspace(1e-6, 4, 300)  # y in (0, 4], avoid log(0)
X, Y = np.meshgrid(x, y)

# Compute function f(x, y) = exp(x) - ln(y)
Z = np.exp(X) - np.log(Y)

# Create figure with two subplots
fig = plt.figure(figsize=(14, 6))
plt.suptitle("f(x, y) = exp(x) - ln(y)", fontsize=15, fontweight='bold', y=0.98)

# --- 3D Surface Plot ---
ax1 = fig.add_subplot(1, 2, 1, projection='3d')
surf = ax1.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none', alpha=0.9)
fig.colorbar(surf, ax=ax1, shrink=0.5, aspect=10, label='f(x, y)')
ax1.set_title("3D Surface Plot", fontsize=13)
ax1.set_xlabel("x", fontsize=11)
ax1.set_ylabel("y", fontsize=11)
ax1.set_zlabel("f(x, y)", fontsize=11)
ax1.set_xlim(-2, 2)
ax1.set_ylim(0, 4)
ax1.view_init(elev=30, azim=-60)

# --- 2D Contour Plot ---
ax2 = fig.add_subplot(1, 2, 2)
levels = np.linspace(Z.min(), Z.max(), 40)
contourf = ax2.contourf(X, Y, Z, levels=levels, cmap='plasma')
contour_lines = ax2.contour(X, Y, Z, levels=15, colors='white', linewidths=0.5, alpha=0.6)
ax2.clabel(contour_lines, inline=True, fontsize=7, fmt="%.1f")
fig.colorbar(contourf, ax=ax2, label='f(x, y)')
ax2.set_title("2D Contour Plot", fontsize=13)
ax2.set_xlabel("x", fontsize=11)
ax2.set_ylabel("y", fontsize=11)
ax2.set_xlim(-2, 2)
ax2.set_ylim(0, 4)

plt.tight_layout()
plt.show()