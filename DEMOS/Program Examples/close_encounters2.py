import sounddevice as sd
import numpy as np
import time

def play_close_encounters_sequence():
    # Define notes (frequency in Hz) and durations (milliseconds)
    notes = [
        ("G4", 392, 500),   # G4 (392 Hz), 500ms
        ("A4", 440, 500),   # A4 (440 Hz), 500ms
        ("F4", 349, 500),   # F4 (349 Hz), 500ms
        ("F3", 174.6, 1000), # F3 (174.6 Hz), 1s
        ("C4", 261.6, 2000) # C4 (261.6 Hz), 2s (longest)
    ]

    # Sampling rate and duration for each note
    fs = 44100  # Sample rate
    duration = 0.1  # Short duration for each note (will be scaled by note duration)

    print("Playing Close Encounters sequence...")

    for note_name, freq, duration_ms in notes:
        # Calculate number of samples for this note
        n_samples = int(duration_ms / 1000 * fs)

        # Generate sine wave
        t = np.linspace(0, duration_ms / 1000, n_samples, False)
        audio = 0.5 * np.sin(2 * np.pi * freq * t)

        # Play the note
        sd.play(audio, fs)
        print(f"Playing {note_name} ({freq} Hz) for {duration_ms}ms")

        # Wait for the note to finish
        sd.wait()

        # Add pause between notes (except after last note)
        if note_name != "C4":
            time.sleep(0.1)  # Small pause between notes

    print("Sequence complete!")

# Run the function
play_close_encounters_sequence()