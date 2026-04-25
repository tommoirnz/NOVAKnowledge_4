# Generated: 2026-04-25 14:14:40
# ============================================================

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

# Define grid
x = np.linspace(-2, 2, 300)
y = np.linspace(0.1, 4, 300)
X, Y = np.meshgrid(x, y)

# Compute function f(x, y) = exp(x) - ln(y)
Z = np.exp(X) - np.log(Y)

# Create figure with two subplots
fig = plt.figure(figsize=(14, 6))
plt.suptitle("f(x, y) = exp(x) - ln(y)", fontsize=15, fontweight='bold', y=0.98)

# --- 3D Surface Plot ---
ax1 = fig.add_subplot(1, 2, 1, projection='3d')
surf = ax1.plot_surface(X, Y, Z, cmap=cm.viridis, edgecolor='none', alpha=0.9)
ax1.set_title("3D Surface Plot", fontsize=12, pad=10)
ax1.set_xlabel("x", fontsize=11, labelpad=8)
ax1.set_ylabel("y", fontsize=11, labelpad=8)
ax1.set_zlabel("f(x, y)", fontsize=11, labelpad=8)
ax1.tick_params(labelsize=8)
cbar1 = fig.colorbar(surf, ax=ax1, shrink=0.5, aspect=10, pad=0.1)
cbar1.set_label("f(x, y)", fontsize=10)

# --- 2D Contour / Level Curve Plot ---
ax2 = fig.add_subplot(1, 2, 2)
levels = np.linspace(Z.min(), Z.max(), 30)
contourf = ax2.contourf(X, Y, Z, levels=levels, cmap=cm.viridis)
contour_lines = ax2.contour(X, Y, Z, levels=15, colors='white', linewidths=0.5, alpha=0.6)
ax2.clabel(contour_lines, inline=True, fontsize=7, fmt="%.1f")
ax2.set_title("2D Contour Plot (Level Curves)", fontsize=12)
ax2.set_xlabel("x", fontsize=11)
ax2.set_ylabel("y", fontsize=11)
cbar2 = fig.colorbar(contourf, ax=ax2)
cbar2.set_label("f(x, y)", fontsize=10)

plt.tight_layout()
plt.show()