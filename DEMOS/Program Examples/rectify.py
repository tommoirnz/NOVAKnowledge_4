import numpy as np
import matplotlib.pyplot as plt

# Define the range and number of points
x_min = 0
x_max = 2 * np.pi  # One full period of sin(x)
num_points = 10000

# Generate x values
x = np.linspace(x_min, x_max, num_points)

# Compute |sin(x)|
abs_sin_x = np.abs(np.sin(x))

# Calculate the average value
average_value = np.mean(abs_sin_x)

print(f"The average value of |sin(x)| over [{x_min}, {x_max}] is: {average_value:.4f}")

# Plot the function and highlight the average value
plt.figure(figsize=(10, 4))
plt.plot(x, abs_sin_x, label=r'$|\sin(x)|$', color='blue')
plt.axhline(y=average_value, color='red', linestyle='--', label=f'Average = {average_value:.3f}')
plt.title('Average of $|\sin(x)|$ over one period')
plt.xlabel('x')
plt.ylabel('$|\sin(x)|$')
plt.legend()
plt.grid(True)
plt.show()