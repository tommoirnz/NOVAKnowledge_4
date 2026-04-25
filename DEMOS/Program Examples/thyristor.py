import numpy as np
import matplotlib.pyplot as plt

# --- Simulation Parameters ---
f = 60.0       # Input AC frequency (Hz)
T = 1/f        # Period of AC input
t = np.linspace(0, 2*T, 1000)  # Time vector (2 periods for clarity)
Vp = 1.0       # Peak voltage of AC phase (normalized)
load_resistance = 10.0  # Simulated load (ohms)
load_inductance = 0.05   # Simulated inductance (H)

# --- Phase Shift for 12-Pulse Converter ---
def phase_displacedVoltage(t, phase_shift):
    return Vp * np.sin(2 * np.pi * f * t + phase_shift)

# --- Gating Signals for Thyristor Firing (6-Pulse) ---
def six_pulse_gate(t):
    angle = 2 * np.pi * f * t
    fire_angle_rad = np.pi / 6  # 30° (π/6) firing angle (simplified)
    gate_signal = np.zeros_like(t)
    for i in range(len(t)):
        if np.mod(angle[i], 2*np.pi) <= fire_angle_rad or np.mod(angle[i], 2*np.pi) >= 5*np.pi/6:
            gate_signal[i] = 1  # Firing pulse (simplified)
    return gate_signal

# --- Gating Signals for 12-Pulse (Two 6-Pulse Sets with 30° Shift) ---
def twelve_pulse_gate(t):
    six_pulse1 = six_pulse_gate(t)
    six_pulse2 = six_pulse_gate(t - 1/(6*f))  # 30° phase shift (1/6 cycle delay)
    return six_pulse1 + six_pulse2  # Combined firing pulses

# --- Output Voltage Calculation (6-Pulse) ---
def six_pulse_output(t, gate_signal):
    v_abc = [Vp * np.sin(2 * np.pi * f * t),
             Vp * np.sin(2 * np.pi * f * t - 2 * np.pi / 3),
             Vp * np.sin(2 * np.pi * f * t - 4 * np.pi / 3)]
    output = np.zeros_like(t)
    for i in range(len(t)):
        if gate_signal[i] == 1:
            output[i] = max(v_abc[0][i], v_abc[1][i], v_abc[2][i])
    return output

# --- Output Voltage Calculation (12-Pulse) ---
def twelve_pulse_output(t, gate_signal):
    v_abc = [Vp * np.sin(2 * np.pi * f * t),
             Vp * np.sin(2 * np.pi * f * t - 2 * np.pi / 3),
             Vp * np.sin(2 * np.pi * f * t - 4 * np.pi / 3)]
    v_def = [Vp * np.sin(2 * np.pi * f * t - np.pi/3),  # 30° shift from ABC
             Vp * np.sin(2 * np.pi * f * t - np.pi/3 - 2 * np.pi / 3),
             Vp * np.sin(2 * np.pi * f * t - np.pi/3 - 4 * np.pi / 3)]
    output = np.zeros_like(t)
    for i in range(len(t)):
        if gate_signal[i] == 1:
            output[i] = max(max(v_abc[0][i], v_abc[1][i], v_abc[2][i]), max(v_def[0][i], v_def[1][i], v_def[2][i]))
    return output

# --- Compute Signals ---
six_pulse_gate_signal = six_pulse_gate(t)
twelve_pulse_gate_signal = twelve_pulse_gate(t)

six_pulse_output_voltage = six_pulse_output(t, six_pulse_gate_signal)
twelve_pulse_output_voltage = twelve_pulse_output(t, twelve_pulse_gate_signal)

# --- Plotting ---
plt.figure(figsize=(14, 10))

# Input 3-Phase Voltages (6-Pulse)
plt.subplot(4, 1, 1)
plt.plot(t, Vp * np.sin(2 * np.pi * f * t), label='Phase A')
plt.plot(t, Vp * np.sin(2 * np.pi * f * t - 2 * np.pi / 3), label='Phase B')
plt.plot(t, Vp * np.sin(2 * np.pi * f * t - 4 * np.pi / 3), label='Phase C')
plt.title('Input 3-Phase AC Voltages (6-Pulse)')
plt.xlabel('Time (s)')
plt.ylabel('Voltage (Normalized)')
plt.legend()
plt.grid(True)

# Input 3-Phase Voltages (12-Pulse, shifted by 30°)
plt.subplot(4, 1, 2)
plt.plot(t, Vp * np.sin(2 * np.pi * f * t), label='Phase A')
plt.plot(t, Vp * np.sin(2 * np.pi * f * t - np.pi/3), label='Phase D (Shifted)')
plt.plot(t, Vp * np.sin(2 * np.pi * f * t - np.pi), label='Phase E (Shifted)')
plt.title('Input 3-Phase Voltages (12-Pulse, 30° Shift)')
plt.xlabel('Time (s)')
plt.ylabel('Voltage (Normalized)')
plt.legend()
plt.grid(True)

# Output Voltage (6-Pulse vs 12-Pulse)
plt.subplot(4, 1, 3)
plt.plot(t, six_pulse_output_voltage, label='6-Pulse Output', color='red')
plt.plot(t, twelve_pulse_output_voltage, label='12-Pulse Output', color='blue')
plt.title('DC Output Voltage Comparison')
plt.xlabel('Time (s)')
plt.ylabel('Output Voltage (Normalized)')
plt.legend()
plt.grid(True)

# Gating Signals (Pulses)
plt.subplot(4, 1, 4)
plt.plot(t, six_pulse_gate_signal, label='6-Pulse Gate', color='red')
plt.plot(t, twelve_pulse_gate_signal, label='12-Pulse Gate', color='blue')
plt.title('Thyristor Gating Signals')
plt.xlabel('Time (s)')
plt.ylabel('Gate Signal (1=Firing)')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()