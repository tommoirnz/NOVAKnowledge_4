import tkinter as tk
import math
import time

def main():
    # Initialize Tkinter root window
    root = tk.Tk()
    root.title("Analog Clock")
    root.resizable(False, False)
    canvas = tk.Canvas(root, width=300, height=300, bg="#000000")
    canvas.pack()

    # Clock face properties
    CENTER_X = 150
    CENTER_Y = 150
    HOUR_HAND_LENGTH = 80
    MINUTE_HAND_LENGTH = 120
    SECOND_HAND_LENGTH = 130
    BACKGROUND_COLOR = "#000000"
    CLOCK_FACE_COLOR = "#FFFFFF"
    NUMBER_COLOR = "#FFFFFF"

    # Draw clock face
    canvas.create_oval(20, 20, 280, 280, outline=CLOCK_FACE_COLOR, width=2)
    for i in range(12):
        angle = math.radians(i * 30 - 90)
        x1 = CENTER_X + math.cos(angle) * 100
        y1 = CENTER_Y + math.sin(angle) * 100
        x2 = CENTER_X + math.cos(angle) * 110
        y2 = CENTER_Y + math.sin(angle) * 110
        canvas.create_line(x1, y1, x2, y2, fill=CLOCK_FACE_COLOR, width=2)

        # Draw hour numbers
        angle_text = math.radians(i * 30 - 90)
        x_text = CENTER_X + math.cos(angle_text) * 90
        y_text = CENTER_Y + math.sin(angle_text) * 90
        canvas.create_text(x_text, y_text, text=str(i % 12 or 12), fill=NUMBER_COLOR, font=("Arial", 10))

    # Function to draw clock hands
    def draw_clock_hands():
        # Get current time
        current_time = time.localtime()
        hour = current_time.tm_hour % 12
        minute = current_time.tm_min
        second = current_time.tm_sec

        # Clear previous hand positions
        canvas.delete("hands")

        # Calculate hand angles in radians
        hour_angle = math.radians((hour * 30) - 90 + (minute * 0.5))
        minute_angle = math.radians((minute * 6) - 90)
        second_angle = math.radians((second * 6) - 90)

        # Draw hour hand
        hour_x = CENTER_X + math.cos(hour_angle) * (HOUR_HAND_LENGTH - 20)
        hour_y = CENTER_Y + math.sin(hour_angle) * (HOUR_HAND_LENGTH - 20)
        canvas.create_line(CENTER_X, CENTER_Y, hour_x, hour_y,
                          fill="#FF0000", width=4, tags="hands")

        # Draw minute hand
        minute_x = CENTER_X + math.cos(minute_angle) * (MINUTE_HAND_LENGTH - 20)
        minute_y = CENTER_Y + math.sin(minute_angle) * (MINUTE_HAND_LENGTH - 20)
        canvas.create_line(CENTER_X, CENTER_Y, minute_x, minute_y,
                          fill="#00FF00", width=2, tags="hands")

        # Draw second hand
        second_x = CENTER_X + math.cos(second_angle) * (SECOND_HAND_LENGTH - 10)
        second_y = CENTER_Y + math.sin(second_angle) * (SECOND_HAND_LENGTH - 10)
        canvas.create_line(CENTER_X, CENTER_Y, second_x, second_y,
                          fill="#0000FF", width=1, tags="hands")

        # Redraw center circle
        canvas.create_oval(CENTER_X-5, CENTER_Y-5, CENTER_X+5, CENTER_Y+5, fill="#FFFFFF", tags="hands")

    # Initial draw
    draw_clock_hands()

    # Update clock hands every second using non-blocking method
    def update_clock():
        draw_clock_hands()
        root.after(1000, update_clock)  # Schedule next update after 1 second

    # Start the clock
    update_clock()

    # Run the Tkinter main loop
    root.mainloop()

if __name__ == "__main__":
    main()