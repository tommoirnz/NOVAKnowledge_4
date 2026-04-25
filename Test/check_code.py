import os
import sys
import py_compile
import traceback
import tkinter as tk
from tkinter import filedialog, scrolledtext
# Checks for syntax errors and indentation only, basic test
class ProjectCheckerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Project Checker")
        self.root.geometry("700x500")

        self.path = tk.StringVar()

        # Top frame
        top_frame = tk.Frame(root)
        top_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(top_frame, text="Selected Path:").pack(anchor="w")

        entry = tk.Entry(top_frame, textvariable=self.path, width=80)
        entry.pack(side="left", padx=5, pady=5)

        tk.Button(top_frame, text="Browse File", command=self.browse_file).pack(side="left", padx=5)
        tk.Button(top_frame, text="Browse Folder", command=self.browse_folder).pack(side="left", padx=5)

        # Run button
        tk.Button(root, text="Run Check", command=self.run_check, bg="green", fg="white").pack(pady=5)

        # Output console
        self.output = scrolledtext.ScrolledText(root, wrap=tk.WORD)
        self.output.pack(fill="both", expand=True, padx=10, pady=10)

    def log(self, text):
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)
        self.root.update()

    def browse_file(self):
        file = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        if file:
            self.path.set(file)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path.set(folder)

    def compile_check(self, target):
        self.log("\n[1] Syntax check")
        errors = 0

        if os.path.isfile(target):
            files = [target]
        else:
            files = []
            for root, _, fs in os.walk(target):
                for f in fs:
                    if f.endswith(".py"):
                        files.append(os.path.join(root, f))

        for path in files:
            try:
                py_compile.compile(path, doraise=True)
            except Exception as e:
                self.log(f"❌ Syntax error in {path}")
                self.log(str(e))
                errors += 1

        if errors == 0:
            self.log("✅ Syntax OK")

        return errors, files

    def import_check(self, files, base_path):
        self.log("\n[2] Import check")
        errors = 0

        sys.path.insert(0, os.path.abspath(base_path))

        for path in files:
            rel = os.path.relpath(path, base_path)
            module_name = rel.replace(os.sep, ".")[:-3]

            try:
                __import__(module_name)
            except Exception:
                self.log(f"❌ Import failed: {module_name}")
                self.log(traceback.format_exc(limit=1))
                errors += 1

        if errors == 0:
            self.log("✅ Imports OK")

        return errors

    def run_check(self):
        self.output.delete(1.0, tk.END)

        target = self.path.get()
        if not target:
            self.log("⚠️ Please select a file or folder")
            return

        self.log("=== Running Checks ===")

        base_path = target if os.path.isdir(target) else os.path.dirname(target)

        syntax_errors, files = self.compile_check(target)
        import_errors = self.import_check(files, base_path)

        if syntax_errors == 0 and import_errors == 0:
            self.log("\n🎉 All checks passed!")
        else:
            self.log("\n⚠️ Issues detected")


if __name__ == "__main__":
    root = tk.Tk()
    app = ProjectCheckerGUI(root)
    root.mainloop()