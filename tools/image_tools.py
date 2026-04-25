import matplotlib

matplotlib.use("Agg")  # ← no GUI backend, never touches tkinter

import requests
import os
import re
import math
import shutil
from datetime import datetime
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt


def search_and_show_image(query, internet_tools, image_dir):
    print("[IMAGE] search_and_show_image started")

    match = re.search(r"\b(\d+)\b", query)
    count = int(match.group(1)) if match else 4
    count = min(count, 10)

    query = re.sub(r"\b\d+\b", "", query)
    query = query.replace("pictures", "").replace("images", "").strip()

    print("[IMAGE] Searching:", query)

    urls = internet_tools._brave_image_search(query, count=count * 3)

    if not urls:
        return "No images found"

    # Create both directories
    os.makedirs(image_dir, exist_ok=True)
    web_dir = "web_images"
    os.makedirs(web_dir, exist_ok=True)

    images = []
    saved_paths = []
    headers = {"User-Agent": "Mozilla/5.0"}
    safe_query = re.sub(r"[^\w]", "_", query)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, url in enumerate(urls):
        try:
            print("[IMAGE] Download:", url)
            r = requests.get(url, headers=headers, timeout=10)
            if "image" not in r.headers.get("content-type", ""):
                continue
            img = Image.open(BytesIO(r.content)).convert("RGB")

            # Save to original directory
            path = os.path.join(image_dir, f"{safe_query}_{i}.jpg")
            img.save(path)
            print("[IMAGE] Saved →", path)

            # Also save to web_images
            web_path = os.path.join(web_dir, f"{safe_query}_{i}_{timestamp}.jpg")
            img.save(web_path)
            print("[IMAGE] Web copy →", web_path)

            images.append(img)
            saved_paths.append(path)
            if len(images) >= count:
                break
        except Exception as e:
            print("[IMAGE] Failed:", e)

    if not images:
        return "No images downloaded"

    print("[IMAGE] Loaded", len(images), "images")

    cols = math.ceil(math.sqrt(len(images)))
    rows = math.ceil(len(images) / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(8, 8))
    axes = [axes] if rows * cols == 1 else list(
        __import__("itertools").chain.from_iterable(
            [axes] if rows == 1 else axes
        )
    )

    for i, (ax, img) in enumerate(zip(axes, images)):
        ax.imshow(img)
        ax.axis("off")

    for ax in axes[len(images):]:
        ax.axis("off")

    plt.tight_layout()

    # Save grid to original directory
    grid_path = os.path.join(image_dir, f"{safe_query}_grid.jpg")
    plt.savefig(grid_path, bbox_inches="tight", dpi=100)
    print("[IMAGE] Grid saved →", grid_path)

    # Save grid to web_images
    web_grid_filename = f"image_grid_{safe_query}_{timestamp}.jpg"
    web_grid_path = os.path.join(web_dir, web_grid_filename)
    shutil.copy2(grid_path, web_grid_path)
    print("[IMAGE] Web grid copy →", web_grid_path)

    plt.close(fig)

    # Return in format the web interface understands
    return f"[IMAGE:{web_grid_filename}]"