# Nova Tool Installation Guide

## Overview

Nova uses an automatic `ToolRegistry` that discovers tools by scanning the `tools/` directory.
This means most registration is handled automatically — but several other layers must be wired
manually for a tool to be fully integrated.

---

## Step 1 — Create the Tool File

Create `tools/your_tool.py`. Follow this signature exactly:

```python
def your_tool(query: str, log_callback=None) -> str:
    """
    One-line description of what this tool does and when to use it.
    """
    try:
        if log_callback:
            log_callback(f"[YOUR_TOOL] Running: {query}")

        # --- tool logic here ---
        result = "your result"
        return result

    except Exception as e:
        if log_callback:
            log_callback(f"[YOUR_TOOL] Error: {e}")
        return f"Error: {str(e)}"
```

**Rules:**
- Function name must match the filename (e.g. `sympy_exec.py` → `def sympy_exec(...)`)
- Always accept `log_callback=None`
- Always return a plain string
- Never raise unhandled exceptions — catch and return error string

---

## Step 2 — Registration (Automatic)

The `ToolRegistry` auto-imports all `.py` files in `tools/` that don't start with `_`.
No manual registration needed — just dropping the file in the folder is enough.

Verify it appeared on next startup:
```
[TOOLS] Loaded: [..., 'your_tool', ...]
```

---

## Step 3 — Add to VALID_AGENTS (TaskPlanner)

In `task_planner.py`, add to the `VALID_AGENTS` set in `__init__`:

```python
self.VALID_AGENTS = {
    ...
    "your_tool",   # ← add here
}
```

Without this, the planner silently drops any task routed to your tool.

---

## Step 4 — Add to the Planner Prompt

In `task_planner.py`, inside `create_plan()`, add to the AVAILABLE AGENTS section:

```
- your_tool   → brief description of when to use it
               Use for: "example trigger phrase", "another phrase"
               Important constraint or argument format note
```

Also add a routing rule if needed, e.g.:

```
YOUR_TOOL RULE:
- Use your_tool when the user asks for X
- Trigger words: "keyword1", "keyword2"
- The task MUST include the actual subject, e.g.:
  {"agent": "your_tool", "task": "do X with <expression>"}
  NOT: {"agent": "your_tool", "task": "do X with the previous result"}
- ALWAYS copy the exact subject from the user request into the task field
```

**Catch:** If the task description is vague (e.g. "verify the result"), the tool
receives no useful input and will fail or produce garbage. The planner prompt must
explicitly instruct the model to carry the full expression/subject forward.

---

## Step 5 — Add to _run_agent (Executor)

In the executor class (e.g. `nova_executor.py`), add a branch to `_run_agent()`:

```python
# ── YOUR TOOL ──────────────────────────
if agent == "your_tool":
    self.nova.log("[YOUR_TOOL] Running...")
    result = self.nova.tools.run("your_tool", job)
    return result
```

Place it before the `# ── MATH / TEXT / FALLBACK` section.

**If your tool requires AI-generated input** (e.g. the tool runs code that the AI writes),
generate it here before calling the tool:

```python
if agent == "your_tool":
    code = self.nova.ai.generate(
        f"Write code to: {job}\nReturn ONLY valid code, no markdown.",
        use_planning=False
    )
    # Strip markdown fences — the AI ignores instructions and adds them anyway
    code = re.sub(r"```(?:python)?\s*", "", code)
    code = re.sub(r"```", "", code).strip()
    result = self.nova.tools.run("your_tool", code)
    return result
```

---

## Step 6 — Add to ai_choose_tool (Tool Descriptions)

In `nova_assistant.py`, add to the `tool_descriptions` dict in `ai_choose_tool()`:

```python
"your_tool": "Brief description of what this tool does and when to use it.",
```

---

## Step 7 — Add to try_ai_tool (Dispatch)

In `nova_assistant.py`, add a branch to `try_ai_tool()`:

```python
elif tool_name == "your_tool":
    result = self.tools.run("your_tool", arg)
    return result
```

---

## Step 8 — Handle Results in _handle_planner

If your tool produces output that the synthesiser (`manager.supervise()`) might
absorb or discard, extract it before synthesis and append it after:

```python
# Extract before synthesis
your_tool_results = []
for i, task in enumerate(plan.get("tasks", [])):
    if task.get("agent") == "your_tool" and i < len(results):
        your_tool_results.append(results[i])

response = manager.supervise(results, user_input)

# Append after synthesis so it always appears
if your_tool_results:
    for r in your_tool_results:
        if r and not str(r).startswith("Error"):
            response = (response or "") + f"\n\n---\n{r}"
```

---

## Checklist

```
✅  tools/your_tool.py          — correct signature, returns string, handles exceptions
✅  VALID_AGENTS set            — tool name added or planner silently drops it
✅  Planner prompt              — tool listed in AVAILABLE AGENTS with description
✅  Planner routing rule        — trigger words and task format specified
✅  _run_agent()                — dispatch branch added
✅  ai_choose_tool()            — tool_descriptions entry added
✅  try_ai_tool()               — dispatch branch added
✅  _handle_planner()           — result extraction if synthesiser might swallow output
```

---

## Common Catches

### 1. AI adds markdown fences to code output
The AI wraps code in ` ```python ``` ` even when told not to. Always strip:
```python
code = re.sub(r"```(?:python)?\s*", "", code)
code = re.sub(r"```", "", code).strip()
```

### 2. AI uses functions without importing them
If the AI generates code that calls functions, prepend safe imports:
```python
header = "from your_library import *\n"
if "import" not in code:
    code = header + code
```

### 3. Synthesiser swallows tool output
`manager.supervise()` merges all results and may drop or summarise tool output.
Extract and append critical results manually (see Step 8).

### 4. LaTeX not rendering correctly
- Raw LaTeX like `\frac{x^3}{3}` must be wrapped in `$$..$$` to survive markdown processing
- Wrap with surrounding text so Nova's router doesn't misclassify it:
  ```python
  result = f"**Tool Result:**\n\n$$\n{result}\n$$"
  ```
- Extend the `protect()` regex in `_render_latex_in_browser` to cover all delimiter styles:
  ```python
  protected = re.sub(
      r'\$\$.*?\$\$|\$.*?\$|\\\[.*?\\\]|\\\(.*?\\\)',
      protect, text, flags=re.DOTALL
  )
  ```

### 5. Vague task descriptions from planner
If the planner generates `"verify the result"` instead of `"verify integral of x^3"`,
the tool receives no useful input. Fix in the planner prompt:
```
- ALWAYS copy the exact subject/expression from the user request into the task field
- NEVER use vague references like "the result" or "the computed value"
```

### 6. Tool not appearing in TOOLS Loaded
- Check the filename doesn't start with `_`
- Check the filename isn't `tool_registry.py`
- Check there are no import errors in the file (check the startup log for failures)

### 7. Tool selected but wrong argument format
Some tools need structured input (code, URLs, paths) not plain English.
Document this clearly in the planner prompt and `ai_choose_tool` description,
and include a CORRECT/INCORRECT example.

---

## Testing

**Functional test** — trigger the tool directly:
```
[trigger phrase] [subject]
```
Watch logs for:
```
[TOOLS] Running → your_tool
[YOUR_TOOL] Running: ...
[TOOL RESULT] ...
```

**Negative test** — confirm it doesn't over-trigger:
```
what is the weather today
```
Should route to planner/research, not your tool.

**Sequential test** — if chaining with other agents:
```
[do X] and [use your_tool to verify]
```
Watch logs for both agents executing in order.
