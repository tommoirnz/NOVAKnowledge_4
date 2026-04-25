import re

path = r"C:\Users\OEM\PycharmProjects\Nova_ResearchAI_4\nova_assistant_v1.py"

with open(path, "r", encoding="utf-8") as f:
    source = f.read()

# Collapse 3+ consecutive blank lines down to 2
compacted = re.sub(r'\n{3,}', '\n\n', source)

with open(path, "w", encoding="utf-8") as f:
    f.write(compacted)

original = source.count('\n')
final = compacted.count('\n')
print(f"Lines before: {original}  →  after: {final}  (saved {original - final})")
