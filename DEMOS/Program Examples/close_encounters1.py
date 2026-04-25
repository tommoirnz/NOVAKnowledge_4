import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# Create a cosmic-inspired colormap (warm/space-like)
cosmic_cmap = LinearSegmentedColormap.from_list(
    'cosmic', ['#1a1a2e', '#b21f1f', '#ffec27', '#ff9f1c', '#ff0000']
)

# Generate a "cosmic signal" (sine wave with noise)
x = np.linspace(0, 10, 1000)
y = np.sin(x) + 0.1 * np.random.randn(1000)  # Sine wave + noise

# Create figure with cosmic theme
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(x, y, color='#ffec27', linewidth=2, label='Alien Signal')

# Customize for Close Encounters theme
ax.set_title('Close Encounters: Cosmic Signal Detection', fontsize=16, pad=20)
ax.set_xlabel('Time (arbitrary units)', fontsize=12)
ax.set_ylabel('Signal Intensity', fontsize=12)
ax.grid(True, alpha=0.3)

# Add a cosmic background gradient
fig.patch.set_facecolor('#0a0a1a')  # Dark space-like background
ax.set_facecolor('#0a0a1a')

# Add a subtle "cosmic dust" effect (random dots)
ax.scatter(np.random.uniform(0, 10, 200),
           np.random.uniform(-2, 2, 200),
           s=5, c='white', alpha=0.5)

# Add a "floating" text label (like the film's title)
ax.text(5, 1.5, 'CONTACT ESTABLISHED',
        fontsize=14, color='#ffec27', ha='center', bbox=dict(facecolor='black', alpha=0.5))

# Add a "signal strength" bar (like the film's meter)
ax.axhline(y=0, color='#ffec27', linestyle='--', alpha=0.5)
ax.axhline(y=1, color='#ffec27', linestyle='--', alpha=0.5)

# Adjust layout and show
plt.tight_layout()
plt.show()