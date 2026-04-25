import numpy as np
import matplotlib.pyplot as plt

# Define x values
x = np.linspace(-4 * np.pi, 4 * np.pi, 1000)

# Fourier series components (10 terms: n=1,3,5,7,9)
fourier_series = (4 / np.pi) * sum( (1 / (2*k - 1)) * np.sin((2*k - 1) * x) for k in range(1, 11) )

# Plot the original square wave
square_wave = np.where(x % (2*np.pi) < np.pi, 1, -1)
square_wave = np.where(x % (2*np.pi) >= np.pi, -1, np.where(x % (2*np.pi) < np.pi, 1, 0))

# Plot
plt.figure(figsize=(10, 5))
plt.plot(x, square_wave, label='Original Square Wave', color='blue', linewidth=2)
plt.plot(x, fourier_series, label='10-Term Fourier Series', color='red', linestyle='--')
plt.title('Fourier Series Approximation of a Square Wave (10 Terms)')
plt.xlabel('x')
plt.ylabel('f(x)')
plt.legend()
plt.grid(True)
plt.show()