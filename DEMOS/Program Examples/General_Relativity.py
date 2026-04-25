# Generated: 2026-04-06 19:05:07
# ============================================================

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from scipy.integrate import solve_ivp

# ── Parameters ──────────────────────────────────────────────────────────────
GM = 1.0          # Gravitational parameter (normalised)
RS = 0.3          # Schwarzschild radius (event horizon proxy)
GRID_N = 120      # Grid resolution
GRID_R = 4.0      # Grid half-extent

# ── Spacetime curvature surface ──────────────────────────────────────────────
x = np.linspace(-GRID_R, GRID_R, GRID_N)
y = np.linspace(-GRID_R, GRID_R, GRID_N)
X, Y = np.meshgrid(x, y)
R = np.sqrt(X**2 + Y**2)
R_safe = np.where(R < RS, RS, R)          # clamp inside event horizon

# Newtonian potential well: Z = -GM/r  (clamped for visualisation)
Z = -GM / R_safe
Z_clamp = np.clip(Z, -3.5, 0.0)

# Curvature intensity for colour mapping (|∇²Φ| ∝ 1/r³ outside horizon)
curvature = GM / R_safe**3
curvature_norm = np.log1p(curvature)      # log scale for dynamic range

# ── Geodesic ODE (Schwarzschild-like in 2-D polar, weak-field) ───────────────
# Equations of motion: r'' = -GM/r² + L²/r³   (effective potential)
# Using state vector [r, phi, dr/dt, dphi/dt]
L = np.sqrt(GM * 2.0)    # specific angular momentum for near-circular orbit
E = 0.5 * (L**2 / (2.0**2)) - GM / 2.0   # energy at r0 = 2.0

def geodesic(t, state):
    r, phi, rdot, phidot = state
    if r < RS:
        r = RS
    rddot = -GM / r**2 + L**2 / r**3
    phiddot = -2.0 * rdot * phidot / r
    return [rdot, phidot, rddot, phiddot]

r0 = 2.0
phidot0 = L / r0**2
state0 = [r0, 0.0, 0.0, phidot0]
t_span = (0, 80)
t_eval = np.linspace(*t_span, 8000)

sol = solve_ivp(geodesic, t_span, state0, t_eval=t_eval,
                method='DOP853', rtol=1e-9, atol=1e-11)

r_geo = sol.y[0]
phi_geo = sol.y[1]
x_geo = r_geo * np.cos(phi_geo)
y_geo = r_geo * np.sin(phi_geo)

# ── Figure layout ─────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 8), facecolor='#0a0a1a')

# ── Subplot 1: 3-D gravity well ───────────────────────────────────────────────
ax1 = fig.add_subplot(121, projection='3d', facecolor='#0a0a1a')

surf = ax1.plot_surface(
    X, Y, Z_clamp,
    facecolors=cm.inferno(curvature_norm / curvature_norm.max()),
    rstride=2, cstride=2, linewidth=0, antialiased=True, alpha=0.92
)

# Event horizon ring
theta_ring = np.linspace(0, 2 * np.pi, 200)
xr = RS * np.cos(theta_ring)
yr = RS * np.sin(theta_ring)
zr = np.full_like(xr, -GM / RS)
ax1.plot(xr, yr, zr, color='cyan', linewidth=2.0, zorder=10)

# Star marker
ax1.scatter([0], [0], [-GM / RS], color='yellow', s=180, zorder=11,
            edgecolors='white', linewidths=1.5)

# Annotations
ax1.text(RS + 0.05, 0, -GM / RS + 0.15,
         'Event Horizon\n(Schwarzschild radius)',
         color='cyan', fontsize=7.5, ha='left')
ax1.text(2.5, 2.5, -0.35,
         'Curvature gradient\n(colour = intensity)',
         color='#ffaa44', fontsize=7.5, ha='center')
ax1.text(0, 0, -GM / RS - 0.25,
         'Stellar mass\n(GM=1)', color='yellow',
         fontsize=7.5, ha='center')

ax1.set_xlabel('x  [Schwarzschild units]', color='white', labelpad=8, fontsize=9)
ax1.set_ylabel('y  [Schwarzschild units]', color='white', labelpad=8, fontsize=9)
ax1.set_zlabel('Gravitational potential  -GM/r', color='white', labelpad=8, fontsize=9)
ax1.set_title('Spacetime Curvature — Gravity Well\n(General Relativity)',
              color='white', fontsize=11, pad=10)

ax1.tick_params(colors='white', labelsize=7)
ax1.xaxis.pane.fill = False
ax1.yaxis.pane.fill = False
ax1.zaxis.pane.fill = False
ax1.xaxis.pane.set_edgecolor('#333355')
ax1.yaxis.pane.set_edgecolor('#333355')
ax1.zaxis.pane.set_edgecolor('#333355')
ax1.grid(True, color='#222244', linewidth=0.4)
ax1.view_init(elev=28, azim=-55)

# Colour bar
mappable = cm.ScalarMappable(cmap='inferno')
mappable.set_array(curvature_norm)
cbar = fig.colorbar(mappable, ax=ax1, shrink=0.55, pad=0.08, aspect=20)
cbar.set_label('log(1 + Curvature)  [arb. units]', color='white', fontsize=8)
cbar.ax.yaxis.set_tick_params(color='white', labelsize=7)
plt.setp(cbar.ax.yaxis.get_ticklabels(), color='white')

# ── Subplot 2: Geodesic orbital path ─────────────────────────────────────────
ax2 = fig.add_subplot(122, facecolor='#0a0a1a')

# Background curvature heatmap
r_bg = np.sqrt(X**2 + Y**2)
r_bg_safe = np.where(r_bg < RS, RS, r_bg)
potential_bg = -GM / r_bg_safe
ax2.contourf(X, Y, potential_bg, levels=60, cmap='inferno', alpha=0.75)
cbar2 = fig.colorbar(
    plt.cm.ScalarMappable(
        norm=plt.Normalize(potential_bg.min(), potential_bg.max()),
        cmap='inferno'),
    ax=ax2, shrink=0.75, pad=0.02, aspect=25)
cbar2.set_label('Gravitational potential  -GM/r', color='white', fontsize=8)
cbar2.ax.yaxis.set_tick_params(color='white', labelsize=7)
plt.setp(cbar2.ax.yaxis.get_ticklabels(), color='white')

# Event horizon circle
eh_circle = plt.Circle((0, 0), RS, color='cyan', fill=False,
                        linewidth=1.8, linestyle='--', label='Event horizon (r_s)')
ax2.add_patch(eh_circle)

# Geodesic path — colour by speed
speed = np.sqrt(np.diff(x_geo)**2 + np.diff(y_geo)**2)
speed_norm = speed / speed.max()
for i in range(len(x_geo) - 1):
    ax2.plot(x_geo[i:i+2], y_geo[i:i+2],
             color=cm.cool(speed_norm[i]), linewidth=0.8, alpha=0.85)

# Geodesic colour bar proxy
geo_mappable = cm.ScalarMappable(
    norm=plt.Normalize(speed.min(), speed.max()), cmap='cool')
geo_mappable.set_array(speed)
cbar3 = fig.colorbar(geo_mappable, ax=ax2, shrink=0.45, pad=0.12, aspect=20,
                     location='left')
cbar3.set_label('Orbital speed  [arb.]', color='white', fontsize=8)
cbar3.ax.yaxis.set_tick_params(color='white', labelsize=7)
plt.setp(cbar3.ax.yaxis.get_ticklabels(), color='white')

# Star
ax2.scatter(0, 0, color='yellow', s=220, zorder=10,
            edgecolors='white', linewidths=1.5, label='Central star')

# Annotations
ax2.annotate('Orbital geodesic\n(curved spacetime path)',
             xy=(x_geo[1200], y_geo[1200]),
             xytext=(1.8, 2.8),
             color='white', fontsize=8,
             arrowprops=dict(arrowstyle='->', color='white', lw=1.2),
             ha='center')
ax2.annotate('Event horizon\n(Schwarzschild radius r_s)',
             xy=(RS * np.cos(np.pi / 4), RS * np.sin(np.pi / 4)),
             xytext=(-2.8, 2.5),
             color='cyan', fontsize=8,
             arrowprops=dict(arrowstyle='->', color='cyan', lw=1.2),
             ha='center')
ax2.text(0, -3.6,
         'Geodesic precesses due to spacetime curvature\n'
         '(analogous to Mercury perihelion advance)',
         color='#aaaacc', fontsize=8, ha='center')

ax2.set_xlim(-GRID_R, GRID_R)
ax2.set_ylim(-GRID_R, GRID_R)
ax2.set_aspect('equal')
ax2.set_xlabel('x  [Schwarzschild units]', color='white', fontsize=9)
ax2.set_ylabel('y  [Schwarzschild units]', color='white', fontsize=9)
ax2.set_title('Geodesic Orbital Path — Test Particle\n(Schwarzschild Metric, Weak-Field)',
              color='white', fontsize=11, pad=10)
ax2.tick_params(colors='white', labelsize=8)
ax2.legend(loc='lower right', fontsize=8, facecolor='#1a1a2e',
           edgecolor='white', labelcolor='white')
for spine in ax2.spines.values():
    spine.set_edgecolor('#333355')

# ── Main title ────────────────────────────────────────────────────────────────
plt.suptitle(
    'General Relativity — Spacetime Curvature and Geodesic Motion\n'
    'USS NOVA  |  Stardate 103968.5  |  Astrophysics Simulation Module',
    color='white', fontsize=12, y=0.98, fontweight='bold')

fig.patch.set_facecolor('#0a0a1a')
plt.tight_layout()
plt.show()