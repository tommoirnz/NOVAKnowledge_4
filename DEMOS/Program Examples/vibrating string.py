import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def simulate_vibrating_string(L=1.0, N=100, T=2.0, dt=0.005, v=1.0):
    # Spatial and temporal discretization
    dx = L / N          # Spatial step
    dt = min(dt, dx / v) # Enforce CFL condition (dt ≤ dx/v)

    # Initialize string displacement (plucked at center)
    x = np.linspace(0, L, N)
    u = np.zeros(N)
    center = N // 2
    width = N // 10
    u[center - width:center + width] = 0.1 * np.sin(np.pi * (x[center - width:center + width] - L/2) / (L/2))

    # Set up plot
    fig, ax = plt.subplots(figsize=(10, 5))
    line, = ax.plot(x, u)
    ax.set_xlim(0, L)
    ax.set_ylim(-0.15, 0.15)
    ax.set_xlabel('Position (m)')
    ax.set_ylabel('Displacement (m)')
    ax.set_title('Vibrating String Simulation')

    # Initialize arrays for wave equation
    u_prev = u.copy()
    u_curr = u.copy()

    def update(frame):
        nonlocal u_curr, u_prev
        u_next = np.zeros_like(u_curr)

        # Explicit Euler method with fixed boundaries
        for i in range(1, N-1):
            u_next[i] = u_curr[i] + (v * dt / dx) ** 2 * 0.5 * (u_curr[i+1] - 2*u_curr[i] + u_curr[i-1])

        # Update arrays and boundaries
        u_next[0] = 0
        u_next[-1] = 0
        u_prev, u_curr = u_curr, u_next
        line.set_ydata(u_curr)
        return line,

    ani = FuncAnimation(fig, update, frames=int(T/dt), interval=20, blit=True)
    plt.tight_layout()
    plt.show()
    return ani

# Run simulation
simulate_vibrating_string(L=1.0, N=200, T=2.0, dt=0.005, v=1.0)