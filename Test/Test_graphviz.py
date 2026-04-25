from graphviz import Digraph
import os
from PIL import Image
import tkinter as tk


def test_graphviz():
    os.makedirs("diagrams", exist_ok=True)

    dot = Digraph(format="png")
    dot.attr(rankdir="LR", nodesep="0.8", ranksep="1.0", splines="ortho")

    edges = [
        ("Reference", "Sum"),
        ("Sum", "Controller"),
        ("Controller", "Plant"),
        ("Plant", "Output"),
        ("Output", "Sum"),
    ]

    nodes = set()
    for a, b in edges:
        nodes.add(a)
        nodes.add(b)

    for n in nodes:
        dot.node(n, n, shape="box", style="rounded,filled", fillcolor="lightblue")

    for a, b in edges:
        dot.edge(a, b)

    path = dot.render("diagrams/test_diagram", cleanup=False)
    print(f"Rendered to: {path}")
    print(f"File exists: {os.path.exists(path)}")

    # Show it
    img = Image.open(path)
    print(f"Image size: {img.size}")
    img.show()


if __name__ == "__main__":
    test_graphviz()