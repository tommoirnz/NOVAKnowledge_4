import numpy as np
from scipy.linalg import sqrtm

def newton_square_root_matrix(A, tol=1e-10, max_iter=100):
    """
    Newton's method to compute the principal square root of a matrix A.
    Returns the matrix square root such that sqrt(A) * sqrt(A) = A.

    Parameters:
    A : numpy.ndarray
        Input square matrix (must be positive semidefinite for real square root)
    tol : float
        Tolerance for convergence
    max_iter : int
        Maximum number of iterations

    Returns:
    numpy.ndarray
        Square root matrix
    """
    # Initial guess (identity matrix)
    X = np.eye(A.shape[0])

    for i in range(max_iter):
        # Newton update: X_new = 0.5*(X + A/X)
        X_new = 0.5 * (X + np.dot(np.linalg.inv(X), A))

        # Check convergence
        if np.linalg.norm(X_new - X, 'fro') < tol:
            print(f"Converged in {i+1} iterations")
            return X_new

        X = X_new

    print(f"Warning: Did not converge in {max_iter} iterations")
    return X

# Test case: Square root of 9 (identity matrix case)
A = np.array([[9.0]])
print("Input matrix:")
print(A)

# Compute square root
sqrt_A = newton_square_root_matrix(A)
print("\nSquare root matrix:")
print(sqrt_A)
print("\nVerification:")
print("sqrt_A * sqrt_A =", np.dot(sqrt_A, sqrt_A))

# Test case: Square root of a 3x3 matrix
B = np.array([[9, 4, 2],
              [4, 4, 1],
              [2, 1, 1]])
print("\nInput 3x3 matrix:")
print(B)

sqrt_B = newton_square_root_matrix(B)
print("\nSquare root of 3x3 matrix:")
print(sqrt_B)
print("\nVerification:")
print("sqrt_B * sqrt_B =", np.dot(sqrt_B, sqrt_B))