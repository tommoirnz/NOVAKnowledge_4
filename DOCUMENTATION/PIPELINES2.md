# Nova's Architecture: A Full Pipeline Breakdown

Here's a comprehensive look at how Nova actually works under the hood, based on a live inspection of the source code (42,379 characters of it).

---

## The Big Picture

Nova uses a **planner-executor pattern**: the LLM plans what to do, the executor dispatches agents, and tools do the actual work. Clean separation of concerns.

```
User Input → TaskPlanner → JSON Plan → AgentExecutor → Results → Final Response
```

---

## 1. Task Planning Pipeline

```
User Input → TaskPlanner.create_plan()
    ├── Intent Detection (_is_follow_up, image keywords)
    ├── Context Extraction (_extract_relevant_context)
    ├── History Formatting (selective vs full)
    └── LLM Prompt → JSON Plan {mode, tasks[]}
```

The planner is the entry point. It analyses raw user input and produces a structured JSON plan specifying **which agents to run** and **how** — parallel or sequential. Nothing executes until the plan exists.

---

## 2. Parallel Execution Pipeline

```
Plan {mode: "parallel"} → AgentExecutor.run_tasks()
    └── ThreadPoolExecutor (max 4 workers)
        ├── _run_agent(task_1)
        ├── _run_agent(task_2)
        └── _run_agent(task_N)  ← all fire simultaneously
```

Used when tasks are **independent** of each other. Results are collected as futures complete. Fast, but no task can depend on another's output.

---

## 3. Sequential Execution Pipeline

```
Plan {mode: "sequential"} → AgentExecutor.run_tasks_sequential()
    ├── Safety net: self_inspect always followed by text agent
    ├── Task 1 → _run_agent() → result_1
    │   └── accumulated_context updated
    ├── Task 2 → _run_agent() [context injected] → result_2
    └── Task N → ...
```

Each task's output feeds into the next via an `accumulated_context` string — this is the **inter-task memory bus**. Critical for chains like `self_inspect → text` or `research → code`. The current response you're reading is itself a product of this pipeline.

---

## 4. Agent Dispatch Pipeline

Inside `_run_agent()`, tasks are routed based on the `agent` field:

```
task.agent →
    ├── Tool agents (tool_map lookup)
    │   ├── search_and_show_image  → query cleaning → tools.run()
    │   ├── open_webpage           → tools.run()
    │   └── play_local_music, etc. → tools.run()
    │
    ├── diagram    → tools.run("diagram") → show_graphviz_diagram()
    ├── research   → ai.react_agent() [multi-step ReAct loop, max 6 steps]
    ├── code       → ai.generate_code() → smart_loop.run() [async thread]
    ├── sympy_exec → ai.generate() → tools.run("sympy_exec")
    ├── math       → ai.generate() [LaTeX only]
    └── text       → ai.generate() [conversational]
```

Query sanitisation happens **before** tool calls for agents like `search_and_show_image` and file commands (`_translate_file_command`), preventing raw user phrasing from polluting tool inputs.

---

## 5. Code Execution Pipeline

```
code agent →
    ai.generate_code(prompt)
    └── smart_loop.run(code)
        ├── Execute code
        ├── On failure: retry/repair (up to N attempts)
        └── _deliver_tool_result(output)  ← async, back on main thread
```

This is the **only asynchronous pipeline**. Code runs in a daemon thread and delivers results back to the UI via `root.after()`. The smart loop handles auto-repair on failure — it doesn't just crash and give up.

---

## 6. Self-Inspect → Text Pipeline *(what produced this response)*

```
self_inspect → raw source code (42,379 chars)
    └── accumulated_context += source
        └── text agent → "Based on source code: {task}"
```

A special two-step sequential chain with an **auto-appended text agent** as a safety net. This ensures inspection results are always *interpreted* rather than dumped raw at the user. Thoughtful design.

---

## Key Design Patterns Summary

| Pattern | Where Used |
|---|---|
| Context accumulation between steps | `run_tasks_sequential` |
| Async code execution | `code` agent + daemon thread |
| Auto-repair on failure | `smart_loop` in code pipeline |
| Auto-appended safety agent | `self_inspect` → always followed by `text` |
| Query sanitisation before tool calls | `search_and_show_image`, `_translate_file_command` |
| History injection into prompts | `_format_history_for_agent` |
| Multi-step reasoning | `research` agent via ReAct loop (max 6 steps) |

---

The architecture is genuinely well-structured — the planner keeps the LLM in a reasoning role while the executor handles all the messy dispatch logic. The `accumulated_context` bus is the clever bit that makes multi-step chains actually useful rather than just sequential noise.