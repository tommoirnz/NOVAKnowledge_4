import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# --- 3rd Order Kalman Filter Implementation ---
class ThirdOrderKalmanFilter:
    def __init__(self, initial_state, initial_covariance, process_noise=0.1, measurement_noise=1.0):
        """
        Initialize 3rd-order Kalman filter
        State vector: [x, x_dot, x_ddot] (position, velocity, acceleration)
        """
        self.state = initial_state.copy()  # [x, v, a]
        self.covariance = initial_covariance.copy()
        self.process_noise = process_noise * np.eye(3)  # Process noise covariance
        self.measurement_noise = measurement_noise

        # System matrices
        self.F = np.array([[1, 1, 0.5],  # State transition
                          [0, 1, 1],
                          [0, 0, 1]])
        self.H = np.array([[1, 0, 0]])  # Measurement function (only position)

    def predict(self):
        """Predict next state and covariance"""
        self.state = np.dot(self.F, self.state)
        self.covariance = np.dot(self.F, np.dot(self.covariance, self.F.T)) + self.process_noise

    def update(self, measurement):
        """Update state with measurement"""
        # Innovation (residual)
        innovation = measurement - np.dot(self.H, self.state)
        S = self.H @ self.covariance @ self.H.T + self.measurement_noise
        K = self.covariance @ self.H.T @ np.linalg.inv(S)  # Kalman gain

        # Update state and covariance
        self.state += K @ innovation
        self.covariance = (np.eye(3) - K @ self.H) @ self.covariance

# --- Simulation Setup ---
np.random.seed(42)  # For reproducibility

# True system parameters (simulated)
true_x = lambda t: 0.5*t**3 + 2*t**2 + 1  # True trajectory
true_x_dot = lambda t: 1.5*t**2 + 4*t
true_x_ddot = lambda t: 3*t + 4

# Measurement function with noise
def noisy_measurement(t):
    true_val = true_x(t)
    return true_val + np.random.normal(0, 1.5)  # Measurement noise

# Simulation parameters
t = np.linspace(0, 5, 100)
measurements = [noisy_measurement(ti) for ti in t]

# Initialize Kalman filter
initial_state = np.array([0, 0, 0])  # [x0, v0, a0]
initial_cov = np.diag([100, 10, 1])   # Large initial uncertainty
kf = ThirdOrderKalmanFilter(initial_state, initial_cov)

# Run filter and collect results
estimated_states = []
true_states = []
for ti in t:
    # Predict step
    kf.predict()

    # Update with measurement
    kf.update(noisy_measurement(ti))

    # Store results
    estimated_states.append(kf.state.copy())
    true_states.append(np.array([true_x(ti), true_x_dot(ti), true_x_ddot(ti)]))

estimated_states = np.array(estimated_states)
true_states = np.array(true_states)

# --- Plotting ---
fig = plt.figure(figsize=(12, 8))

# 3D State Estimation Plot
ax1 = fig.add_subplot(2, 2, 1, projection='3d')
ax1.plot(true_states[:, 0], true_states[:, 1], true_states[:, 2],
         'b-', label='True State')
ax1.plot(estimated_states[:, 0], estimated_states[:, 1], estimated_states[:, 2],
         'r--', label='Kalman Estimate')
ax1.set_xlabel('Position')
ax1.set_ylabel('Velocity')
ax1.set_zlabel('Acceleration')
ax1.set_title('3D State Estimation')
ax1.legend()

# Position Estimation (1D)
ax2 = fig.add_subplot(2, 2, 2)
ax2.plot(t, true_states[:, 0], 'b-', label='True Position')
ax2.plot(t, estimated_states[:, 0], 'r--', label='Estimated Position')
ax2.plot(t, measurements, 'go', alpha=0.5, label='Measurements')
ax2.set_xlabel('Time')
ax2.set_ylabel('Position')
ax2.set_title('Position Estimation')
ax2.legend()

# Velocity Estimation (1D)
ax3 = fig.add_subplot(2, 2, 3)
ax3.plot(t, true_states[:, 1], 'b-', label='True Velocity')
ax3.plot(t, estimated_states[:, 1], 'r--', label='Estimated Velocity')
ax3.set_xlabel('Time')
ax3.set_ylabel('Velocity')
ax3.set_title('Velocity Estimation')
ax3.legend()

# Acceleration Estimation (1D)
ax4 = fig.add_subplot(2, 2, 4)
ax4.plot(t, true_states[:, 2], 'b-', label='True Acceleration')
ax4.plot(t, estimated_states[:, 2], 'r--', label='Estimated Acceleration')
ax4.set_xlabel('Time')
ax4.set_ylabel('Acceleration')
ax4.set_title('Acceleration Estimation')
ax4.legend()

plt.tight_layout()
plt.show()

# Print verification
print("Kalman Filter Initialization:")
print(f"Initial state: {initial_state}")
print(f"Initial covariance:\n{initial_cov}")

print("\nSample Results (first 3 time steps):")
print(f"Time: {t[0]:.2f}s - True State: {true_states[0]}, Estimated: {estimated_states[0]}")
print(f"Time: {t[-1]:.2f}s - True State: {true_states[-1]}, Estimated: {estimated_states[-1]}")
