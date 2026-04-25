import numpy as np
import matplotlib.pyplot as plt
import sounddevice as sd  # For sound output
import time

# Piano note frequencies (Hz) for C4 to C5 major scale
notes = {
    'C4': 261.63,
    'D4': 293.66,
    'E4': 329.63,
    'F4': 349.23,
    'G4': 392.00,
    'A4': 440.00,
    'B4': 493.88,
    'C5': 523.25
}

# Parameters
sample_rate = 44100  # Standard audio sample rate
duration = 0.5  # Duration of each note in seconds
freqs = list(notes.values())
note_names = list(notes.keys())

# Generate sine wave for each note
def generate_sine_wave(freq, duration, sample_rate):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = np.sin(2 * np.pi * freq * t)
    return t, wave

# Play notes sequentially
def play_notes():
    for i, (name, freq) in enumerate(zip(note_names, freqs)):
        print(f"Playing {name} ({freq}Hz)...")
        t, wave = generate_sine_wave(freq, duration, sample_rate)
        sd.play(wave, sample_rate)
        sd.wait()  # Wait until sound finishes
        time.sleep(0.1)  # Small pause between notes

# Plot the waveform
def plot_waveform():
    plt.figure(figsize=(12, 6))
    for i, (name, freq) in enumerate(zip(note_names, freqs)):
        t, wave = generate_sine_wave(freq, duration, sample_rate)
        plt.subplot(len(note_names), 1, i+1)
        plt.plot(t, wave)
        plt.title(f"{name} ({freq}Hz)")
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")
        plt.grid(True)
    plt.tight_layout()
    plt.show()

# Main execution
if __name__ == "__main__":
    print("Generating and playing C4 to C5 major scale...")
    play_notes()
    print("\nNow plotting the waveforms...")
    plot_waveform()
    print("Complete!")