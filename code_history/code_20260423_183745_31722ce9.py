# Generated: 2026-04-23 18:37:45
# ============================================================

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Slider

# ── Reproducibility ──────────────────────────────────────────────────────────
np.random.seed(42)

# ── Simulation parameters ─────────────────────────────────────────────────────
N = 300
t = np.arange(N)
shift = N // 2          # parameter shift at t = 150

# True AR(2) parameters (two regimes)
phi1_true = np.where(t < shift, 0.9, 0.5)
phi2_true = np.where(t < shift, -0.3, 0.4)

obs_noise_std = 0.5

# Simulate AR(2) signal
y = np.zeros(N)
y[0] = np.random.randn()
y[1] = np.random.randn()
for i in range(2, N):
    y[i] = (phi1_true[i] * y[i-1] +
            phi2_true[i] * y[i-2] +
            obs_noise_std * np.random.randn())

# ── Kalman Filter for time-varying AR(2) coefficients ────────────────────────
def run_kalman(y, Q_val, R_val):
    """
    State vector: x = [phi1, phi2]
    Observation:  y[t] = phi1*y[t-1] + phi2*y[t-2] + noise
    State transition: x[t] = x[t-1] + process_noise  (random walk)
    """
    n_state = 2
    x_est = np.zeros((N, n_state))
    P_est = np.zeros((N, n_state, n_state))

    # Initialise
    x = np.array([0.0, 0.0])
    P = np.eye(n_state) * 1.0
    Q = np.eye(n_state) * Q_val
    R = R_val

    phi1_hat = np.zeros(N)
    phi2_hat = np.zeros(N)

    for i in range(2, N):
        # Observation vector
        H = np.array([[y[i-1], y[i-2]]])   # shape (1, 2)

        # Predict
        x_pred = x.copy()
        P_pred = P + Q

        # Innovation
        z = y[i]
        z_hat = H @ x_pred
        S = H @ P_pred @ H.T + R
        K = P_pred @ H.T / S[0, 0]   # shape (2,)

        # Update
        x = x_pred + K * (z - z_hat[0])
        P = (np.eye(n_state) - np.outer(K, H)) @ P_pred

        phi1_hat[i] = x[0]
        phi2_hat[i] = x[1]

    return phi1_hat, phi2_hat

# ── Initial filter run ────────────────────────────────────────────────────────
Q_init = 0.01
R_init = 0.25

phi1_hat, phi2_hat = run_kalman(y, Q_init, R_init)

# ── Figure layout ─────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(13, 9))
fig.suptitle("AR(2) Kalman Filter - Interactive Parameter Estimation", y=0.98)

gs = gridspec.GridSpec(3, 1, figure=fig, hspace=0.55)

ax_sig  = fig.add_subplot(gs[0])
ax_phi1 = fig.add_subplot(gs[1])
ax_phi2 = fig.add_subplot(gs[2])

# ── Observed signal ───────────────────────────────────────────────────────────
ax_sig.plot(t, y, color='steelblue', lw=0.8, label='Observed signal')
ax_sig.axvline(shift, color='red', ls='--', lw=1.2, label='Parameter shift')
ax_sig.set_ylabel("y(t)")
ax_sig.set_title("Observed AR(2) Signal")
ax_sig.legend(fontsize=8, loc='upper right')
ax_sig.grid(True, alpha=0.3)

# ── phi1 ──────────────────────────────────────────────────────────────────────
(line_phi1_true,) = ax_phi1.plot(t, phi1_true, 'k--', lw=1.5, label='True phi1')
(line_phi1_hat,)  = ax_phi1.plot(t, phi1_hat,  color='darkorange', lw=1.2,
                                  label='Estimated phi1')
ax_phi1.axvline(shift, color='red', ls='--', lw=1.2)
ax_phi1.set_ylabel("phi1")
ax_phi1.set_title("phi1 - True vs Kalman Estimate")
ax_phi1.legend(fontsize=8, loc='upper right')
ax_phi1.grid(True, alpha=0.3)

# ── phi2 ──────────────────────────────────────────────────────────────────────
(line_phi2_true,) = ax_phi2.plot(t, phi2_true, 'k--', lw=1.5, label='True phi2')
(line_phi2_hat,)  = ax_phi2.plot(t, phi2_hat,  color='mediumseagreen', lw=1.2,
                                  label='Estimated phi2')
ax_phi2.axvline(shift, color='red', ls='--', lw=1.2)
ax_phi2.set_ylabel("phi2")
ax_phi2.set_xlabel("Time step")
ax_phi2.set_title("phi2 - True vs Kalman Estimate")
ax_phi2.legend(fontsize=8, loc='upper right')
ax_phi2.grid(True, alpha=0.3)

plt.tight_layout()

# ── Sliders ───────────────────────────────────────────────────────────────────
fig.subplots_adjust(bottom=0.18)   # make room below plots for sliders

ax_Q = fig.add_axes([0.15, 0.09, 0.70, 0.025])
ax_R = fig.add_axes([0.15, 0.04, 0.70, 0.025])

slider_Q = Slider(ax_Q, 'Process noise Q', 1e-4, 0.5,
                  valinit=Q_init, valstep=1e-4, color='darkorange')
slider_R = Slider(ax_R, 'Obs noise R',     1e-4, 2.0,
                  valinit=R_init, valstep=1e-4, color='mediumseagreen')

# ── Update callback ───────────────────────────────────────────────────────────
def update(_):
    Q_val = slider_Q.val
    R_val = slider_R.val
    p1, p2 = run_kalman(y, Q_val, R_val)
    line_phi1_hat.set_ydata(p1)
    line_phi2_hat.set_ydata(p2)
    # Rescale axes
    for ax, data_hat, data_true in [
        (ax_phi1, p1, phi1_true),
        (ax_phi2, p2, phi2_true),
    ]:
        combined = np.concatenate([data_hat[2:], data_true])
        margin = 0.15 * (combined.max() - combined.min() + 1e-6)
        ax.set_ylim(combined.min() - margin, combined.max() + margin)
    fig.canvas.draw_idle()

slider_Q.on_changed(update)
slider_R.on_changed(update)

plt.show()