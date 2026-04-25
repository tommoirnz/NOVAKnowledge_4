import tkinter as tk
from tkinter import ttk, font
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class WaveformGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Waveform Generator")
        self.root.geometry("800x600")

        # Default parameters
        self.frequency = 1.0
        self.amplitude = 1.0
        self.wave_type = "sine"
        self.time_points = 1000

        # Create GUI elements
        self.create_widgets()

        # Initialize plot
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Initial plot
        self.update_plot()

    def create_widgets(self):
        # Wave type selector
        self.wave_type_label = ttk.Label(self.root, text="Wave Type:")
        self.wave_type_label.pack(pady=5)

        self.wave_type_var = tk.StringVar(value="sine")
        self.wave_type_menu = ttk.Combobox(
            self.root,
            textvariable=self.wave_type_var,
            values=["sine", "square", "triangle"],
            state="readonly"
        )
        self.wave_type_menu.pack(pady=5)
        self.wave_type_menu.bind("<<ComboboxSelected>>", self.on_wave_type_change)

        # Frequency control
        self.freq_frame = ttk.Frame(self.root)
        self.freq_frame.pack(pady=10)

        ttk.Label(self.freq_frame, text="Frequency:").pack(side=tk.LEFT)
        self.freq_slider = ttk.Scale(
            self.freq_frame,
            from_=0.1,
            to=20.0,
            value=1.0,
            orient=tk.HORIZONTAL,
            command=self.on_frequency_change
        )
        self.freq_slider.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Amplitude control
        self.amp_frame = ttk.Frame(self.root)
        self.amp_frame.pack(pady=10)

        ttk.Label(self.amp_frame, text="Amplitude:").pack(side=tk.LEFT)
        self.amp_slider = ttk.Scale(
            self.amp_frame,
            from_=0.1,
            to=2.0,
            value=1.0,
            orient=tk.HORIZONTAL,
            command=self.on_amplitude_change
        )
        self.amp_slider.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Update button
        self.update_button = ttk.Button(
            self.root,
            text="Update Waveform",
            command=self.update_plot
        )
        self.update_button.pack(pady=10)

    def on_wave_type_change(self, event=None):
        self.wave_type = self.wave_type_var.get()
        self.update_plot()

    def on_frequency_change(self, value):
        self.frequency = float(value)
        self.update_plot()

    def on_amplitude_change(self, value):
        self.amplitude = float(value)
        self.update_plot()

    def generate_wave(self):
        t = np.linspace(0, 10, self.time_points)
        if self.wave_type == "sine":
            wave = self.amplitude * np.sin(2 * np.pi * self.frequency * t)
        elif self.wave_type == "square":
            wave = self.amplitude * np.sign(np.sin(2 * np.pi * self.frequency * t))
        elif self.wave_type == "triangle":
            wave = self.amplitude * (2/np.pi) * np.arcsin(np.sin(2 * np.pi * self.frequency * t))
        return t, wave

    def update_plot(self):
        t, wave = self.generate_wave()

        # Clear previous plot
        self.ax.clear()

        # Plot new wave
        self.ax.plot(t, wave, linewidth=2)
        self.ax.set_title(f"{self.wave_type.capitalize()} Wave (f={self.frequency:.1f}Hz)")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Amplitude")
        self.ax.grid(True)

        # Adjust y-axis limits
        self.ax.set_ylim(-1.2*self.amplitude, 1.2*self.amplitude)

        # Redraw canvas
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = WaveformGenerator(root)
    print("Waveform Generator started. Controls:")
    print("1. Select wave type (sine/square/triangle)")
    print("2. Adjust frequency with slider (0.1-20Hz)")
    print("3. Adjust amplitude with slider (0.1-2.0)")
    print("4. Click 'Update Waveform' to refresh")
    root.mainloop()