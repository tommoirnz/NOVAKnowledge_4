import tkinter as tk
from datetime import datetime

def tekken_style_label(parent_frame, text, row, col, font_size=12):
    label = tk.Label(
        parent_frame,
        text=text,
        font=('Arial', font_size, 'bold'),
        bg='black',  # Tekken style dark background
        fg='white',  # White text
        padx=10,
        pady=10,
        wraplength=300
    )
    label.grid(row=row, column=col, sticky="nsew")
    return label

def update_time():
    now = datetime.now().strftime("%H:%M:%S")
    time_label.config(text=now)
    root.after(1000, update_time)  # Update every second

# Create main window
root = tk.Tk()
root.title("Tekken-Style Clock")
root.configure(bg='black')
root.geometry("500x300")

# Create main container frame
main_frame = tk.Frame(root, bg='black')
main_frame.pack(fill=tk.BOTH, expand=True)

# Create time display frame
time_frame = tk.Frame(main_frame, bg='black', padx=20, pady=20)
time_frame.pack(pady=20)

# Create date display frame
date_frame = tk.Frame(main_frame, bg='black', padx=20, pady=20)
date_frame.pack(pady=20)

# Create a title frame
title_frame = tk.Frame(main_frame, bg='black')
title_frame.pack(pady=10)

# Create title label
title_label = tekken_style_label(title_frame, "TEKKEN STYLE CLOCK", 0, 0, 20)

# Create time label with tekken style
time_str = "00:00:00"
time_label = tekken_style_label(time_frame, time_str, 0, 0, font_size=48)

# Create date label
now = datetime.now().strftime("%A, %B %d, %Y")
date_label = tekken_style_label(date_frame, now, 0, 0, font_size=16)

# Initialize time update
update_time()

# Run the application
root.mainloop()