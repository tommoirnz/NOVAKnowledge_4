import numpy as np


def matrix_inversion_negative_feedback(
    X: np.ndarray,
    eta: float = 0.1,
    W0: np.ndarray = None,
    delta: float = 1e-5,
    max_iterations: int = 100_000,
) -> tuple[np.ndarray, list[float], int]:
    """
    Compute the inverse of matrix X using a negative feedback iterative scheme.

    The update rule is:
        W_{k+1} = W_k + eta * (I - W_k @ X)

    This drives W toward X^{-1} by minimising the error (I - W_k @ X).
    The term (I - W_k @ X) acts as a negative feedback signal: when W_k
    is the true inverse, this error term is zero and the iteration stops.

    Parameters
    ----------
    X : np.ndarray
        Square, invertible matrix to invert (shape: n x n).
    eta : float
        Learning rate (step size). Must satisfy 0 < eta < 2 / sigma_max^2,
        where sigma_max is the largest singular value of X, to guarantee
        convergence.
    W0 : np.ndarray, optional
        Initial guess for the inverse (shape: n x n).
        Defaults to eta * X.T (a common stable initialisation).
    delta : float
        Convergence threshold for the normalised Frobenius error norm.
        Iteration stops when ||X @ W_k - I||_F / ||X||_F < delta.
    max_iterations : int
        Safety cap on the number of iterations.

    Returns
    -------
    W : np.ndarray
        Approximation of X^{-1}.
    error_history : list[float]
        Normalised error norm recorded at each iteration.
    k : int
        Number of iterations performed.
    """
    n = X.shape[0]
    assert X.shape == (n, n), "X must be a square matrix."

    I = np.eye(n)

    # Default initialisation: W0 = eta * X^T is a standard choice that
    # ensures the initial iterate is in a convergent regime.
    if W0 is None:
        W0 = eta * X.T

    W = W0.copy()
    error_history = []

    for k in range(max_iterations):
        # --- Compute normalised error norm (stopping criterion) ---
        # e_n = ||X @ W_k - I||_F / ||X||_F
        # Note: the paper uses XW (right inverse check); we check X @ W here.
        residual = X @ W - I
        e_n = np.linalg.norm(residual, "fro") / np.linalg.norm(X, "fro")
        error_history.append(e_n)

        # --- Check convergence ---
        if e_n < delta:
            print(f"Converged after {k} iterations (e_n = {e_n:.2e} < delta = {delta:.2e})")
            break

        # --- Negative feedback update rule ---
        # W_{k+1} = W_k + eta * (I - W_k @ X)
        # The correction term (I - W_k @ X) is zero when W_k = X^{-1},
        # making the fixed point exactly the matrix inverse.
        W = W + eta * (I - W @ X)

    else:
        print(f"Warning: did not converge within {max_iterations} iterations. "
              f"Final e_n = {error_history[-1]:.2e}")

    return W, error_history, k


def suggest_eta(X: np.ndarray) -> float:
    """
    Suggest a safe learning rate eta based on the spectral norm of X.

    Convergence is guaranteed when:
        0 < eta < 2 / sigma_max^2

    where sigma_max is the largest singular value of X.
    We use eta = 1 / sigma_max^2 as a conservative, stable default.

    Parameters
    ----------
    X : np.ndarray
        The matrix to invert.

    Returns
    -------
    float
        A suggested learning rate.
    """
    sigma_max = np.linalg.norm(X, ord=2)  # largest singular value
    return 1.0 / (sigma_max ** 2)


# ---------------------------------------------------------------------------
# Usage example
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    np.random.seed(42)

    # ------------------------------------------------------------------ #
    # Example 1: Small well-conditioned matrix
    # ------------------------------------------------------------------ #
    print("=" * 60)
    print("Example 1: 3x3 random well-conditioned matrix")
    print("=" * 60)

    X = np.array([[4.0, 1.0, 0.5],
                  [1.0, 3.0, 0.2],
                  [0.5, 0.2, 2.0]])

    eta = suggest_eta(X)
    print(f"Suggested eta: {eta:.6f}")

    W_approx, errors, iters = matrix_inversion_negative_feedback(
        X, eta=eta, delta=1e-8
    )

    X_inv_true = np.linalg.inv(X)

    print(f"\nApproximated inverse (after {iters} iterations):\n{W_approx}")
    print(f"\nTrue inverse (numpy):\n{X_inv_true}")
    print(f"\nMax absolute difference: {np.max(np.abs(W_approx - X_inv_true)):.2e}")
    print(f"Verification X @ W ≈ I:\n{np.round(X @ W_approx, 6)}")

    # ------------------------------------------------------------------ #
    # Example 2: Larger random matrix
    # ------------------------------------------------------------------ #
    print("\n" + "=" * 60)
    print("Example 2: 10x10 random matrix")
    print("=" * 60)

    n = 10
    A = np.random.randn(n, n)
    # Make it diagonally dominant to ensure invertibility
    A += n * np.eye(n)

    eta2 = suggest_eta(A)
    print(f"Suggested eta: {eta2:.6f}")

    W2, errors2, iters2 = matrix_inversion_negative_feedback(
        A, eta=eta2, delta=1e-7
    )

    A_inv_true = np.linalg.inv(A)
    print(f"Max absolute difference: {np.max(np.abs(W2 - A_inv_true)):.2e}")
    print(f"Verification ||A @ W - I||_F: {np.linalg.norm(A @ W2 - np.eye(n), 'fro'):.2e}")

    # ------------------------------------------------------------------ #
    # Plot convergence (optional — requires matplotlib)
    # ------------------------------------------------------------------ #
    try:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(12, 4))

        axes[0].semilogy(errors, color="steelblue", linewidth=1.5)
        axes[0].axhline(1e-8, color="red", linestyle="--", label="delta = 1e-8")
        axes[0].set_title("Example 1: 3×3 Matrix — Convergence")
        axes[0].set_xlabel("Iteration")
        axes[0].set_ylabel("Normalised error norm (log scale)")
        axes[0].legend()
        axes[0].grid(True, which="both", alpha=0.4)

        axes[1].semilogy(errors2, color="darkorange", linewidth=1.5)
        axes[1].axhline(1e-7, color="red", linestyle="--", label="delta = 1e-7")
        axes[1].set_title("Example 2: 10×10 Matrix — Convergence")
        axes[1].set_xlabel("Iteration")
        axes[1].set_ylabel("Normalised error norm (log scale)")
        axes[1].legend()
        axes[1].grid(True, which="both", alpha=0.4)

        plt.tight_layout()
        plt.savefig("convergence.png", dpi=150)
        plt.show()
        print("\nConvergence plot saved to 'convergence.png'.")
    except ImportError:
        print("\nmatplotlib not available — skipping convergence plot.")