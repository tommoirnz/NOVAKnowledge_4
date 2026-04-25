import tkinter as tk
import time
from math import sin, cos, radians

class AnalogClock:
    def __init__(self, root):
        self.root = root
        self.root.title("Analog Clock")
        self.canvas = tk.Canvas(root, width=300, height=300, bg="black")
        self.canvas.pack()

        # Clock parameters
        self.center_x, self.center_y = 150, 150
        self.radius = 100

        # Draw clock face
        self.draw_clock_face()

        # Initialize hands
        self.hour_hand = self.canvas.create_line(
            self.center_x, self.center_y,
            self.center_x + self.radius, self.center_y,
            width=4, fill="white"
        )
        self.minute_hand = self.canvas.create_line(
            self.center_x, self.center_y,
            self.center_x + self.radius, self.center_y,
            width=3, fill="blue"
        )
        self.second_hand = self.canvas.create_line(
            self.center_x, self.center_y,
            self.center_x + self.radius, self.center_y,
            width=1, fill="red"
        )

        # Draw center dot
        self.center_dot = self.canvas.create_oval(
            self.center_x - 3, self.center_y - 3,
            self.center_x + 3, self.center_y + 3,
            fill="white"
        )

        # Start updating time
        self.update_time()

    def draw_clock_face(self):
        # Draw circle (clock face)
        self.canvas.create_oval(
            self.center_x - self.radius, self.center_y - self.radius,
            self.center_x + self.radius, self.center_y + self.radius,
            width=2, outline="white", fill="black"
        )

        # Draw hour markers
        for i in range(12):
            angle = radians(i * 30 - 90)
            x1 = self.center_x + (self.radius - 15) * cos(angle)
            y1 = self.center_y + (self.radius - 15) * sin(angle)
            x2 = self.center_x + self.radius * cos(angle)
            y2 = self.center_y + self.radius * sin(angle)
            self.canvas.create_line(x1, y1, x2, y2, width=2, fill="white")

        # Draw minute markers
        for i in range(60):
            angle = radians(i * 6 - 90)
            if i % 5 != 0:  # Skip hour markers
                x1 = self.center_x + (self.radius - 10) * cos(angle)
                y1 = self.center_y + (self.radius - 10) * sin(angle)
                x2 = self.center_x + (self.radius - 5) * cos(angle)
                y2 = self.center_y + (self.radius - 5) * sin(angle)
                self.canvas.create_line(x1, y1, x2, y2, width=1, fill="white")

    def update_time(self):
        current_time = time.localtime()
        hour = current_time.tm_hour % 12
        minute = current_time.tm_min
        second = current_time.tm_sec

        # Calculate angles (in degrees)
        hour_angle = (hour * 30) + (minute * 0.5)
        minute_angle = minute * 6
        second_angle = second * 6

        # Convert to radians and calculate hand positions
        hour_x = self.center_x + (self.radius - 30) * cos(radians(hour_angle - 90))
        hour_y = self.center_y + (self.radius - 30) * sin(radians(hour_angle - 90))
        minute_x = self.center_x + (self.radius - 40) * cos(radians(minute_angle - 90))
        minute_y = self.center_y + (self.radius - 40) * sin(radians(minute_angle - 90))
        second_x = self.center_x + (self.radius - 50) * cos(radians(second_angle - 90))
        second_y = self.center_y + (self.radius - 50) * sin(radians(second_angle - 90))

        # Update hand positions
        self.canvas.coords(
            self.hour_hand,
            self.center_x, self.center_y,
            hour_x, hour_y
        )
        self.canvas.coords(
            self.minute_hand,
            self.center_x, self.center_y,
            minute_x, minute_y
        )
        self.canvas.coords(
            self.second_hand,
            self.center_x, self.center_y,
            second_x, second_y
        )

        # Schedule next update
        self.root.after(1000, self.update_time)

if __name__ == "__main__":
    root = tk.Tk()
    clock = AnalogClock(root)
    root.mainloop()
