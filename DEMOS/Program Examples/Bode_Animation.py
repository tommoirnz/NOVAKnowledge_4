import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Slider
from scipy import signal

# Natural frequency
wn = 1.0

# Frequency range for Bode plot
w = np.logspace(-2, 2, 500)

def compute_bode(zeta):
    num = [wn**2]
    den = [1, 2*zeta*wn, wn**2]
    sys = signal.TransferFunction(num, den)
    w_out, H = signal.freqs(num, den, worN=w)
    mag = 20 * np.log10(np.abs(H))
    phase = np.degrees(np.unwrap(np.angle(H)))
    return w_out, mag, phase

def compute_step(zeta):
    num = [wn**2]
    den = [1, 2*zeta*wn, wn**2]
    sys = signal.TransferFunction(num, den)
    t = np.linspace(0, 40, 2000)
    t_out, y = signal.step(sys, T=t)
    return t_out, y

# Initial zeta
zeta_init = 0.5

# Setup figure
fig = plt.figure(figsize=(13, 9))
fig.patch.set_facecolor('#1a1a2e')

gs = gridspec.GridSpec(3, 2, figure=fig, height_ratios=[1, 1, 0.15])

ax_mag   = fig.add_subplot(gs[0, 0])
ax_phase = fig.add_subplot(gs[1, 0])
ax_step  = fig.add_subplot(gs[0:2, 1])
ax_slide = fig.add_subplot(gs[2, :])

# Style all axes
for ax in [ax_mag, ax_phase, ax_step]:
    ax.set_facecolor('#0f0f23')
    ax.tick_params(colors='#cccccc', labelsize=9)
    ax.spines['bottom'].set_color('#444466')
    ax.spines['top'].set_color('#444466')
    ax.spines['left'].set_color('#444466')
    ax.spines['right'].set_color('#444466')
    ax.yaxis.label.set_color('#cccccc')
    ax.xaxis.label.set_color('#cccccc')
    ax.title.set_color('#e0e0ff')
    ax.grid(True, color='#2a2a4a', linestyle='--', linewidth=0.6)

# --- Bode Magnitude ---
ax_mag.set_xscale('log')
ax_mag.set_title('Bode Plot - Magnitude', fontsize=11, fontweight='bold')
ax_mag.set_ylabel('Magnitude (dB)', fontsize=9)
ax_mag.set_xlim([w[0], w[-1]])

w0, mag0, phase0 = compute_bode(zeta_init)
line_mag, = ax_mag.plot(w0, mag0, color='#00d4ff', linewidth=2)
ax_mag.axvline(x=wn, color='#ff6b6b', linestyle=':', linewidth=1.2, label='wn = 1')
ax_mag.legend(fontsize=8, facecolor='#1a1a2e', edgecolor='#444466',
              labelcolor='#cccccc', loc='lower left')

# --- Bode Phase ---
ax_phase.set_xscale('log')
ax_phase.set_title('Bode Plot - Phase', fontsize=11, fontweight='bold')
ax_phase.set_ylabel('Phase (deg)', fontsize=9)
ax_phase.set_xlabel('Frequency (rad/s)', fontsize=9)
ax_phase.set_xlim([w[0], w[-1]])
ax_phase.set_yticks([-180, -135, -90, -45, 0])

line_phase, = ax_phase.plot(w0, phase0, color='#ff9f43', linewidth=2)
ax_phase.axvline(x=wn, color='#ff6b6b', linestyle=':', linewidth=1.2)

# --- Step Response ---
ax_step.set_title('Step Response', fontsize=11, fontweight='bold')
ax_step.set_xlabel('Time (s)', fontsize=9)
ax_step.set_ylabel('Amplitude', fontsize=9)

t0, y0 = compute_step(zeta_init)
line_step, = ax_step.plot(t0, y0, color='#a29bfe', linewidth=2)
ax_step.axhline(y=1.0, color='#ff6b6b', linestyle='--', linewidth=1.0, label='Steady state')
ax_step.set_xlim([0, 40])
ax_step.set_ylim([-0.2, 2.0])
ax_step.legend(fontsize=8, facecolor='#1a1a2e', edgecolor='#444466',
               labelcolor='#cccccc')

# Damping regime text
text_regime = ax_step.text(0.98, 0.92, '', transform=ax_step.transAxes,
                           fontsize=9, color='#ffeaa7',
                           ha='right', va='top',
                           bbox=dict(boxstyle='round,pad=0.3',
                                     facecolor='#2d2d5e', edgecolor='#555588'))

# Zeta annotation on step plot
text_zeta = ax_step.text(0.98, 0.80, f'zeta = {zeta_init:.2f}',
                         transform=ax_step.transAxes,
                         fontsize=10, color='#00d4ff',
                         ha='right', va='top', fontweight='bold',
                         bbox=dict(boxstyle='round,pad=0.3',
                                   facecolor='#1a1a2e', edgecolor='#00d4ff'))

def get_regime(zeta):
    if zeta < 1.0:
        return 'Underdamped'
    elif abs(zeta - 1.0) < 1e-9:
        return 'Critically Damped'
    else:
        return 'Overdamped'

def update_regime_text(zeta):
    regime = get_regime(zeta)
    color_map = {
        'Underdamped': '#fd79a8',
        'Critically Damped': '#55efc4',
        'Overdamped': '#fdcb6e'
    }
    text_regime.set_text(regime)
    text_regime.set_color(color_map[regime])

update_regime_text(zeta_init)

# --- Slider ---
ax_slide.set_facecolor('#1a1a2e')
slider = Slider(
    ax=ax_slide,
    label='Damping Ratio  zeta',
    valmin=0.1,
    valmax=2.0,
    valinit=zeta_init,
    valstep=0.01,
    color='#6c5ce7'
)
slider.label.set_color('#cccccc')
slider.valtext.set_color('#00d4ff')
slider.valtext.set_fontsize(11)

# Main title
fig.suptitle(
    'Second-Order System  H(s) = wn^2 / (s^2 + 2*zeta*wn*s + wn^2)   [wn = 1]',
    fontsize=12, fontweight='bold', color='#e0e0ff', y=0.98
)

def update(val):
    zeta = slider.val

    # Bode
    w_out, mag, phase = compute_bode(zeta)
    line_mag.set_ydata(mag)
    line_phase.set_ydata(phase)

    # Auto-scale magnitude
    ax_mag.set_ylim([min(mag) - 5, max(mag) + 5])

    # Step
    t_out, y = compute_step(zeta)
    line_step.set_xdata(t_out)
    line_step.set_ydata(y)

    # Update annotations
    text_zeta.set_text(f'zeta = {zeta:.2f}')
    update_regime_text(zeta)

    fig.canvas.draw_idle()

slider.on_changed(update)

# Initial magnitude scale
w0, mag0, phase0 = compute_bode(zeta_init)
ax_mag.set_ylim([min(mag0) - 5, max(mag0) + 5])

plt.tight_layout()
plt.show()
