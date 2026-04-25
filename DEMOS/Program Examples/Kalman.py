import numpy as np
import matplotlib.pyplot as plt

def kalman_filter(true_state, Q, R):
    # Initialize variables with proper types
    x_hat = np.array(true_state, dtype=np.float64)
    P = np.eye(2) * 10.0  # Initial covariance matrix
    states = []
    measurements = []
    estimates = []

    current_state = np.array(true_state, dtype=np.float64)

    for t in range(100):  # 100 time steps
        # Store current state for visualization
        states.append(current_state.copy())

        # Measurement (noisy position measurement)
        z = current_state[0] + np.random.normal(0, np.sqrt(R))
        measurements.append(z)

        # Time update (prediction)
        F = np.array([[1, 0.1], [0, 1]], dtype=np.float64)
        x_hat = F @ x_hat
        P = F @ P @ F.T + Q

        # Measurement update
        H = np.array([1, 0], dtype=np.float64)

        # Kalman gain calculation
        y = z - H @ x_hat
        S = H @ P @ H.T + R
        K = (P @ H.T) / S

        # Update state estimate
        x_hat = x_hat + K * y
        P = (np.eye(2, dtype=np.float64) - K @ H) @ P

        # Update true state for next step
        current_state += 0.1 * np.array([current_state[1], -0.1*current_state[1]], dtype=np.float64)

        estimates.append(x_hat.copy())

    return np.array(states, dtype=np.float64), np.array(measurements, dtype=np.float64), np.array(estimates, dtype=np.float64)

# Parameters
true_state = np.array([0, 1], dtype=np.float64)  # [position, velocity] at t=0
Q = np.array([[0.05**2, 0], [0, 0.1**2]], dtype=np.float64)  # Process noise covariance
R = 0.5**2  # Measurement noise variance

# Run simulation
true_states, measurements, estimates = kalman_filter(true_state, Q, R)

# Plot results
plt.figure(figsize=(12, 8))

plt.subplot(3, 1, 1)
plt.plot(true_states[:, 0], label='True Position')
plt.plot(estimates[:, 0], '--', label='Kalman Estimate')
plt.plot(measurements, 'o', label='Measurements')
plt.ylabel('Position')
plt.legend()

plt.subplot(3, 1, 2)
plt.plot(true_states[:, 1], label='True Velocity')
plt.plot(estimates[:, 1], '--', label='Kalman Estimate')
plt.ylabel('Velocity')
plt.legend()

plt.subplot(3, 1, 3)
plt.plot(true_states[:, 0] - estimates[:, 0], label='Position Error')
plt.plot(true_states[:, 1] - estimates[:, 1], label='Velocity Error')
plt.ylabel('Error')
plt.legend()

plt.tight_layout()
plt.show()