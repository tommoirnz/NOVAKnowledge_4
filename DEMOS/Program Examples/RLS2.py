import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import lfilter

# Parameters for AR(2) process
n = 1000  # Number of time steps
phi1 = 0.8  # AR coefficient 1
phi2 = -0.3  # AR coefficient 2
sigma = 1.0  # Noise standard deviation

# Generate white noise
np.random.seed(42)
epsilon = np.random.normal(0, sigma, n)

# Generate AR(2) process: y_t = phi1*y_{t-1} + phi2*y_{t-2} + epsilon_t
y = np.zeros(n)
for t in range(2, n):
    y[t] = phi1 * y[t-1] + phi2 * y[t-2] + epsilon[t]

# Recursive least squares estimation (online)
N = 100  # Window size for estimation
theta_hat = np.zeros((n, 2))  # Store estimated coefficients
P = np.eye(2) * 1000  # Initial covariance matrix

for t in range(2, n):
    # Prepare observation vector
    x = np.array([y[t-1], y[t-2]]).reshape(-1, 1)

    # Kalman gain
    K = P @ x / (1 + x.T @ P @ x)

    # Update estimate
    theta_hat[t] = theta_hat[t-1] + K @ (y[t] - x.T @ theta_hat[t-1])

    # Update covariance
    P = (np.eye(2) - K @ x.T) @ P

# Plot the true and estimated AR coefficients
plt.figure(figsize=(12, 6))

# True coefficients
plt.axhline(phi1, color='r', linestyle='--', label=f'True φ₁ = {phi1:.2f}')
plt.axhline(phi2, color='b', linestyle='--', label=f'True φ₂ = {phi2:.2f}')

# Estimated coefficients
plt.plot(theta_hat[:, 0], label='Estimated φ₁')
plt.plot(theta_hat[:, 1], label='Estimated φ₂')

plt.title('Recursive Least Squares Estimation of AR(2) Coefficients')
plt.xlabel('Time Step')
plt.ylabel('Coefficient Value')
plt.legend()
plt.grid(True)
plt.show()

# Plot the AR(2) process
plt.figure(figsize=(12, 4))
plt.plot(y, label='AR(2) Process')
plt.title('AR(2) Process Generated from White Noise')
plt.xlabel('Time Step')
plt.ylabel('Value')
plt.legend()
plt.grid(True)
plt.show()