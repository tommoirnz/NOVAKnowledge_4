import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patheffects as pe

# --- Setup dark space theme ---
plt.style.use('dark_background')
fig = plt.figure(figsize=(14, 9), facecolor='#000010')
fig.patch.set_facecolor('#000010')

# Layout: main simulation on left, equations panel on right
ax_sim = fig.add_axes([0.0, 0.0, 0.72, 1.0])
ax_eq = fig.add_axes([0.72, 0.0, 0.28, 1.0])

ax_sim.set_facecolor('#000010')
ax_eq.set_facecolor('#050520')

for spine in ax_eq.spines.values():
    spine.set_color('#1a1a4a')
ax_eq.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

# --- Simulation parameters ---
G = 6.674e-11  # real G, but we'll use scaled units
G_sim = 200.0   # simulation G
dt = 0.016

SIM_W = 200.0
SIM_H = 140.0

ax_sim.set_xlim(-SIM_W/2, SIM_W/2)
ax_sim.set_ylim(-SIM_H/2, SIM_H/2)
ax_sim.set_aspect('equal')
ax_sim.axis('off')

# --- Starfield background ---
np.random.seed(42)
n_stars = 300
star_x = np.random.uniform(-SIM_W/2, SIM_W/2, n_stars)
star_y = np.random.uniform(-SIM_H/2, SIM_H/2, n_stars)
star_sizes = np.random.uniform(0.2, 2.5, n_stars)
star_alpha = np.random.uniform(0.3, 1.0, n_stars)
ax_sim.scatter(star_x, star_y, s=star_sizes, c='white', alpha=0.6, zorder=0)

# --- Bodies definition ---
# Compute orbital velocity for circular orbit: v = sqrt(G*M/r)
def orbital_v(G_s, M, r):
    return np.sqrt(G_s * M / r)

# Redefine velocities with proper values
M_star = 3000.0
r_A = 60.0
v_A = orbital_v(G_sim, M_star, r_A)   # sqrt(200*3000/60) = 100

r_B = 90.0
v_B = orbital_v(G_sim, M_star, r_B)   # sqrt(200*3000/90) = 81.65

# Moon around planet A (mass 50)
M_A = 50.0
r_moon = 12.0
v_moon_local = orbital_v(G_sim, M_A, r_moon)  # sqrt(200*50/12) = 28.87

bodies_init = [
    # x,     y,    vx,          vy,           mass,   radius, color,      name
    [0.0,    0.0,   0.0,         0.0,          3000.0, 6.0,   '#FFD700',  'Star'],
    [60.0,   0.0,   0.0,         v_A,          50.0,   3.0,   '#4FC3F7',  'Planet A'],
    [-90.0,  0.0,   0.0,        -v_B,          30.0,   2.5,   '#EF5350',  'Planet B'],
    [80.0,   55.0, -15.0,       -25.0,         5.0,    1.5,   '#B2FF59',  'Comet'],
    [60.0,   12.0,  0.0,         v_A+v_moon_local, 3.0, 1.0, '#CE93D8',  'Moon'],
]

N = len(bodies_init)
pos = np.array([[b[0], b[1]] for b in bodies_init], dtype=float)
vel = np.array([[b[2], b[3]] for b in bodies_init], dtype=float)
mass = np.array([b[4] for b in bodies_init], dtype=float)
radii = np.array([b[5] for b in bodies_init], dtype=float)
colors = [b[6] for b in bodies_init]
names = [b[7] for b in bodies_init]

TRAIL_LEN = 120
trails = [[] for _ in range(N)]

# --- Draw objects ---
body_circles = []
trail_lines = []
label_texts = []

for i in range(N):
    # Glow effect via multiple circles
    glow = Circle((pos[i,0], pos[i,1]), radii[i]*2.5,
                  color=colors[i], alpha=0.08, zorder=3)
    ax_sim.add_patch(glow)

    circ = Circle((pos[i,0], pos[i,1]), radii[i],
                  color=colors[i], zorder=5)
    ax_sim.add_patch(circ)
    body_circles.append((glow, circ))

    line, = ax_sim.plot([], [], '-', color=colors[i], alpha=0.5,
                        linewidth=0.8, zorder=2)
    trail_lines.append(line)

    txt = ax_sim.text(pos[i,0], pos[i,1]+radii[i]+2, names[i],
                      color=colors[i], fontsize=6.5, ha='center', va='bottom',
                      zorder=6, fontweight='bold')
    txt.set_path_effects([pe.withStroke(linewidth=1.5, foreground='black')])
    label_texts.append(txt)

# --- Title on simulation ---
title_txt = ax_sim.text(0, SIM_H/2 - 5, 'GRAVITY SIMULATION',
                        color='white', fontsize=14, ha='center', va='top',
                        fontweight='bold', zorder=10,
                        fontfamily='monospace')
title_txt.set_path_effects([pe.withStroke(linewidth=3, foreground='#000030')])

subtitle_txt = ax_sim.text(0, SIM_H/2 - 12,
                           'Newtonian Gravity -- Proof that Gravity is Real',
                           color='#aaaacc', fontsize=7.5, ha='center', va='top',
                           zorder=10, style='italic')

# Force arrow (between star and planet A)
arrow_obj = ax_sim.annotate('', xy=(0,0), xytext=(0,0),
                             arrowprops=dict(arrowstyle='->', color='#FF8F00',
                                            lw=1.5, alpha=0.8),
                             zorder=7)

# Distance text
dist_text = ax_sim.text(-SIM_W/2+3, -SIM_H/2+3, '',
                        color='#FF8F00', fontsize=7, zorder=10,
                        fontfamily='monospace')

# Time counter
time_text = ax_sim.text(SIM_W/2-3, -SIM_H/2+3, '',
                        color='#888888', fontsize=7, ha='right', zorder=10,
                        fontfamily='monospace')

# --- Equations panel ---
ax_eq.set_xlim(0, 1)
ax_eq.set_ylim(0, 1)
ax_eq.axis('off')

eq_title = ax_eq.text(0.5, 0.97, 'PHYSICS EQUATIONS',
                      color='#FFD700', fontsize=10, ha='center', va='top',
                      fontweight='bold', fontfamily='monospace',
                      transform=ax_eq.transAxes)
eq_title.set_path_effects([pe.withStroke(linewidth=2, foreground='#050520')])

# Divider - use ax.plot instead of axhline to allow transform
ax_eq.plot([0, 1], [0.94, 0.94], color='#FFD700', alpha=0.4, linewidth=0.8,
           transform=ax_eq.transAxes)

equations = [
    ("Newton's Law of", 0.91, '#FFFFFF', 9, 'bold', False),
    ("Universal Gravitation:", 0.87, '#FFFFFF', 9, 'bold', False),
    ("", 0.84, '#FFFFFF', 8, 'normal', False),
    (r"$F = G \frac{m_1 m_2}{r^2}$", 0.80, '#FFD700', 10, 'bold', True),
    ("", 0.76, '#FFFFFF', 8, 'normal', False),
    ("Where:", 0.73, '#AAAACC', 8, 'normal', False),
    ("F = gravitational force (N)", 0.69, '#4FC3F7', 7.5, 'normal', False),
    (r"G = 6.674$\times$10$^{-11}$ N m$^2$ kg$^{-2}$", 0.65, '#4FC3F7', 7.5, 'normal', False),
    ("m1, m2 = masses (kg)", 0.61, '#4FC3F7', 7.5, 'normal', False),
    ("r = distance between bodies", 0.57, '#4FC3F7', 7.5, 'normal', False),
    ("", 0.53, '#FFFFFF', 8, 'normal', False),
    ("Orbital Velocity:", 0.50, '#FFFFFF', 9, 'bold', False),
    (r"$v = \sqrt{\frac{GM}{r}}$", 0.46, '#B2FF59', 10, 'bold', True),
    ("", 0.42, '#FFFFFF', 8, 'normal', False),
    ("Gravitational Accel:", 0.39, '#FFFFFF', 9, 'bold', False),
    (r"$g = \frac{GM}{r^2}$", 0.35, '#EF5350', 10, 'bold', True),
    ("", 0.31, '#FFFFFF', 8, 'normal', False),
    ("Energy Conservation:", 0.28, '#FFFFFF', 9, 'bold', False),
    (r"$E = KE + PE = const$", 0.24, '#CE93D8', 9, 'bold', True),
    (r"$KE = \frac{1}{2}mv^2$", 0.20, '#CE93D8', 8, 'normal', False),
    (r"$PE = -\frac{Gm_1m_2}{r}$", 0.16, '#CE93D8', 8, 'normal', False),
]

for (text, y, color, fsize, fw, box) in equations:
    if box:
        bbox_props = dict(boxstyle='round,pad=0.3', facecolor='#0a0a30',
                         edgecolor=color, alpha=0.7)
        ax_eq.text(0.5, y, text, color=color, fontsize=fsize,
                   ha='center', va='center', fontweight=fw,
                   fontfamily='monospace', transform=ax_eq.transAxes,
                   bbox=bbox_props)
    else:
        ax_eq.text(0.5, y, text, color=color, fontsize=fsize,
                   ha='center', va='center', fontweight=fw,
                   transform=ax_eq.transAxes)

# Divider - use ax.plot instead of axhline
ax_eq.plot([0, 1], [0.12, 0.12], color='#333366', alpha=0.6, linewidth=0.8,
           transform=ax_eq.transAxes)

# Live force display
force_label = ax_eq.text(0.5, 0.09,
                         'Live Force (Star→Planet A):',
                         color='#888888', fontsize=7, ha='center',
                         transform=ax_eq.transAxes)
force_val_text = ax_eq.text(0.5, 0.05, 'F = --- N',
                            color='#FF8F00', fontsize=8.5, ha='center',
                            fontweight='bold', fontfamily='monospace',
                            transform=ax_eq.transAxes)

flat_earth_text = ax_eq.text(0.5, 0.01,
                             '"Gravity is not a theory, it is the law."',
                             color='#555577', fontsize=6, ha='center',
                             style='italic', transform=ax_eq.transAxes)

# --- Physics update ---
def compute_forces(pos, mass):
    N = len(mass)
    forces = np.zeros((N, 2))
    for i in range(N):
        for j in range(i+1, N):
            diff = pos[j] - pos[i]
            dist = np.linalg.norm(diff)
            dist = max(dist, radii[i] + radii[j] + 0.5)  # softening
            F_mag = G_sim * mass[i] * mass[j] / (dist**2)
            F_vec = F_mag * diff / dist
            forces[i] += F_vec
            forces[j] -= F_vec
    return forces

frame_count = [0]

def animate(frame):
    global pos, vel, trails

    # Multiple physics steps per frame for stability
    steps = 3
    for _ in range(steps):
        forces = compute_forces(pos, mass)
        acc = forces / mass[:, np.newaxis]
        vel += acc * dt
        pos += vel * dt

        # Boundary wrapping (soft)
        for i in range(N):
            if abs(pos[i, 0]) > SIM_W/2 + 20:
                pos[i, 0] *= -0.98
                vel[i, 0] *= -0.5
            if abs(pos[i, 1]) > SIM_H/2 + 20:
                pos[i, 1] *= -0.98
                vel[i, 1] *= -0.5

    frame_count[0] += 1

    # Update trails
    for i in range(N):
        trails[i].append(pos[i].copy())
        if len(trails[i]) > TRAIL_LEN:
            trails[i].pop(0)

    # Update visuals
    for i in range(N):
        glow, circ = body_circles[i]
        circ.center = (pos[i, 0], pos[i, 1])
        glow.center = (pos[i, 0], pos[i, 1])
        label_texts[i].set_position((pos[i, 0], pos[i, 1] + radii[i] + 2))

        # Trail with fading
        if len(trails[i]) > 2:
            tx = [t[0] for t in trails[i]]
            ty = [t[1] for t in trails[i]]
            trail_lines[i].set_data(tx, ty)
            alpha = min(0.6, 0.15 + 0.45 * len(trails[i]) / TRAIL_LEN)
            trail_lines[i].set_alpha(alpha)

    # Force arrow: star to planet A
    star_pos = pos[0]
    pA_pos = pos[1]
    arrow_obj.xy = (pA_pos[0], pA_pos[1])
    arrow_obj.set_position((star_pos[0], star_pos[1]))

    # Distance & force display
    r = np.linalg.norm(pA_pos - star_pos)
    F = G_sim * mass[0] * mass[1] / max(r**2, 1.0)
    dist_text.set_text(f'r(Star-PlanetA) = {r:.1f} units')
    force_val_text.set_text(f'F = {F:.1f} sim-N')

    t = frame_count[0] * dt * steps
    time_text.set_text(f't = {t:.1f} s')

    # Return all artists that need to be updated
    artists = []
    for glow, circ in body_circles:
        artists.extend([glow, circ])
    artists.extend(trail_lines)
    artists.extend(label_texts)
    artists.extend([dist_text, force_val_text, time_text, arrow_obj])
    return artists

# --- Run animation ---
ani = animation.FuncAnimation(
    fig, animate,
    frames=2000,
    interval=20,
    blit=True,
    cache_frame_data=False
)

plt.suptitle('Gravity Simulation -- Newton\'s Universal Law of Gravitation',
             y=0.98, color='white', fontsize=11, fontweight='bold',
             fontfamily='monospace')

plt.tight_layout()
plt.show()