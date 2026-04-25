import numpy as np
import matplotlib.pyplot as plt

# Parameters for AR(2) process
true_c1 = 0.8
true_c2 = -0.3
sigma = 1.0  # Noise standard deviation

# Generate AR(2) data
def generate_ar2_data(n_samples, c1, c2, sigma):
    x = np.zeros(n_samples)
    x[0] = np.random.normal(0, sigma)
    x[1] = np.random.normal(0, sigma)

    for t in range(2, n_samples):
        x[t] = c1 * x[t-1] + c2 * x[t-2] + np.random.normal(0, sigma)
    return x

# Recursive Least Squares (RLS) for AR(2)
def recursive_least_squares(x, c1_true, c2_true, lambda_=0.99):
    n = len(x)
    P = np.eye(2) * 1e6  # Initial covariance matrix
    theta = np.zeros(2)  # Initial parameter estimate
    estimates = []

    for t in range(2, n):
        phi = np.array([x[t-1], x[t-2]]).reshape(-1, 1)
        K = P @ phi / (1 + phi.T @ P @ phi)
        theta = theta + K @ (x[t] - phi.T @ theta)
        P = (1 / lambda_) * (P - K @ phi.T @ P)
        estimates.append(theta.copy())

    return np.array(estimates)

# Generate data
n_samples = 1000
x = generate_ar2_data(n_samples, true_c1, true_c2, sigma)

# Estimate parameters
estimates = recursive_least_squares(x, true_c1, true_c2)

# Plot results
plt.figure(figsize=(10, 6))
plt.plot(estimates[:, 0], label='Estimated c1', alpha=0.7)
plt.axhline(true_c1, color='r', linestyle='--', label='True c1')
plt.xlabel('Time')
plt.ylabel('Coefficient')
plt.title('Recursive Least Squares Estimation for AR(2) Coefficient c1')
plt.legend()
plt.grid(True)
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(estimates[:, 1], label='Estimated c2', alpha=0.7)
plt.axhline(true_c2, color='r', linestyle='--', label='True c2')
plt.xlabel('Time')
plt.ylabel('Coefficient')
plt.title('Recursive Least Squares Estimation for AR(2) Coefficient c2')
plt.legend()
plt.grid(True)
plt.show()