import os
import re
import time
import shutil
from datetime import datetime
from graphviz import Digraph


def _create_graphviz_diagram(text, filename=None):
    os.makedirs("diagrams", exist_ok=True)
    if filename is None:
        filename = f"diagrams/gv_diagram_{int(time.time() * 1000)}"

    dot = Digraph(format="png")
    dot.attr(rankdir="LR", nodesep="0.8", ranksep="1.0", splines="ortho")

    edges = []
    nodes = set()
    parts = re.split(r'[,\n]', text)
    for p in parts:
        if "->" not in p:
            continue
        a, b = [x.strip() for x in p.split("->", 1)]
        edges.append((a, b))
        nodes.add(a)
        nodes.add(b)

    for n in nodes:
        dot.node(n, n, shape="box", style="rounded,filled", fillcolor="lightblue")
    for a, b in edges:
        dot.edge(a, b)

    return dot.render(filename, cleanup=False)


def diagram(description, ai, output_dir="diagrams"):
    """Generate a graphviz block diagram from a description or edge list."""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("web_images", exist_ok=True)

    if "->" in description:
        chain = description
    else:
        prompt = f"""Convert this concept into a block diagram edge list.

Rules:
- One connection per line
- Format: A -> B
- Multiple inputs allowed
- Feedback loops allowed
- Return ONLY the edge list, nothing else

Concept: {description}
"""
        chain = ai.generate(prompt, use_planning=False).strip()
        if not chain or "->" not in chain:
            return f"Could not generate diagram for: {description}"

    try:
        # Generate the diagram (saves to diagrams folder)
        original_path = _create_graphviz_diagram(chain)

        # The path might be without extension, add .png if needed
        original_png = original_path + ".png" if not original_path.endswith(".png") else original_path

        # Create a SAFE web-friendly filename - REMOVE ALL SPACES AND SPECIAL CHARS
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Remove everything except letters, numbers, and underscores
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', description)[:50]
        web_filename = f"diagram_{safe_name}_{timestamp}.png"
        web_path = os.path.join("web_images", web_filename)

        # Copy to web_images
        if os.path.exists(original_png):
            shutil.copy2(original_png, web_path)
            print(f"[DIAGRAM] ✅ Saved to web: {web_filename}")
            return f"[DIAGRAM:{web_filename}]"
        else:
            # If PNG not found, look for any PNG in diagrams folder
            import glob
            png_files = glob.glob("diagrams/*.png")
            if png_files:
                latest = max(png_files, key=os.path.getctime)
                shutil.copy2(latest, web_path)
                print(f"[DIAGRAM] ✅ Found and copied: {web_filename}")
                return f"[DIAGRAM:{web_filename}]"
            else:
                return f"Diagram error: No PNG file found"

    except Exception as e:
        print(f"[DIAGRAM] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return f"Diagram error: {e}"