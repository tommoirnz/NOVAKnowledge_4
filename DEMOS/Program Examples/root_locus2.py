import control as ctrl
import matplotlib.pyplot as plt

# Define the open-loop transfer function (example system)
numerator = [1]  # K is handled automatically as a parameter
denominator = [1, 6, 11, 6]  # (s+1)(s+2)(s+3) = s³ + 6s² + 11s + 6

# Create a transfer function object
sys = ctrl.TransferFunction(numerator, denominator)

# Plot the root locus
ctrl.root_locus(sys)

# Add labels and title
plt.title('Root Locus of Third-Order System')
plt.xlabel('Real Axis')
plt.ylabel('Imaginary Axis')
plt.grid(True)
plt.show()
