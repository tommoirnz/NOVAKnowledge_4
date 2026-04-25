import numpy as np
import matplotlib.pyplot as plt
from control import tf, root_locus, root_locus_plot

# Define numerator and denominator coefficients
num = [1, 2, 1]
den = [1, 5, 4, 2]

# Create transfer function
system = tf(num, den)

# Plot the root locus
fig, ax = plt.subplots(figsize=(8, 6))

# Generate and plot root locus
root_locus_plot(system, ax=ax)

# Add grid and labels
ax.grid(True, linestyle='--', alpha=0.6)
ax.set_xlabel('Real')
ax.set_ylabel('Imaginary')
ax.set_title('Root Locus Plot')
ax.axhline(0, color='black', linewidth=0.5)
ax.axvline(0, color='black', linewidth=0.5)

plt.show()