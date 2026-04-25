import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# System parameters
dt = 0.1  # Time step
Tf = 10   # Total time
N = int(Tf/dt)  # Number of time steps

# True system parameters (hidden process)
A_true = np.array([[1, dt], [0, 1]])  # State transition matrix
C_true = np.array([[1, 0]])            # Observation matrix
Q_true = np.array([[0.1**2, 0],
                   [0, 0.1**2]])       # Process noise covariance
R = 0.5**2                          # Measurement noise covariance

# Initial state and measurement
x0_true = np.array([3, 0.5])          # True initial state
x0_est = np.array([0, 0])             # Initial estimate
P0 = np.eye(2) * 10                  # Initial covariance

# Generate true trajectory and noisy measurements
x_true = np.zeros((N, 2))
x_meas = np.zeros((N, 1))
for k in range(1, N):
    x_true[k] = A_true @ x_true[k-1] + np.random.multivariate_normal(np.zeros(2), Q_true)
    x_meas[k] = C_true @ x_true[k] + np.random.normal(0, np.sqrt(R))

# Kalman filter implementation
x_est = np.zeros((N, 2))
P_est = np.zeros((N, 2, 2))
for k in range(N):
    if k == 0:
        x_est[k] = x0_est
        P_est[k] = P0
    else:
        # Time update
        x_pred = A_true @ x_est[k-1]
        P_pred = A_true @ P_est[k-1] @ A_true.T + Q_true

        # Measurement update
        y = x_meas[k] - C_true @ x_pred
        K = P_pred @ C_true.T / (C_true @ P_pred @ C_true.T + R)
        x_est[k] = x_pred + K @ y
        P_est[k] = (np.eye(2) - K @ C_true) @ P_pred

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))
ax.set_xlim(0, Tf)
ax.set_ylim(min(x_meas.min(), x_true[:,0].min()-1), max(x_meas.max(), x_true[:,0].max()+1))
ax.set_xlabel('Time')
ax.set_ylabel('State')
ax.grid(True)

# Store plot data
lines = []
lines.append(ax.plot([], [], 'b-', label='True State')[0])
lines.append(ax.plot([], [], 'r-', label='Estimated State')[0])
lines.append(ax.plot([], [], 'go', label='Measurement')[0])

def update(frame):
    ax.clear()
    ax.set_xlim(0, Tf)
    ax.set_ylim(min(x_meas.min(), x_true[:,0].min()-1), max(x_meas.max(), x_true[:,0].max()+1))
    ax.set_xlabel('Time')
    ax.set_ylabel('State')
    ax.grid(True)

    ax.plot([], [], 'b-', label='True State')
    ax.plot([], [], 'r-', label='Estimated State')
    ax.plot([], [], 'go', label='Measurement')

    ax.plot(x_meas[:frame], x_meas[:frame], 'go', markersize=5)
    ax.plot(np.arange(frame)*dt, x_true[:frame,0], 'b-')
    ax.plot(np.arange(frame)*dt, x_est[:frame,0], 'r-')

    ax.legend(loc='best')

ani = FuncAnimation(fig, update, frames=N, repeat=False)
plt.title('Two-state Kalman Filter Demonstration')
plt.tight_layout()
plt.show()