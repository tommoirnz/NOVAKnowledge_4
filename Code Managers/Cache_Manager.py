# cache_manager.py - WITH .ENV SUPPORT
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import json
import os
import datetime
import time
import httpx
from dataclasses import dataclass
from typing import Optional, List
from dotenv import load_dotenv


#Use this to add to cache occasional undocumented errors.
#You need a Brave api key.


# Load .env file
load_dotenv()
# TEST: Print to verify it loaded
brave_key = os.getenv("BRAVE_KEY")
if brave_key:
    print(f"✅ BRAVE_KEY loaded: {brave_key[:10]}...{brave_key[-5:]}")  # Show first 10 and last 5 chars
else:
    print("❌ BRAVE_KEY not found in .env!")

###################

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    pubdate: Optional[str] = None


class CacheManagerApp:
    def __init__(self, root):
        self.root = root
        root.title("Error Cache Manager with Search")
        root.geometry("1200x750")

        # Search rate limiting
        self._last_brave_search_time = 0
        self._min_brave_search_interval = 1.5

        # Load config
        self.load_config()

        # Create UI
        self.create_ui()

        # Load cache
        self.load_cache()
        self.refresh_cache_list()

    def load_config(self):
        """Load cache configuration"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
            with open(config_path, "r") as f:
                cfg = json.load(f)

            self.cache_dir = cfg["cache_directory"]
            self.cache_file = os.path.join(
                self.cache_dir,
                cfg["error_cache_file"]
            )

            print(f"[CONFIG] Cache file: {self.cache_file}")


        except Exception as e:
            messagebox.showerror("Config Error", f"Failed to load config.json: {e}")
            self.cache_dir = "."
            self.cache_file = "error_search_cache.json"

    def load_cache(self):
        """Load existing cache from disk"""
        if not os.path.exists(self.cache_file):
            self.cache = {}
            print(f"[CACHE] Cache file doesn't exist, starting fresh")
            return

        try:
            with open(self.cache_file, "r", encoding='utf-8') as f:
                self.cache = json.load(f)
            print(f"[CACHE] Loaded {len(self.cache)} entries")
        except Exception as e:
            messagebox.showerror("Cache Error", f"Failed to load cache: {e}")
            self.cache = {}

    def save_cache(self):
        """Save cache to disk"""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)

            with open(self.cache_file, "w", encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2)

            print(f"[CACHE] Saved {len(self.cache)} entries")
            messagebox.showinfo("Success", f"Cache saved! ({len(self.cache)} entries)")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save cache: {e}")

    def brave_search(self, query: str, count: int = 6) -> List[SearchResult]:
        """Search using Brave API"""
        # Strip quotes
        query = query.strip('"').strip("'")
        print(f"\n🔍 brave_search: '{query}'")

        # Rate limit check
        now = time.time()
        elapsed = now - self._last_brave_search_time
        if elapsed < self._min_brave_search_interval:
            wait_time = self._min_brave_search_interval - elapsed
            print(f"[SEARCH] ⏳ Rate limiting: waiting {wait_time:.1f}s")
            time.sleep(wait_time)

        brave_key = os.getenv("BRAVE_KEY")
        if not brave_key:
            raise RuntimeError("No BRAVE_KEY environment variable found!\n\nSet it with: set BRAVE_KEY=your_api_key")

        endpoint = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "X-Subscription-Token": brave_key,
            "User-Agent": "CacheManager/1.0"
        }
        params = {"q": query, "count": count}

        try:
            with httpx.Client(timeout=25.0, headers=headers) as client:
                r = client.get(endpoint, params=params)
                r.raise_for_status()
                data = r.json()

            # Update last search time
            self._last_brave_search_time = time.time()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                print(f"[SEARCH] 🚫 Rate limit hit (429)")
                time.sleep(5.0)
                self._last_brave_search_time = time.time()
                raise RuntimeError("Brave API rate limit hit. Wait a few seconds.")
            else:
                raise RuntimeError(f"Brave API error: {e}")

        # Extract results
        out = []
        web_results = data.get("web", {}).get("results", [])

        for w in web_results:
            out.append(SearchResult(
                title=w.get('title', ''),
                url=w.get('url', ''),
                snippet=w.get('description', w.get('snippet', '')),
                pubdate=w.get('publication_date', w.get('date', None))
            ))

        print(f"[BRAVE] ✅ Found {len(out)} results")
        return out

    def search_and_populate(self):
        """Search for error solution and populate results field"""
        error_type = self.error_type_var.get().strip()
        library = self.library_var.get().strip()

        if not error_type or not library:
            messagebox.showwarning("Missing Info", "Please set Error Type and Library first")
            return

        # Build search query
        search_query = f"Python {library} {error_type} fix example code"

        # Update status
        self.search_status_label.config(text="🔍 Searching...", fg="blue")
        self.root.update()

        try:
            results = self.brave_search(search_query, count=5)

            if not results:
                self.search_status_label.config(text="❌ No results found", fg="red")
                messagebox.showinfo("No Results", f"No results found for: {search_query}")
                return

            # Format results for cache
            formatted = f"Search results for: {search_query}\n\n"

            for i, result in enumerate(results, 1):
                formatted += f"## Result {i}: {result.title}\n"
                formatted += f"URL: {result.url}\n"
                if result.snippet:
                    formatted += f"Summary: {result.snippet}\n"
                formatted += "\n"

            # Populate results field
            self.results_text.delete("1.0", tk.END)
            self.results_text.insert("1.0", formatted)

            # Update query field
            self.query_entry.delete(0, tk.END)
            self.query_entry.insert(0, search_query)

            self.search_status_label.config(
                text=f"✅ Found {len(results)} results",
                fg="green"
            )

            messagebox.showinfo(
                "Search Complete",
                f"Found {len(results)} results.\n\nNow:\n1. Review and edit the results\n2. Add your own fixes/examples\n3. Click 'Add to Cache'"
            )

        except Exception as e:
            self.search_status_label.config(text="❌ Search failed", fg="red")
            messagebox.showerror("Search Error", str(e))

    def create_ui(self):
        """Create the user interface"""

        # Main container
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ===== LEFT PANEL: Form =====
        left_frame = tk.LabelFrame(main_frame, text="Add New Cache Entry", font=("Arial", 11, "bold"))
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Error Type
        tk.Label(left_frame, text="Error Type:", font=("Arial", 10)).pack(anchor=tk.W, padx=10, pady=(10, 0))

        self.error_type_var = tk.StringVar(value="modulenotfounderror")
        error_types = [
            "modulenotfounderror", "attributeerror", "typeerror", "valueerror",
            "importerror", "keyerror", "indexerror", "nameerror",
            "syntaxerror", "indentationerror", "unboundlocalerror", "runtimeerror",
            "zerodivisionerror", "filenotfounderror", "oserror", "ioerror",
            "permissionerror", "timeouterror", "connectionerror",
            "unicodeerror", "unicodeencodeerror", "unicodedecodeerror",  # ← All Unicode errors
            "recursionerror", "memoryerror", "assertionerror",
            "_ufuncoutputcastingerror", "argumenterror", "portaudioerror"
        ]
        error_combo = ttk.Combobox(left_frame, textvariable=self.error_type_var, values=error_types, state="normal")
        error_combo.pack(fill=tk.X, padx=10, pady=5)

        # Library
        tk.Label(left_frame, text="Library:", font=("Arial", 10)).pack(anchor=tk.W, padx=10, pady=(10, 0))

        self.library_var = tk.StringVar(value="scipy")
        self.library_var = tk.StringVar(value="scipy")
        libraries = [
            'python',
            'control', 'matplotlib', 'numpy', 'scipy', 'pandas', 'sympy',
            'tensorflow', 'torch', 'sklearn', 'keras', 'transformers', 'opencv-python',
            'flask', 'django', 'fastapi', 'requests', 'beautifulsoup4', 'selenium',
            'polars', 'dask', 'seaborn', 'plotly', 'statsmodels',
            'slycot', 'scipy.signal',
            'tkinter', 'pygame', 'pyqt5', 'kivy', 'pyside6',
            'cv2', 'pillow', 'scikit-image', 'albumentations',
            'pydub', 'librosa', 'soundfile', 'pyaudio', 'wave', 'sounddevice',  # ← Added sounddevice
            'pyopengl', 'moderngl', 'vispy', 'pyvista', 'trimesh', 'ffmpeg', 'bode',
            'winsound',
            'os', 'sys', 'pathlib', 'json', 'csv'
        ]

        lib_combo = ttk.Combobox(left_frame, textvariable=self.library_var, values=sorted(libraries), state="normal")
        lib_combo.pack(fill=tk.X, padx=10, pady=5)

        # Search button
        search_frame = tk.Frame(left_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(
            search_frame,
            text="🔍 Search for Solution",
            command=self.search_and_populate,
            bg="#9b59b6",
            fg="white",
            font=("Arial", 10, "bold"),
            width=20
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.search_status_label = tk.Label(
            search_frame,
            text="",
            font=("Arial", 9)
        )
        self.search_status_label.pack(side=tk.LEFT)

        # Query
        tk.Label(left_frame, text="Query:", font=("Arial", 10)).pack(anchor=tk.W, padx=10, pady=(10, 0))

        self.query_entry = tk.Entry(left_frame)
        self.query_entry.pack(fill=tk.X, padx=10, pady=5)
        self.query_entry.insert(0, "python library API reference import documentation")

        # Results (large text area)
        tk.Label(left_frame, text="Results (documentation/fix):", font=("Arial", 10)).pack(anchor=tk.W, padx=10,
                                                                                           pady=(10, 0))

        self.results_text = scrolledtext.ScrolledText(left_frame, height=15, wrap=tk.WORD)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Buttons
        button_frame = tk.Frame(left_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(
            button_frame,
            text="➕ Add to Cache",
            command=self.add_entry,
            bg="#27AE60",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="💾 Save Cache",
            command=self.save_cache,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="🗑️ Clear Form",
            command=self.clear_form,
            width=12
        ).pack(side=tk.LEFT, padx=5)

        # ===== RIGHT PANEL: Cache List =====
        right_frame = tk.LabelFrame(main_frame, text="Current Cache Entries", font=("Arial", 11, "bold"))
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Search
        search_frame = tk.Frame(right_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.refresh_cache_list())

        search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Cache list
        self.cache_listbox = tk.Listbox(right_frame, font=("Courier", 9))
        self.cache_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.cache_listbox.bind("<Double-Button-1>", self.load_entry_to_form)

        scrollbar = tk.Scrollbar(self.cache_listbox)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cache_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.cache_listbox.yview)

        # Info label
        self.info_label = tk.Label(right_frame, text="", font=("Arial", 9), fg="#7f8c8d")
        self.info_label.pack(pady=(0, 10))

        # Delete button
        tk.Button(
            right_frame,
            text="🗑️ Delete Selected",
            command=self.delete_entry,
            bg="#e74c3c",
            fg="white",
            width=20
        ).pack(pady=(0, 10))

    def refresh_cache_list(self):
        """Refresh the cache list display"""
        self.cache_listbox.delete(0, tk.END)

        search_term = self.search_var.get().lower()

        matching_keys = []
        for key in sorted(self.cache.keys()):
            if search_term in key.lower():
                matching_keys.append(key)

        for key in matching_keys:
            entry = self.cache[key]
            result_len = entry.get("result_length", len(entry.get("results", "")))
            self.cache_listbox.insert(tk.END, f"{key} ({result_len} chars)")

        self.info_label.config(text=f"Showing {len(matching_keys)} of {len(self.cache)} entries")

    def add_entry(self):
        """Add new entry to cache"""
        error_type = self.error_type_var.get().strip().lower()
        library = self.library_var.get().strip().lower()
        query = self.query_entry.get().strip()
        results = self.results_text.get("1.0", tk.END).strip()

        if not error_type or not library:
            messagebox.showwarning("Missing Data", "Please provide error type and library")
            return

        if not results:
            messagebox.showwarning("Missing Data", "Please provide results/documentation")
            return

        # Build cache key
        cache_key = f"{error_type}::{library}"

        # Build full query
        full_query = f"{library} {query}" if query else library

        # Create entry
        entry = {
            "error_type": error_type,
            "query": full_query,
            "results": results if results.startswith(
                "Search results for:") else f"Search results for: {full_query}\n\n{results}",
            "timestamp": datetime.datetime.now().isoformat(),
            "result_length": len(results)
        }

        # Check if exists
        if cache_key in self.cache:
            if not messagebox.askyesno("Overwrite?", f"Entry '{cache_key}' already exists. Overwrite?"):
                return

        # Add to cache
        self.cache[cache_key] = entry

        print(f"[CACHE] Added: {cache_key}")
        messagebox.showinfo("Success", f"Added: {cache_key}\n\nDon't forget to click 'Save Cache'!")

        # Refresh list
        self.refresh_cache_list()

        # Clear form
        self.clear_form()

    def clear_form(self):
        """Clear the input form"""
        self.results_text.delete("1.0", tk.END)
        self.query_entry.delete(0, tk.END)
        self.query_entry.insert(0, "python library API reference import documentation")
        self.search_status_label.config(text="")

    def load_entry_to_form(self, event=None):
        """Load selected entry into form for editing"""
        selection = self.cache_listbox.curselection()
        if not selection:
            return

        # Get selected key
        item_text = self.cache_listbox.get(selection[0])
        cache_key = item_text.split(" (")[0]

        if cache_key not in self.cache:
            return

        entry = self.cache[cache_key]

        # Parse key
        parts = cache_key.split("::")
        if len(parts) == 2:
            error_type, library = parts
            self.error_type_var.set(error_type)
            self.library_var.set(library)

        # Load query
        query = entry.get("query", "")
        self.query_entry.delete(0, tk.END)
        self.query_entry.insert(0, query)

        # Load results (strip the "Search results for:" prefix)
        results = entry.get("results", "")
        if results.startswith("Search results for:"):
            lines = results.split("\n")
            results = "\n".join(lines[2:])

        self.results_text.delete("1.0", tk.END)
        self.results_text.insert("1.0", results)

        print(f"[CACHE] Loaded: {cache_key}")

    def delete_entry(self):
        """Delete selected cache entry"""
        selection = self.cache_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an entry to delete")
            return

        item_text = self.cache_listbox.get(selection[0])
        cache_key = item_text.split(" (")[0]

        if cache_key not in self.cache:
            return

        if messagebox.askyesno("Delete?", f"Delete '{cache_key}'?"):
            del self.cache[cache_key]
            print(f"[CACHE] Deleted: {cache_key}")
            self.refresh_cache_list()
            messagebox.showinfo("Deleted", f"Deleted: {cache_key}")


if __name__ == "__main__":
    root = tk.Tk()
    app = CacheManagerApp(root)
    root.mainloop()