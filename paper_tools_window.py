import tkinter as tk
from tkinter import simpledialog
import threading


class PaperToolsWindow(tk.Toplevel):

    def __init__(self, root, ai, get_paper_text, log_fn, send_code_fn, chime_fn):
        super().__init__(root)
        self.send_code = send_code_fn
        self.algorithms_text = None
        self.examples_list = []
        self.algorithms_list = []
        self._play_chime = chime_fn
        self.ai = ai
        self.get_paper_text = get_paper_text
        self.log = log_fn

        self.title("Paper Tools")
        self.geometry("500x450")
        self.configure(bg="#0F1318")

        self._build_ui()


    # 🔔 double chime for completion
    def _chime_done(self):
        self._play_chime(1200, 120)
        self.after(180, lambda: self._play_chime(1400, 120))


    def _build_ui(self):

        tk.Label(
            self,
            text="Paper Tools",
            font=("Rajdhani", 16, "bold"),
            fg="#4A9EFF",
            bg="#0F1318"
        ).pack(pady=10)


        btn_frame = tk.Frame(self, bg="#0F1318")
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="Summarise Paper",
            width=25,
            command=self.summarise_paper
        ).pack(pady=5)

        tk.Button(
            btn_frame,
            text="Extract Algorithms",
            width=25,
            command=self.extract_algorithms
        ).pack(pady=5)

        tk.Button(
            btn_frame,
            text="Run Example",
            width=25,
            command=self.run_example
        ).pack(pady=5)

        tk.Button(
            btn_frame,
            text="Implement Algorithm",
            width=25,
            command=self.implement_algorithm
        ).pack(pady=5)

        tk.Button(
            btn_frame,
            text="Extract Worked Examples",
            width=25,
            command=self.extract_examples
        ).pack(pady=5)

        tk.Label(
            self,
            text="Custom Request",
            fg="#4A9EFF",
            bg="#0F1318"
        ).pack()

        self.custom_entry = tk.Entry(self)
        self.custom_entry.pack(fill="x", padx=10, pady=5)

        tk.Button(
            self,
            text="Run Custom Request",
            command=self.run_custom_request
        ).pack(pady=5)

        self.item_list = tk.Listbox(
            self,
            bg="#0C1219",
            fg="#C8D6E5",
            height=6
        )

        self.item_list.pack(fill="x", padx=10, pady=5)

        self.output = tk.Text(
            self,
            bg="#0C1219",
            fg="#C8D6E5",
            wrap="word"
        )

        self.output.pack(fill="both", expand=True, padx=10, pady=10)


    # --------------------------------------------------------
    # SUMMARISE PAPER
    # --------------------------------------------------------
    def run_custom_request(self):

        command = self.custom_entry.get().strip()

        if not command:
            return

        text = self.get_paper_text()

        if not text:
            self.output.delete("1.0", "end")
            self.output.insert("1.0", "No document loaded.")
            return

        # START CHIME
        self._play_chime()

        prompt = f"""
    You are analysing a scientific paper.

    Locate the relevant section in the paper before answering.

    User request:
    {command}

    Paper text:
    {text[:12000]}

    If the request asks for code, return runnable code only.
    Otherwise return a clear explanation.
    """

        def worker():

            result = self.ai.generate(prompt, use_planning=False)

            if not result:
                result = "AI returned no result."

            # detect code blocks
            if "```" in result:

                import re
                code_blocks = re.findall(r"```[a-zA-Z]*\n(.*?)```", result, re.S)

                if code_blocks:
                    code = code_blocks[0].strip()

                    # send to code window
                    self.send_code(code)

                    self.output.delete("1.0", "end")
                    self.output.insert("1.0", "Code sent to AutoCoder window.")

            else:
                self.output.delete("1.0", "end")
                self.output.insert("1.0", result)

            # FINISH CHIME (two beeps)
            self._play_chime()
            self._play_chime()

        threading.Thread(target=worker, daemon=True).start()



    def summarise_paper(self):

        text = self.get_paper_text()

        if not text:
            self.output.delete("1.0", "end")
            self.output.insert("1.0", "No document loaded.")
            return

        prompt = f"""
Summarise the following technical document.

Provide a structured summary with:

Title
Authors
Main topic
Key ideas
Important algorithms or methods
Conclusion

TEXT:
{text[:12000]}
"""

        def worker():

            summary = self.ai.generate(prompt, use_planning=False)

            if not summary:
                summary = "Unable to summarise document."

            self.output.delete("1.0", "end")
            self.output.insert("1.0", summary)

            self._chime_done()

        self._play_chime()
        threading.Thread(target=worker, daemon=True).start()


    # --------------------------------------------------------
    # EXTRACT ALGORITHMS
    # --------------------------------------------------------

    def extract_algorithms(self):

        text = self.get_paper_text()

        if not text:
            self.log("[PAPER] No paper loaded")
            return

        prompt = f"""
You are analysing technical lecture notes or a scientific paper.

Identify any computational procedures or algorithms described in the text.

Return them in this format:

Algorithm 1:
Name:
Description:
Steps:

Algorithm 2:
Name:
Description:
Steps:

TEXT:
{text[:12000]}
"""

        def worker():

            result = self.ai.generate(prompt, use_planning=False)

            import re

            self.item_list.delete(0, tk.END)

            self.algorithms_list = re.findall(r"Algorithm\s*\d+", result)

            for alg in self.algorithms_list:
                self.item_list.insert(tk.END, alg)

            self.algorithms_text = result

            self.output.delete("1.0", "end")
            self.output.insert("1.0", result)

            self._chime_done()

        self._play_chime()
        threading.Thread(target=worker, daemon=True).start()


    # --------------------------------------------------------
    # RUN EXAMPLE
    # --------------------------------------------------------

    def run_example(self):

        import re

        selection = self.item_list.curselection()

        if not selection:
            self.output.delete("1.0", "end")
            self.output.insert("1.0", "Select an example from the list first.")
            return

        example_label = self.item_list.get(selection[0])

        if not example_label.lower().startswith("example"):
            self.output.delete("1.0", "end")
            self.output.insert("1.0", "Select an example, not an algorithm.")
            return

        example_num = re.findall(r"\d+", example_label)[0]

        text = self.get_paper_text()

        if not text:
            self.output.delete("1.0", "end")
            self.output.insert("1.0", "No document loaded.")
            return

        pattern = r"(Example\s*" + str(example_num) + r"[:\.\-\s].*?)(?:Example\s*\d+|\Z)"
        match = re.search(pattern, text, re.S | re.I)

        if match:
            example_text = match.group(1)
        else:
            example_text = text[:12000]

        prompt = f"""
From the following text reproduce Example {example_num}.

Write Python code that reproduces this example numerically.

Return runnable Python code only.

TEXT:
{example_text}
"""

        def worker():

            code = self.ai.generate(prompt, use_planning=False)

            if not code:
                code = "Unable to generate code for this example."

            self.send_code(code)

            self.output.delete("1.0", "end")
            self.output.insert("1.0", f"Example {example_num} sent to AutoCoder.")

            self._chime_done()

        self._play_chime()
        threading.Thread(target=worker, daemon=True).start()


    # --------------------------------------------------------
    # EXTRACT EXAMPLES
    # --------------------------------------------------------

    def extract_examples(self):

        text = self.get_paper_text()

        if not text:
            self.log("[PAPER] No paper loaded")
            return

        prompt = f"""
From the following technical text, identify any worked examples.

Return them as:

Example 1:
Title:
Problem:
Method:
Solution steps:

Example 2:
Title:
Problem:
Method:
Solution steps:

TEXT:
{text[:12000]}
"""

        def worker():

            result = self.ai.generate(prompt, use_planning=False)

            import re

            self.examples_list = re.findall(r"Example\s*\d+", result)

            self.item_list.delete(0, tk.END)

            for ex in self.examples_list:
                self.item_list.insert(tk.END, ex)

            self.output.delete("1.0", "end")
            self.output.insert("1.0", result)

            self._chime_done()

        self._play_chime()
        threading.Thread(target=worker, daemon=True).start()


    # --------------------------------------------------------
    # IMPLEMENT ALGORITHM
    # --------------------------------------------------------

    def implement_algorithm(self):

        if self.algorithms_text is None:
            self.output.delete("1.0", "end")
            self.output.insert("1.0", "Please run 'Extract Algorithms' first.")
            return

        selection = self.item_list.curselection()

        if selection:
            label = self.item_list.get(selection[0])

            if not label.lower().startswith("algorithm"):
                self.output.delete("1.0", "end")
                self.output.insert("1.0", "Select an algorithm, not an example.")
                return

            import re
            alg = re.findall(r"\d+", label)[0]

        else:
            alg = simpledialog.askstring(
                "Algorithm",
                "Enter algorithm number (example: 1)"
            )

        if not alg:
            return

        prompt = f"""
You are analysing a scientific paper.

The following algorithms were extracted from the paper:

{self.algorithms_text}

Implement Algorithm {alg} as runnable Python code.

Include:
- clear functions
- comments explaining the algorithm
- a small usage example
"""

        def worker():

            code = self.ai.generate(prompt, use_planning=False)

            self.send_code(code)

            self.output.delete("1.0", "end")
            self.output.insert("1.0", "Code sent to AutoCoder window.")

            self._chime_done()

        self._play_chime()
        threading.Thread(target=worker, daemon=True).start()