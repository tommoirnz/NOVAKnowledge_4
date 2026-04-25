import json
import os

# Go up one directory to the project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
json_path = os.path.join(project_root, "nova_state.json")

print(f"Looking for file at: {json_path}")
print(f"File exists: {os.path.exists(json_path)}")

if os.path.exists(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)
        print(f"\nNumber of saved exchanges: {len(data.get('history', []))}")
        print("\nAll saved queries:")
        for i, entry in enumerate(data.get('history', [])):
            print(f"{i+1}. {entry.get('task', '')[:80]}")
else:
    print("nova_state.json not found")