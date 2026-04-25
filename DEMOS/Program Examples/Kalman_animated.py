# Generated: 2026-03-30 13:27:07
# ============================================================

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Slider
from matplotlib.animation import FuncAnimation

# ── Second-order system parameters ────────────────────────────────────────────
omega_n = 2.0          # natural frequency (rad/s)
dt      = 0.05         # time step
T       = 100.0         # simulation duration
N       = int(T / dt)  # number of steps
t_arr   = np.linspace(0, T, N)

# Process / measurement noise
Q_scale = 0.01   # process noise covariance scale
R_meas  = 1.0    # measurement noise variance

# ── Build state-space matrices for given damping ratio ─────────────────────────
def build_system(zeta):
    """
    x = [position, velocity]
    Continuous: x_dot = A_c x + B_c u
    Discretised with Euler for simplicity.
    """
    A_c = np.array([[0,          1         ],
                    [-omega_n**2, -2*zeta*omega_n]])
    # Discrete (Euler)
    A = np.eye(2) + dt * A_c
    B = np.array([[0], [dt]])          # step input
    H = np.array([[1, 0]])             # we observe position only
    Q = Q_scale * np.eye(2)
    R = np.array([[R_meas]])
    return A, B, H, Q, R

# ── Simulate true trajectory + noisy measurements ─────────────────────────────
def simulate(zeta):
    A, B, H, Q, R = build_system(zeta)
    x_true = np.zeros((2, N))
    z_meas = np.zeros(N)
    u      = 1.0   # unit step input

    rng = np.random.default_rng(42)
    x = np.array([[0.0], [0.0]])

    for k in range(N):
        x_true[:, k] = x[:, 0]
        z_meas[k]    = (H @ x)[0, 0] + rng.normal(0, np.sqrt(R_meas))
        w            = rng.multivariate_normal([0, 0], Q).reshape(2, 1)
        x            = A @ x + B * u + w

    return x_true, z_meas, A, B, H, Q, R

# ── Kalman filter ──────────────────────────────────────────────────────────────
def kalman_filter(z_meas, A, B, H, Q, R):
    x_est = np.zeros((2, N))
    P     = np.eye(2)
    x_hat = np.zeros((2, 1))
    u     = 1.0

    for k in range(N):
        # Predict
        x_hat = A @ x_hat + B * u
        P     = A @ P @ A.T + Q
        # Update
        S     = H @ P @ H.T + R
        K     = P @ H.T @ np.linalg.inv(S)
        innov = z_meas[k] - (H @ x_hat)[0, 0]
        x_hat = x_hat + K * innov
        P     = (np.eye(2) - K @ H) @ P
        x_est[:, k] = x_hat[:, 0]

    return x_est

# ── Initial simulation ─────────────────────────────────────────────────────────
zeta_init = 0.5
x_true, z_meas, A, B, H, Q, R = simulate(zeta_init)
x_est = kalman_filter(z_meas, A, B, H, Q, R)

# ── Figure layout ──────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(13, 8))
gs  = gridspec.GridSpec(3, 2, figure=fig, hspace=0.55, wspace=0.38)

ax_pos  = fig.add_subplot(gs[0, :])   # position (full width)
ax_vel  = fig.add_subplot(gs[1, 0])   # velocity
ax_err  = fig.add_subplot(gs[1, 1])   # estimation error
ax_meas = fig.add_subplot(gs[2, 0])   # measurements vs true
ax_gain = fig.add_subplot(gs[2, 1])   # Kalman gain over time

slider_ax = fig.add_axes([0.15, 0.01, 0.70, 0.025])
slider = Slider(slider_ax, 'Damping ratio', 0.001, 2.0,
                valinit=zeta_init, valstep=0.01, color='steelblue')

fig.suptitle("2nd-Order System with Real-Time Kalman Filter Estimation",
             fontsize=13, fontweight='bold', y=0.98)

# ── Helper: compute Kalman gain trace over time ────────────────────────────────
def kalman_gain_trace(A, B, H, Q, R):
    gains = np.zeros(N)
    P     = np.eye(2)
    x_hat = np.zeros((2, 1))
    u     = 1.0
    for k in range(N):
        x_hat = A @ x_hat + B * u
        P     = A @ P @ A.T + Q
        S     = H @ P @ H.T + R
        K     = P @ H.T @ np.linalg.inv(S)
        gains[k] = K[0, 0]
        innov = 0.0
        x_hat = x_hat + K * innov
        P     = (np.eye(2) - K @ H) @ P
    return gains

# ── Animation state ────────────────────────────────────────────────────────────
anim_data = {
    'x_true': x_true,
    'z_meas': z_meas,
    'x_est' : x_est,
    'zeta'  : zeta_init,
    'frame' : 0,
    'running': True,
}

TRAIL = N   # show full history at each frame for clarity; animate pointer

# ── Draw static backgrounds & animated lines ───────────────────────────────────
def init_plot():
    for ax in [ax_pos, ax_vel, ax_err, ax_meas, ax_gain]:
        ax.cla()

    d = anim_data
    xt, xe, zm = d['x_true'], d['x_est'], d['z_meas']
    gains = kalman_gain_trace(A, B, H, Q, R)

    # Position
    ax_pos.set_title(f"Position  (zeta = {d['zeta']:.2f})", fontsize=10)
    ax_pos.plot(t_arr, xt[0], 'b-',  lw=1.5, label='True position')
    ax_pos.plot(t_arr, xe[0], 'r--', lw=1.5, label='KF estimate')
    ax_pos.scatter(t_arr[::4], zm[::4], s=6, c='gray', alpha=0.5, label='Measurements')
    ax_pos.axhline(0, color='k', lw=0.4, ls=':')
    ax_pos.set_xlabel('Time (s)'); ax_pos.set_ylabel('Position')
    ax_pos.legend(fontsize=8, loc='upper right')
    ax_pos.set_xlim(0, T)

    # Velocity
    ax_vel.set_title('Velocity', fontsize=10)
    ax_vel.plot(t_arr, xt[1], 'b-',  lw=1.5, label='True')
    ax_vel.plot(t_arr, xe[1], 'r--', lw=1.5, label='KF estimate')
    ax_vel.axhline(0, color='k', lw=0.4, ls=':')
    ax_vel.set_xlabel('Time (s)'); ax_vel.set_ylabel('Velocity')
    ax_vel.legend(fontsize=8)
    ax_vel.set_xlim(0, T)

    # Error
    pos_err = xt[0] - xe[0]
    vel_err = xt[1] - xe[1]
    ax_err.set_title('Estimation Error', fontsize=10)
    ax_err.plot(t_arr, pos_err, 'g-',  lw=1.2, label='Position error')
    ax_err.plot(t_arr, vel_err, 'm--', lw=1.2, label='Velocity error')
    ax_err.axhline(0, color='k', lw=0.6)
    ax_err.set_xlabel('Time (s)'); ax_err.set_ylabel('Error')
    ax_err.legend(fontsize=8)
    ax_err.set_xlim(0, T)

    # Measurements
    ax_meas.set_title('Measurements vs True Position', fontsize=10)
    ax_meas.plot(t_arr, xt[0], 'b-', lw=1.5, label='True')
    ax_meas.scatter(t_arr[::2], zm[::2], s=5, c='orange', alpha=0.6, label='Noisy meas.')
    ax_meas.set_xlabel('Time (s)'); ax_meas.set_ylabel('Position')
    ax_meas.legend(fontsize=8)
    ax_meas.set_xlim(0, T)

    # Kalman gain
    ax_gain.set_title('Kalman Gain K[0] over Time', fontsize=10)
    ax_gain.plot(t_arr, gains, 'darkorange', lw=1.5)
    ax_gain.set_xlabel('Time (s)'); ax_gain.set_ylabel('Gain')
    ax_gain.set_xlim(0, T)

    # Animated vertical time marker
    for ax in [ax_pos, ax_vel, ax_err, ax_meas, ax_gain]:
        ax.axvline(0, color='k', lw=0.8, ls='--', alpha=0.6)

    plt.tight_layout()

# ── Animation: moving time cursor ─────────────────────────────────────────────
vlines = []

def animate(frame):
    global vlines
    for vl in vlines:
        try:
            vl.remove()
        except Exception:
            pass
    vlines = []
    t_now = t_arr[frame % N]
    for ax in [ax_pos, ax_vel, ax_err, ax_meas, ax_gain]:
        vl = ax.axvline(t_now, color='red', lw=1.0, ls='--', alpha=0.8)
        vlines.append(vl)
    return vlines

# ── Slider callback ────────────────────────────────────────────────────────────
def on_slider(val):
    zeta = slider.val
    anim_data['zeta'] = zeta
    xt, zm, A2, B2, H2, Q2, R2 = simulate(zeta)
    xe = kalman_filter(zm, A2, B2, H2, Q2, R2)
    anim_data['x_true'] = xt
    anim_data['z_meas'] = zm
    anim_data['x_est']  = xe
    # Rebuild static plots
    init_plot()
    fig.canvas.draw_idle()

slider.on_changed(on_slider)

# ── Run ────────────────────────────────────────────────────────────────────────
init_plot()

ani = FuncAnimation(fig, animate, frames=N, interval=40, blit=False, repeat=True)

plt.show()