import tkinter as tk
from tkinter import font
import datetime

class DigitalClock:
    def __init__(self, root):
        self.root = root
        self.root.title("Digital Clock & Date")
        self.root.geometry("400x250")
        self.root.resizable(False, False)
        self.root.configure(bg='#2E2E4A')

        # Main clock display
        self.time_label = tk.Label(
            root,
            font=('Arial', 50, 'bold'),
            bg='#2E2E4A',
            fg='white'
        )
        self.time_label.pack(pady=10)

        # Date display
        self.date_label = tk.Label(
            root,
            font=('Arial', 20),
            bg='#2E2E4A',
            fg='white'
        )
        self.date_label.pack(pady=5)

        # Day display
        self.day_label = tk.Label(
            root,
            font=('Arial', 20),
            bg='#2E2E4A',
            fg='#FFD700'
        )
        self.day_label.pack(pady=5)

        # Update time and date immediately
        self.update_time()

        # Schedule continuous updates
        self.root.after(1000, self.update_time)

    def update_time(self):
        now = datetime.datetime.now()

        # Format time (12-hour with AM/PM)
        current_time = now.strftime("%I:%M:%S %p")

        # Format date (Month Day, Year)
        current_date = now.strftime("%B %d, %Y")

        # Format day of week
        current_day = now.strftime("%A")

        # Update all labels
        self.time_label.config(text=current_time)
        self.date_label.config(text=current_date)
        self.day_label.config(text=current_day)

        # Schedule next update
        self.root.after(1000, self.update_time)

if __name__ == "__main__":
    root = tk.Tk()
    app = DigitalClock(root)
    root.mainloop()