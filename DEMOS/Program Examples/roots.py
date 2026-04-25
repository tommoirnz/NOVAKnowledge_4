import numpy as np

def polynomial(x):
    """Polynomial function to find roots of"""
    return 2*x**4 - 5*x**3 + x**2 + 7*x - 4

def find_all_roots():
    """Find all roots (real and complex) using NumPy's roots function"""
    # Create coefficient list [a4, a3, a2, a1, a0] for 2x⁴ -5x³ +x² +7x -4
    coeffs = [2, -5, 1, 7, -4]

    # Get all roots (real and complex)
    all_roots = np.roots(coeffs)

    # Filter and format results
    results = []
    for root in all_roots:
        if np.isreal(root):
            # Real root - format to 6 decimal places
            results.append(f"x = {root.real:.6f} (real)")
        else:
            # Complex root - format as a+ib
            real_part = root.real
            imag_part = root.imag
            results.append(f"x = {real_part:+.6f} + {imag_part:+.6f}i")

    return results

# Find and display all roots
all_roots = find_all_roots()

print("Complete root analysis for polynomial 2x⁴ - 5x³ + x² + 7x - 4:")
print("="*60)
for i, root in enumerate(all_roots, 1):
    print(f"Root {i}: {root}")
print("="*60)