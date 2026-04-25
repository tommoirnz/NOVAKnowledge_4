import tkinter as tk
from tkinter import messagebox
import os
import threading
import time
import random
from PIL import Image, ImageTk

class FlashingLightEffect:
    def __init__(self, master):
        self.master = master
        self.flash_state = True  # True for "on", False for "off"
        self.canvas = tk.Canvas(master, width=500, height=500, bg="black")
        self.canvas.pack(pady=20)
        self.image_label = None
        self.bg_thread = threading.Thread(target=self.flash_background, daemon=True)
        self.bg_thread.start()

        # Close button
        self.close_button = tk.Button(master, text="Close", command=master.destroy)
        self.close_button.pack(side=tk.BOTTOM, pady=10)

    def flash_background(self):
        while True:
            time.sleep(0.3)  # Flash interval
            if self.flash_state:
                self.canvas.config(bg=random.choice(["#00ff00", "#0000ff", "#ffff00"]))
            else:
                self.canvas.config(bg="black")
            self.flash_state = not self.flash_state

    def load_and_display_image(self, image_path):
        try:
            # Load image with fallback to PIL if not found
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"File not found: {image_path}")

            # Load and resize image
            img = Image.open(image_path)
            img = img.resize((400, 400), Image.LANCZOS)  # Resize to fit canvas

            # Convert to Tkinter PhotoImage
            self.photo_img = ImageTk.PhotoImage(img)

            # Create image label with flash effect
            self.image_label = tk.Label(self.canvas, image=self.photo_img)
            self.image_label.image = self.photo_img  # Keep reference
            self.image_label.place(x=50, y=50)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
            self.master.destroy()

def main():
    root = tk.Tk()
    root.title("Horse with Flashing Lights")
    root.geometry("600x600")

    # Define path to horse.png
    image_path = r"C:\Users\OEM\Desktop\horse.png"

    # Check if file exists, if not ask user to browse
    if not os.path.exists(image_path):
        from tkinter.filedialog import askopenfilename
        image_path = askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if not image_path:
            messagebox.showerror("Error", "No image selected. Exiting.")
            return

    # Create flashing light effect window
    app = FlashingLightEffect(root)
    app.load_and_display_image(image_path)

    # Run the application
    root.mainloop()

if __name__ == "__main__":
    main()