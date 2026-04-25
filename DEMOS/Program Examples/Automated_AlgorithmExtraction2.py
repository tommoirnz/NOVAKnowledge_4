# Continuous-Time Division via Negative Feedback

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from typing import Callable, Optional, Tuple


def compute_reciprocal_continuous(
    x: float,
    w0: float,
    K: float,
    t_span: Tuple[float, float] = (0, 10),
    t_eval: Optional[np.ndarray] = None,
) -> dict:
    """
    Compute the reciprocal of a scalar x using continuous-time negative feedback.

    The system is governed by the nonlinear ODE:
        dw(t)/dt = K * (1 - w(t) * x)

    At equilibrium (dw/dt = 0), we get:
        1 - w* * x = 0  =>  w* = 1/x

    Stability requires sgn(K) = sgn(x) to ensure negative feedback.
    The time constant of convergence is T = 1 / (K * x).

    Parameters
    ----------
    x : float
        The scalar value whose reciprocal is to be computed (x != 0).
    w0 : float
        Initial estimate of 1/x (the initial condition w(0)).
    K : float
        Integrator gain. Must satisfy sgn(K) = sgn(x) for stability.
    t_span : tuple of float
        Time interval (t_start, t_end) for the simulation.
    t_eval : np.ndarray, optional
        Specific time points at which to evaluate the solution.
        If None, the solver chooses the points automatically.

    Returns
    -------
    dict with keys:
        't'          : time points
        'w'          : w(t) trajectory (estimate of 1/x over time)
        'error'      : e(t) = 1 - w(t)*x  (the feedback error signal)
        'w_star'     : theoretical equilibrium value (1/x)
        'time_const' : theoretical time constant T = 1/(K*x)
        'x'          : the input value
    """
    # --- Input validation ---
    if x == 0:
        raise ValueError("x must be non-zero (cannot compute reciprocal of zero).")
    if np.sign(K) != np.sign(x):
        raise ValueError(
            f"Stability violated: sgn(K)={np.sign(K)} must equal sgn(x)={np.sign(x)}. "
            "Mismatched signs cause positive feedback and divergence."
        )

    # --- Theoretical values ---
    w_star = 1.0 / x          # Equilibrium: the true reciprocal
    time_const = 1.0 / (K * x)  # Time constant of exponential convergence

    # --- Define the ODE: dw/dt = K * (1 - w*x) ---
    def ode(t: float, w: list) -> list:
        """
        Right-hand side of the feedback ODE.

        The error signal e(t) = 1 - w(t)*x drives the integrator.
        When e > 0, w increases; when e < 0, w decreases.
        """
        error = 1.0 - w[0] * x   # Feedback error: e(t) = 1 - w(t)*x
        dw_dt = K * error         # Integrator: dw/dt = K * e(t)
        return [dw_dt]

    # --- Solve the ODE numerically ---
    solution = solve_ivp(
        fun=ode,
        t_span=t_span,
        y0=[w0],          # Initial condition
        t_eval=t_eval,
        method="RK45",    # Runge-Kutta 4(5) adaptive step solver
        rtol=1e-9,
        atol=1e-12,
    )

    if not solution.success:
        raise RuntimeError(f"ODE solver failed: {solution.message}")

    t_out = solution.t
    w_out = solution.y[0]

    # --- Compute the error signal e(t) = 1 - w(t)*x at each time point ---
    error_out = 1.0 - w_out * x

    return {
        "t": t_out,
        "w": w_out,
        "error": error_out,
        "w_star": w_star,
        "time_const": time_const,
        "x": x,
    }


def analytical_solution(
    x: float,
    w0: float,
    K: float,
    t: np.ndarray,
) -> np.ndarray:
    """
    Compute the analytical (closed-form) solution of the feedback ODE.

    The ODE dw/dt = K*(1 - w*x) is a first-order linear ODE with solution:

        w(t) = 1/x + (w0 - 1/x) * exp(-K*x*t)

    This shows exponential convergence to 1/x with time constant T = 1/(K*x).

    Parameters
    ----------
    x : float
        Input scalar (x != 0).
    w0 : float
        Initial condition w(0).
    K : float
        Integrator gain (sgn(K) = sgn(x) for stability).
    t : np.ndarray
        Time points at which to evaluate the solution.

    Returns
    -------
    np.ndarray
        Analytical w(t) at each time point in t.
    """
    w_star = 1.0 / x
    # Exponential decay of the initial error toward equilibrium
    return w_star + (w0 - w_star) * np.exp(-K * x * t)


def plot_results(result: dict, analytical: Optional[np.ndarray] = None) -> None:
    """
    Plot the trajectory w(t), the error e(t), and compare with the analytical solution.

    Parameters
    ----------
    result : dict
        Output dictionary from compute_reciprocal_continuous().
    analytical : np.ndarray, optional
        Analytical solution values at result['t'] for comparison.
    """
    t = result["t"]
    w = result["w"]
    error = result["error"]
    w_star = result["w_star"]
    time_const = result["time_const"]
    x = result["x"]

    fig, axes = plt.subplots(2, 1, figsize=(10, 8))
    fig.suptitle(
        f"Continuous-Time Reciprocal via Negative Feedback\n"
        f"x = {x},  1/x = {w_star:.6f},  K = {result.get('K', 'N/A')},  "
        f"τ = {time_const:.4f}",
        fontsize=13,
    )

    # --- Top plot: w(t) trajectory ---
    ax1 = axes[0]
    ax1.plot(t, w, label="Numerical w(t)", color="steelblue", linewidth=2)
    if analytical is not None:
        ax1.plot(
            t, analytical, "--", label="Analytical w(t)", color="orange", linewidth=2
        )
    ax1.axhline(w_star, color="red", linestyle=":", linewidth=1.5, label=f"w* = 1/x = {w_star:.6f}")
    ax1.axvline(time_const, color="gray", linestyle="--", linewidth=1, label=f"τ = {time_const:.4f}")
    ax1.set_xlabel("Time t")
    ax1.set_ylabel("w(t)")
    ax1.set_title("Estimate w(t) converging to 1/x")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # --- Bottom plot: error signal e(t) = 1 - w(t)*x ---
    ax2 = axes[1]
    ax2.plot(t, error, label="Error e(t) = 1 - w(t)·x", color="crimson", linewidth=2)
    ax2.axhline(0, color="black", linestyle="--", linewidth=1)
    ax2.set_xlabel("Time t")
    ax2.set_ylabel("e(t)")
    ax2.set_title("Feedback Error Signal e(t) → 0")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == "__main__":

    print("=" * 60)
    print("  Continuous-Time Division via Negative Feedback")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Example 1: Compute 1/x for a positive scalar
    # ------------------------------------------------------------------
    x_val = 4.0       # We want to compute 1/4 = 0.25
    K_val = 2.0       # Gain: sgn(K) = sgn(x) = positive => stable
    w0_val = 0.0      # Initial estimate (start from zero)
    t_end = 5.0       # Simulate for 5 time units

    t_eval_pts = np.linspace(0, t_end, 1000)

    print(f"\nExample 1: x = {x_val}")
    print(f"  True reciprocal  : 1/x = {1/x_val:.6f}")
    print(f"  Gain K           : {K_val}")
    print(f"  Initial estimate : w(0) = {w0_val}")
    print(f"  Time constant    : τ = 1/(K·x) = {1/(K_val*x_val):.4f}")

    result1 = compute_reciprocal_continuous(
        x=x_val,
        w0=w0_val,
        K=K_val,
        t_span=(0, t_end),
        t_eval=t_eval_pts,
    )

    # Analytical solution for comparison
    analytical1 = analytical_solution(x_val, w0_val, K_val, t_eval_pts)

    # Report final values
    w_final = result1["w"][-1]
    print(f"\n  Numerical w(T_end)  : {w_final:.8f}")
    print(f"  Analytical w(T_end) : {analytical1[-1]:.8f}")
    print(f"  True 1/x            : {1/x_val:.8f}")
    print(f"  Absolute error      : {abs(w_final - 1/x_val):.2e}")

    # Store K in result for plot title
    result1["K"] = K_val
    plot_results(result1, analytical=analytical1)

    # ------------------------------------------------------------------
    # Example 2: Compute 1/x for a negative scalar
    # ------------------------------------------------------------------
    x_neg = -3.0      # We want to compute 1/(-3) ≈ -0.3333
    K_neg = -1.5      # Gain must be negative to match sgn(x) = negative
    w0_neg = 0.0

    print("\n" + "=" * 60)
    print(f"Example 2: x = {x_neg}  (negative input)")
    print(f"  True reciprocal  : 1/x = {1/x_neg:.6f}")
    print(f"  Gain K           : {K_neg}  (negative, matching sgn(x))")
    print(f"  Time constant    : τ = 1/(K·x) = {1/(K_neg*x_neg):.4f}")

    result2 = compute_reciprocal_continuous(
        x=x_neg,
        w0=w0_neg,
        K=K_neg,
        t_span=(0, 5),
        t_eval=np.linspace(0, 5, 1000),
    )

    analytical2 = analytical_solution(x_neg, w0_neg, K_neg, result2["t"])

    w_final2 = result2["w"][-1]
    print(f"\n  Numerical w(T_end)  : {w_final2:.8f}")
    print(f"  True 1/x            : {1/x_neg:.8f}")
    print(f"  Absolute error      : {abs(w_final2 - 1/x_neg):.2e}")

    result2["K"] = K_neg
    plot_results(result2, analytical=analytical2)

    # ------------------------------------------------------------------
    # Example 3: Effect of gain K on convergence speed
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("Example 3: Effect of gain K on convergence speed")
    print(f"  x = 2.0,  True 1/x = {1/2.0:.4f}")
    print()

    x_demo = 2.0
    gains = [0.5, 1.0, 3.0, 8.0]
    t_demo = np.linspace(0, 4, 500)

    plt.figure(figsize=(10, 5))
    for K_demo in gains:
        res = compute_reciprocal_continuous(
            x=x_demo, w0=0.0, K=K_demo, t_span=(0, 4), t_eval=t_demo
        )
        tau = res["time_const"]
        plt.plot(res["t"], res["w"], label=f"K={K_demo}, τ={tau:.3f}")
        print(f"  K = {K_demo:4.1f} | τ = {tau:.4f} | w(final) = {res['w'][-1]:.6f}")

    plt.axhline(1 / x_demo, color="red", linestyle="--", linewidth=2, label=f"1/x = {1/x_demo}")
    plt.xlabel("Time t")
    plt.ylabel("w(t)")
    plt.title(f"Convergence Speed vs. Gain K  (x = {x_demo})")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

    # ------------------------------------------------------------------
    # Example 4: Demonstrate instability when sgn(K) != sgn(x)
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("Example 4: Instability demonstration (wrong sign of K)")
    try:
        bad_result = compute_reciprocal_continuous(
            x=4.0,
            w0=0.1,
            K=-1.0,   # Wrong sign! sgn(K)=-1 but sgn(x)=+1 => positive feedback
            t_span=(0, 5),
        )
    except ValueError as e:
        print(f"  Caught expected error: {e}")