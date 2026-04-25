import os
import importlib
import inspect


class ToolRegistry:

    def __init__(self, tool_dir="tools"):

        self.tool_dir = tool_dir
        self.tools = {}

        self.load_tools()

    def load_tools(self):

        for file in os.listdir(self.tool_dir):

            if not file.endswith(".py"):
                continue

            if file.startswith("_") or file == "tool_registry.py":
                continue

            module_name = f"{self.tool_dir}.{file[:-3]}"

            try:

                module = importlib.import_module(module_name)

                # reload module so changes appear without restart
                importlib.reload(module)

                for name, obj in inspect.getmembers(module, inspect.isfunction):
                    if obj.__module__ == module.__name__ and not name.startswith("_"):
                        self.tools[name] = obj

            except Exception as e:

                print(f"[TOOLS] Failed loading {module_name}: {e}")

        print(f"[TOOLS] Loaded: {list(self.tools.keys())}")

    def list_tools(self):

        return list(self.tools.keys())

    def audit(self) -> dict:
        """Check all registered tools are callable and report status."""
        results = {}
        for name, func in self.tools.items():
            try:
                if not callable(func):
                    results[name] = "⚠️ Not callable"
                else:
                    sig = inspect.signature(func)
                    results[name] = f"✅ OK — {len(sig.parameters)} param(s)"
            except Exception as e:
                results[name] = f"❌ {e}"
        return results

    def run(self, name, *args, **kwargs):

        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")

        print(f"[TOOLS] Running → {name}")

        import inspect

        func = self.tools[name]

        print("[DEBUG] Function:", func)
        print("[DEBUG] Signature:", inspect.signature(func))

        return func(*args, **kwargs)