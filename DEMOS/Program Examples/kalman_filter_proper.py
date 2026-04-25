import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import solve_continuous_are

# Define system matrices
A = np.array([[0, 1], [0, 0]])  # State matrix (2x2)
B = np.array([[0], [1]])  # Input matrix (2x1)
C = np.array([[1, 0]])  # Output matrix (1x2)

# System parameters
Q = np.eye(2)  # State cost matrix (for LQR)
R_lqr = 1.0  # Input cost for LQR (scalar)

# Kalman filter parameters
Q_kf = np.eye(2) * 0.01  # Process noise covariance
R_kf = 0.1  # Measurement noise covariance (scalar)

dt = 0.1  # Time step
T = 10.0  # Simulation time
t = np.arange(0, T, dt)

# Generate random input
np.random.seed(42)
u = np.random.randn(len(t)) * 0.5  # Random input (1D array of scalars)

print("=" * 60)
print("DEBUGGING INFORMATION")
print("=" * 60)
print(f"A shape: {A.shape}")
print(f"B shape: {B.shape}")
print(f"C shape: {C.shape}")
print(f"Q shape: {Q.shape}")
print(f"Q_kf shape: {Q_kf.shape}")
print(f"u shape: {u.shape}")
print(f"t shape: {t.shape}")
print(f"dt: {dt}")

# First compute LQR gains for state feedback
P = solve_continuous_are(A, B, Q, R_lqr)
print(f"\nP shape (from ARE): {P.shape}")
print(f"P:\n{P}")

# For scalar R, use division instead of inverse
K = (1.0 / R_lqr) * (B.T @ P)
print(f"K shape: {K.shape}")
print(f"K: {K}")

# Compute Kalman filter gain (the correct way)
# Solve the continuous-time algebraic Riccati equation for estimation
P_kf = solve_continuous_are(A.T, C.T, Q_kf, R_kf)
print(f"\nP_kf shape (from ARE): {P_kf.shape}")
print(f"P_kf:\n{P_kf}")

# For scalar R_kf, use division instead of inverse
L = (P_kf @ C.T) * (1.0 / R_kf)  # Kalman gain (2x1)
print(f"L shape: {L.shape}")
print(f"L:\n{L}")

# Initial conditions
x = np.zeros((len(t), 2))  # True state
x_hat = np.zeros((len(t), 2))  # Estimated state
P_hat = np.zeros((len(t), 2, 2))  # Estimation error covariance

# Initial states
x[0] = np.array([0.5, 0.2])  # Non-zero initial true state
x_hat[0] = np.array([0, 0])  # Initial estimate
P_hat[0] = np.eye(2) * 0.1  # Initial covariance

print(f"\nx[0] shape: {x[0].shape}, value: {x[0]}")
print(f"x_hat[0] shape: {x_hat[0].shape}, value: {x_hat[0]}")
print(f"P_hat[0] shape: {P_hat[0].shape}")

print("\n" + "=" * 60)
print("STARTING SIMULATION")
print("=" * 60)

# Simulation
for i in range(1, len(t)):
    print(f"\n--- Time step {i}, t = {t[i]:.1f} ---")

    # True system dynamics with process noise
    # Create process noise as 1D array of length 2
    process_noise = np.random.randn(2) * 0.01
    print(f"process_noise shape: {process_noise.shape}, value: {process_noise}")

    # Get scalar input value
    u_scalar = u[i - 1]
    print(f"u_scalar: {u_scalar}")

    # Calculate x_dot = A*x + B*u
    print(f"x[i-1] shape: {x[i - 1].shape}, value: {x[i - 1]}")

    # Debug A @ x[i-1] - ensure it's 2D (2x1)
    Ax = A @ x[i - 1].reshape(-1, 1)  # Make it 2x1
    print(f"A @ x[i-1] shape: {Ax.shape}, value:\n{Ax}")

    # Debug B * u_scalar
    Bu = B * u_scalar  # This is 2x1
    print(f"B * u_scalar shape: {Bu.shape}, value:\n{Bu}")

    # Now add 2x1 matrices
    x_dot = Ax + Bu
    print(f"x_dot shape: {x_dot.shape}, value:\n{x_dot}")

    # Flatten to 1D for addition with x[i-1]
    x_dot_flat = x_dot.flatten()
    print(f"x_dot (flattened) shape: {x_dot_flat.shape}, value: {x_dot_flat}")

    # Debug each term
    print(f"x[i-1] shape: {x[i - 1].shape}")
    print(f"x_dot_flat * dt shape: {(x_dot_flat * dt).shape}")
    print(f"process_noise shape: {process_noise.shape}")

    # Now all terms should be (2,) shape
    x[i] = x[i - 1] + x_dot_flat * dt + process_noise
    print(f"x[{i}] = {x[i]}")

    # Only do first few steps for debugging
    if i >= 2:
        print("... continuing with full simulation")
        break

print("\n" + "=" * 60)
print("CONTINUING FULL SIMULATION")
print("=" * 60)

# Now continue the full simulation properly
for i in range(2, len(t)):
    # True system dynamics with process noise
    process_noise = np.random.randn(2) * 0.01
    u_scalar = u[i - 1]

    # Calculate x_dot = A*x + B*u
    Ax = A @ x[i - 1].reshape(-1, 1)
    Bu = B * u_scalar
    x_dot = (Ax + Bu).flatten()

    # Discrete-time update
    x[i] = x[i - 1] + x_dot * dt + process_noise

    # Measurement with noise
    measurement_noise = np.random.randn() * np.sqrt(R_kf)
    z = float(C @ x[i]) + measurement_noise

    # Kalman filter prediction step
    # State prediction
    Ax_hat = A @ x_hat[i - 1].reshape(-1, 1)
    x_hat_dot = (Ax_hat + B * u_scalar).flatten()
    x_pred = x_hat[i - 1] + x_hat_dot * dt

    # Covariance prediction
    P_pred = P_hat[i - 1] + (A @ P_hat[i - 1] + P_hat[i - 1] @ A.T + Q_kf) * dt

    # Kalman filter update step
    y_residual = z - float(C @ x_pred)
    S_scalar = float(C @ P_pred @ C.T) + R_kf
    K_kf = (P_pred @ C.T) * (1.0 / S_scalar)
    K_kf_1d = K_kf.flatten()
    x_hat[i] = x_pred + K_kf_1d * y_residual

    # Covariance update
    I = np.eye(2)
    KC = K_kf @ C
    P_hat[i] = (I - KC) @ P_pred @ (I - KC).T + (K_kf * R_kf) @ K_kf.T

# Plotting
plt.figure(figsize=(12, 8))

# True states vs Estimated states
plt.subplot(2, 1, 1)
plt.plot(t, x[:, 0], 'b-', label='True x1 (position)', linewidth=2)
plt.plot(t, x[:, 1], 'r-', label='True x2 (velocity)', linewidth=2)
plt.plot(t, x_hat[:, 0], 'g--', label='Estimated x1', linewidth=1.5)
plt.plot(t, x_hat[:, 1], 'm--', label='Estimated x2', linewidth=1.5)
plt.title('True vs Estimated System States (Double Integrator)')
plt.ylabel('State values')
plt.legend()
plt.grid(True)

# Estimation errors
plt.subplot(2, 1, 2)
plt.plot(t, x[:, 0] - x_hat[:, 0], 'b-', label='x1 error (position)', linewidth=1.5)
plt.plot(t, x[:, 1] - x_hat[:, 1], 'r-', label='x2 error (velocity)', linewidth=1.5)
plt.title('Estimation Errors')
plt.xlabel('Time (s)')
plt.ylabel('Error')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()

# Print verification
print("=" * 60)
print("SIMULATION RESULTS")
print("=" * 60)
print(f"Final true state: {x[-1]}")
print(f"Final estimated state: {x_hat[-1]}")
print(f"Final estimation errors:")
print(f"Position error (x1): {x[-1, 0] - x_hat[-1, 0]:.6f}")
print(f"Velocity error (x2): {x[-1, 1] - x_hat[-1, 1]:.6f}")

# Calculate RMS errors
rms_error_x1 = np.sqrt(np.mean((x[:, 0] - x_hat[:, 0]) ** 2))
rms_error_x2 = np.sqrt(np.mean((x[:, 1] - x_hat[:, 1]) ** 2))
print(f"\nRMS Estimation Errors:")
print(f"Position (x1) RMS error: {rms_error_x1:.6f}")
print(f"Velocity (x2) RMS error: {rms_error_x2:.6f}")

print(f"\nKalman gain L:\n{L}")
print(f"LQR gain K: {K.flatten()}")