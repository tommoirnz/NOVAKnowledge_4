import numpy as np
import matplotlib.pyplot as plt

# Parameters
T = 2 * np.pi          # Period of square wave (2π for normalized)
L = T / 2              # Half-period (π for normalized)
N_terms = 10           # Number of Fourier terms to plot
x = np.linspace(-np.pi, np.pi, 1000)  # x values from -π to π
y_exact = np.sign(np.sin(x))         # Exact square wave

# Fourier series components
def square_wave_fourier(x, n_terms):
    y = np.zeros_like(x)
    for n in range(1, n_terms + 1):
        if n % 2 == 1:  # Only odd harmonics
            y += (4/(n*np.pi)) * np.sin(n*x)
    return y

# Create plot
plt.figure(figsize=(10, 6))

# Plot exact square wave
plt.plot(x, y_exact, 'k-', linewidth=2, label='Exact Square Wave')

# Plot Fourier approximations
for n in [1, 3, 5, 7, 10]:
    y_fourier = square_wave_fourier(x, n)
    plt.plot(x, y_fourier, '--', linewidth=1.5,
             label=f'N={n} terms' if n == N_terms else None)

# Plot final approximation
y_fourier = square_wave_fourier(x, N_terms)
plt.plot(x, y_fourier, 'r-', linewidth=2, label=f'N={N_terms} terms')

# Customize plot
plt.title('Fourier Series Approximation of Square Wave', fontsize=14)
plt.xlabel('x', fontsize=12)
plt.ylabel('Amplitude', fontsize=12)
plt.grid(True, alpha=0.3)
plt.legend(loc='upper right', fontsize=10)

# Highlight important points
plt.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.show()

# Print coefficients for reference
print(f"\nFourier Series Coefficients (a_n = 0, b_n = 4/({n}*π) for odd n):")
for n in range(1, N_terms+1, 2):
    print(f"b_{n} = {4/(n*np.pi):.4f}")