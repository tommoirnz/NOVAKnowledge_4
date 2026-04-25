# Generated: 2026-04-08 18:59:37
# ============================================================

import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import toeplitz

# ── Reproducibility ──────────────────────────────────────────────────────────
np.random.seed(42)

# ── Signal parameters ────────────────────────────────────────────────────────
N        = 256          # number of samples
fs       = 1.0          # normalised sample rate
f0       = 0.05         # sinusoid frequency (cycles / sample)
t        = np.arange(N)
signal   = np.sin(2 * np.pi * f0 * t)

# ── Noise calibration (SNR ≈ 5 dB) ──────────────────────────────────────────
SNR_dB   = 5.0
SNR_lin  = 10 ** (SNR_dB / 10)
sig_pwr  = np.mean(signal ** 2)
noise_std = np.sqrt(sig_pwr / SNR_lin)
noise    = noise_std * np.random.randn(N)
obs      = signal + noise          # noisy observations

# ── Helper: build Wiener-Hopf system ─────────────────────────────────────────
def wiener_hopf(obs, signal, M, delay=0):
    """
    Solve the Wiener-Hopf equations for a causal FIR filter of length M.
    delay > 0  → smoother (non-causal in spirit; we shift the desired signal)
    delay < 0  → predictor (desired signal is ahead of observations)
    Returns filter coefficients h of length M.
    """
    # Autocorrelation of observations (biased estimate)
    r_xx = np.correlate(obs, obs, mode='full') / N
    mid  = N - 1
    r_xx_vec = r_xx[mid : mid + M]          # r_xx[0..M-1]
    R_xx = toeplitz(r_xx_vec)               # M×M Toeplitz matrix

    # Cross-correlation between desired signal and observations
    # desired = signal shifted by -delay  (positive delay → smoother)
    desired = np.roll(signal, -delay)       # shift desired signal
    r_dx = np.correlate(desired, obs, mode='full') / N
    # r_dx[mid] = r_dx(0), r_dx[mid-1] = r_dx(-1), …
    # For causal filter: we need r_dx[0], r_dx[-1], …, r_dx[-(M-1)]
    r_dx_vec = r_dx[mid : mid + M]         # r_dx[0..M-1] (causal lags)

    # Solve R_xx * h = r_dx
    h = np.linalg.solve(R_xx + 1e-10 * np.eye(M), r_dx_vec)
    return h

def apply_fir(h, obs):
    """Apply causal FIR filter h to obs (zero-pad at the start)."""
    M   = len(h)
    out = np.zeros(len(obs))
    for n in range(len(obs)):
        for k in range(M):
            if n - k >= 0:
                out[n] += h[k] * obs[n - k]
    return out

# ── (1) Wiener Filter (delay = 0, causal, current-time estimation) ───────────
M_filter = 32
h_filter = wiener_hopf(obs, signal, M_filter, delay=0)
est_filter = apply_fir(h_filter, obs)

# ── (2) Wiener Smoother (delay = +5, access to future observations) ───────────
# For a smoother we use a non-causal approach:
# apply a causal filter to the full sequence and then shift the output back.
M_smooth  = 32
smooth_delay = 5
h_smooth  = wiener_hopf(obs, signal, M_smooth, delay=smooth_delay)
est_smooth_raw = apply_fir(h_smooth, obs)
# Shift output forward by smooth_delay to align with true signal
est_smooth = np.roll(est_smooth_raw, smooth_delay)
est_smooth[:smooth_delay] = np.nan   # undefined at the start

# ── (3) Wiener Predictor (predict 3 steps ahead) ─────────────────────────────
M_pred   = 32
pred_steps = 3
# delay = -pred_steps → desired signal is pred_steps ahead of observations
h_pred   = wiener_hopf(obs, signal, M_pred, delay=-pred_steps)
est_pred_raw = apply_fir(h_pred, obs)
# The output at time n is an estimate of signal[n + pred_steps]
# Shift back so the estimate aligns with the future time index
est_pred = np.roll(est_pred_raw, -pred_steps)
est_pred[-pred_steps:] = np.nan      # undefined at the end

# ── Plotting ─────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(3, 1, figsize=(13, 11))
plt.suptitle("Discrete-Time Wiener Estimator Examples  (SNR = 5 dB)", y=0.98,
             fontsize=14, fontweight='bold')

plot_range = slice(0, 200)   # show first 200 samples for clarity

# — Subplot 1: Wiener Filter —
ax = axes[0]
ax.plot(t[plot_range], signal[plot_range], 'k-',  lw=1.5, label='True signal')
ax.plot(t[plot_range], obs[plot_range],    'b.',  ms=2.5, alpha=0.5, label='Noisy observations')
ax.plot(t[plot_range], est_filter[plot_range], 'r-', lw=1.5, label='Wiener filter estimate')
ax.set_title(f'Wiener Filter  (causal FIR, M={M_filter}, delay=0)', fontsize=11)
ax.set_xlabel('Sample index n')
ax.set_ylabel('Amplitude')
ax.legend(loc='upper right', fontsize=8)
ax.grid(True, alpha=0.3)

# — Subplot 2: Wiener Smoother —
ax = axes[1]
ax.plot(t[plot_range], signal[plot_range], 'k-',  lw=1.5, label='True signal')
ax.plot(t[plot_range], obs[plot_range],    'b.',  ms=2.5, alpha=0.5, label='Noisy observations')
ax.plot(t[plot_range], est_smooth[plot_range], 'g-', lw=1.5,
        label=f'Wiener smoother estimate (delay={smooth_delay})')
ax.set_title(f'Wiener Smoother  (non-causal FIR, M={M_smooth}, delay={smooth_delay} steps back)',
             fontsize=11)
ax.set_xlabel('Sample index n')
ax.set_ylabel('Amplitude')
ax.legend(loc='upper right', fontsize=8)
ax.grid(True, alpha=0.3)

# — Subplot 3: Wiener Predictor —
ax = axes[2]
ax.plot(t[plot_range], signal[plot_range], 'k-',  lw=1.5, label='True signal')
ax.plot(t[plot_range], obs[plot_range],    'b.',  ms=2.5, alpha=0.5, label='Noisy observations')
ax.plot(t[plot_range], est_pred[plot_range], 'm-', lw=1.5,
        label=f'Wiener predictor estimate ({pred_steps} steps ahead)')
ax.set_title(f'Wiener Predictor  (causal FIR, M={M_pred}, {pred_steps} steps ahead)',
             fontsize=11)
ax.set_xlabel('Sample index n')
ax.set_ylabel('Amplitude')
ax.legend(loc='upper right', fontsize=8)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# ── Performance summary ───────────────────────────────────────────────────────
def mse(a, b, mask=None):
    if mask is not None:
        a, b = a[mask], b[mask]
    return np.mean((a - b) ** 2)

valid_smooth = ~np.isnan(est_smooth)
valid_pred   = ~np.isnan(est_pred)

print("=" * 52)
print("  Wiener Estimator Performance Summary")
print("=" * 52)
print(f"  Noise variance          : {noise_std**2:.4f}")
print(f"  Signal power            : {sig_pwr:.4f}")
print(f"  SNR                     : {SNR_dB:.1f} dB")
print("-" * 52)
print(f"  MSE — Noisy obs         : {mse(signal, obs):.4f}")
print(f"  MSE — Wiener Filter     : {mse(signal, est_filter):.4f}")
print(f"  MSE — Wiener Smoother   : {mse(signal[valid_smooth], est_smooth[valid_smooth]):.4f}")
print(f"  MSE — Wiener Predictor  : {mse(signal[valid_pred],  est_pred[valid_pred]):.4f}")
print("=" * 52)