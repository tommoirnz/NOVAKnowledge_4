import tkinter as tk
from tkinter import ttk
import random

class PrototypeFeedbackGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Prototype Feedback - Task Completion Test")
        self.root.geometry("500x400")

        # --- UI Setup (Mock Incomplete Prototype) ---
        self.setup_prototype_mock()

        # --- Feedback Form ---
        self.setup_feedback_form()

    def setup_prototype_mock(self):
        """Simulates an incomplete prototype (e.g., a UI with missing features)."""
        self.label = tk.Label(
            self.root,
            text="Incomplete Prototype: Check Task Completion",
            font=("Arial", 14, "bold")
        )
        self.label.pack(pady=10)

        # Mock "incomplete" prototype UI (e.g., a form with missing fields)
        self.incomplete_prototype_frame = ttk.Frame(self.root)
        self.incomplete_prototype_frame.pack(pady=10)

        # Example: Incomplete input field (missing validation)
        ttk.Label(self.incomplete_prototype_frame, text="Enter Email:").grid(row=0, column=0, padx=10)
        self.email_entry = ttk.Entry(self.incomplete_prototype_frame, width=20)
        self.email_entry.grid(row=0, column=1, padx=10, pady=5)

        # Example: Missing confirmation button (simulated)
        ttk.Button(
            self.incomplete_prototype_frame,
            text="Submit",
            command=self.simulate_task_completion
        ).grid(row=1, column=0, columnspan=2, pady=10)

    def simulate_task_completion(self):
        """Simulates a user attempting a task (e.g., filling out a form)."""
        alert = tk.Toplevel(self.root)
        alert.title("Task Completion Alert")
        alert.geometry("300x100")

        if random.random() < 0.3:
            task_result = "❌ Incomplete: Missing email validation."
        else:
            task_result = "✅ Task Successful: Email submitted!"

        ttk.Label(alert, text=task_result, font=("Arial", 12)).pack(pady=20)

    def setup_feedback_form(self):
        """Feedback form inspired by search results (actionable feedback)."""
        ttk.Label(self.root, text="Rate Your Experience:", font=("Arial", 12)).pack(pady=10)

        # --- Usability Scale (1-5) ---
        ttk.Label(self.root, text="How easy was this task?").pack(pady=5)
        self.feedback_scale = ttk.Scale(
            self.root, from_=1, to=5, orient="horizontal"
        )
        self.feedback_scale.pack(pady=5)

        # --- Open-ended feedback ---
        ttk.Label(self.root, text="What was missing?").pack(pady=5)
        self.feedback_text = tk.Text(self.root, height=4, width=40)
        self.feedback_text.pack(pady=5)

        # --- Submit Button ---
        ttk.Button(
            self.root,
            text="Submit Feedback",
            command=self.process_feedback
        ).pack(pady=10)

    def process_feedback(self):
        """Capture and display feedback (simulated)."""
        feedback = {
            "usability_score": self.feedback_scale.get(),
            "comments": self.feedback_text.get("1.0", "end-1c")
        }
        print(f"Feedback Received: {feedback}")

        # --- Pop-up confirmation ---
        alert = tk.Toplevel(self.root)
        alert.title("Feedback Submitted")
        ttk.Label(alert, text="Thank you for your feedback!", font=("Arial", 12)).pack(pady=20)

if __name__ == "__main__":
    root = tk.Tk()
    app = PrototypeFeedbackGUI(root)
    root.mainloop()