import os
import re



def write_file(path, content):
    path = path.replace("~", os.path.expanduser("~"))
    path = path.replace("%desktop%", os.path.join(os.path.expanduser("~"), "Desktop"))

    # Only replace standalone 'desktop' keyword, not inside real paths
    if re.match(r'^desktop[/\\]', path, re.IGNORECASE):
        path = os.path.join(os.path.expanduser("~"), "Desktop", path[8:])

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return f"✅ Written → {os.path.abspath(path)}"