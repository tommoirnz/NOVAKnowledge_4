#!/usr/bin/env python3
"""
Simple Close Encounters Player
Plays: A4, B4, G4, G3, D4 (with D4 twice as long)
"""

import numpy as np
import sounddevice as sd
import time


def play_tone(frequency, duration, sample_rate=44100, volume=0.3):
    """Generate and play a sine wave tone"""
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # Create sine wave
    wave = volume * np.sin(2 * np.pi * frequency * t)

    # Apply fade in/out to prevent clicks
    fade_samples = int(0.01 * sample_rate)
    if fade_samples > 0:
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        wave[:fade_samples] *= fade_in
        wave[-fade_samples:] *= fade_out

    # Play the sound
    sd.play(wave, sample_rate, blocking=True)


def main():
    """Play A4, B4, G4, G3, D4 (with D4 twice as long)"""
    print("🎵 Playing Close Encounters: A4, B4, G4, G3, D4 (long) 🎵")
    print("-" * 40)

    # A4, B4, G4, G3, D4 (last note is 1.2 seconds - twice the normal 0.6)
    notes = [
        ("A4", 440.00, 0.4),  # A4
        ("B4", 493.88, 0.4),  # B4
        ("G4", 392.00, 0.4),  # G4
        ("G3", 196.00, 0.6),  # G3 (octave lower)
        ("D4", 293.66, 1.2),  # D4 - TWICE AS LONG (2 × 0.6 = 1.2 seconds)
    ]

    for i, (note_name, frequency, duration) in enumerate(notes):
        print(f"Note {i + 1}: {note_name} ({frequency:.1f} Hz) for {duration}s")
        play_tone(frequency, duration)

        # Short pause between notes (except after last one)
        if i < len(notes) - 1:
            time.sleep(0.15)

    print("-" * 40)
    print("🎵 Complete! 🎵")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure you have the required libraries installed:")
        print("  pip install numpy sounddevice")
