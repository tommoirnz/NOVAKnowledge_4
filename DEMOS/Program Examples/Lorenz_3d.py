import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button

# Lorenz attractor solver
def lorenz_solver(sigma=10.0, rho=28.0, beta=8/3, dt=0.01, max_steps=10000):
    """
    Solve Lorenz equations using Euler integration.
    Returns trajectory points (x, y, z) as a numpy array.
    """
    # Initial conditions
    x, y, z = 0.1, 0.0, 0.0
    trajectory = np.zeros((max_steps, 3))

    for i in range(max_steps):
        # Lorenz equations
        dx = sigma * (y - x)
        dy = x * (rho - z) - y
        dz = x * y - beta * z

        # Euler integration
        x += dx * dt
        y += dy * dt
        z += dz * dt

        trajectory[i] = [x, y, z]

    return trajectory

# Initialize trajectory
trajectory = lorenz_solver()
print(f"Generated {len(trajectory)} trajectory points.")

# Set up 3D plot
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
ax.set_xlabel('X Axis')
ax.set_ylabel('Y Axis')
ax.set_zlabel('Z Axis')
ax.set_title('Lorenz Attractor (Chaotic Butterfly)')

# Initial plot (first 100 points)
line, = ax.plot(trajectory[:100, 0], trajectory[:100, 1], trajectory[:100, 2],
                'b-', linewidth=2, alpha=0.7)

# Animation update function
def update(frame):
    # Update line with new points (trail effect)
    line.set_data(trajectory[:frame, 0], trajectory[:frame, 1])
    line.set_3d_properties(trajectory[:frame, 2])
    return line,

# Create animation
ani = FuncAnimation(fig, update, frames=len(trajectory), interval=10, blit=False)

# Add interactive controls
plt.subplots_adjust(bottom=0.2)
axcolor = 'lightgoldenrodyellow'

# Slider for sigma
slider_sigma = plt.axes([0.2, 0.1, 0.65, 0.03])
sigma_slider = Slider(slider_sigma, 'Sigma', 1, 30, valinit=10)

# Slider for rho
slider_rho = plt.axes([0.2, 0.15, 0.65, 0.03])
rho_slider = Slider(slider_rho, 'Rho', 10, 100, valinit=28)

# Slider for beta
slider_beta = plt.axes([0.2, 0.2, 0.65, 0.03])
beta_slider = Slider(slider_beta, 'Beta', 1, 10, valinit=8/3)

# Reset button
reset_ax = plt.axes([0.8, 0.025, 0.1, 0.04])
reset_button = Button(reset_ax, 'Reset')

# Function to update parameters and restart animation
def update_params(event):
    global trajectory
    sigma = sigma_slider.val
    rho = rho_slider.val
    beta = beta_slider.val
    print(f"Updated parameters: sigma={sigma}, rho={rho}, beta={beta}")

    # Recompute trajectory with new parameters
    trajectory = lorenz_solver(sigma=sigma, rho=rho, beta=beta)
    print(f"Regenerated {len(trajectory)} trajectory points with new parameters.")

    # Restart animation
    ani.event_source.stop()
    ani = FuncAnimation(fig, update, frames=len(trajectory), interval=10, blit=False)

# Connect sliders to update function
sigma_slider.on_changed(update_params)
rho_slider.on_changed(update_params)
beta_slider.on_changed(update_params)

# Reset button function
def reset(event):
    sigma_slider.reset()
    rho_slider.reset()
    beta_slider.reset()
    update_params(None)

reset_button.on_clicked(reset)

# Show plot
plt.tight_layout()
plt.show()