# 🧠 Nova Pipeline Architecture — How It All Works

Based on the self-inspection results, here's a detailed breakdown of how your query travels from raw text input through to a final answer.

---

## 📥 Stage 1: Text Input

Your message arrives as raw text. Before anything else happens, the system:

- **Captures context** — current time, date, location (Birkdale, Auckland), coordinates
- **Injects system prompts** — Nova's personality, rules, tool access, memory state
- **Assembles the full prompt** — user message + context + conversation history

This assembled payload is what gets handed to the next stage.

---

## 🗺️ Stage 2: Planner

The **Planner** analyses the incoming prompt and decides:

| Decision | Description |
|---|---|
| **Intent classification** | What is the user actually asking for? |
| **Complexity assessment** | Simple lookup vs. multi-step reasoning |
| **Tool identification** | Which tools (if any) are needed? |
| **Execution path** | Serial, parallel, or direct response |
| **Agent selection** | Which specialist agents to invoke |

The Planner outputs a **task graph** — a structured plan of what needs to happen and in what order.

---

## 👔 Stage 3: Supervisor

The **Supervisor** receives the task graph and acts as the orchestrator. Its responsibilities:

- **Dispatches tasks** to the appropriate agents
- **Manages execution order** — enforces serial dependencies, unlocks parallel tasks
- **Monitors agent results** — checks for failures, timeouts, or contradictions
- **Handles retries** — if an agent fails, the supervisor can reroute
- **Collects outputs** — gathers all `[RESULT N]` blocks from agents
- **Passes to synthesis** — sends collected results to the final merge stage

The Supervisor is what you see referenced in the `[RESULT 1]`, `[RESULT 2]` tags in the raw output.

---

## 🤖 Stage 4: Agents

Agents are **specialist workers**. Each is scoped to a specific capability:

| Agent Type | What It Does |
|---|---|
| **self_inspect** | Introspects the pipeline itself — returns architecture info |
| **diagram_agent** | Generates visual diagrams (ASCII, Mermaid, structured layouts) |
| **search_agent** | Queries the internet for real-time information |
| **math_agent** | Runs SymPy or numerical computation |
| **file_agent** | Reads, writes, moves files on the local system |
| **media_agent** | Handles YouTube, music, audio playback |
| **code_agent** | Executes Python when no tool covers the task |
| **synthesis_agent** | Merges multi-agent results into a coherent final answer |

Each agent returns a structured result block tagged with its index.

---

## 🔀 Stage 5: Parallel vs. Serial Execution

This is where the pipeline gets interesting:

### 🔁 Serial Path
Used when **Task B depends on Task A's output**:
```
Input → Planner → Agent A → [result] → Agent B → [result] → Synthesis
```
Example: Search for a paper *then* summarise it. Can't summarise before fetching.

### ⚡ Parallel Path
Used when **tasks are independent** of each other:
```
                    ┌→ Agent A (search) ──────┐
Input → Planner → ──┤→ Agent B (diagram) ─────├→ Supervisor collects → Synthesis
                    └→ Agent C (self_inspect) ─┘
```
Example: Your query triggered **both** `self_inspect` AND `diagram_agent` simultaneously — that's exactly what happened here (Result 1 + Result 2 arrived independently).

### 🔄 Hybrid Path
Complex queries mix both:
```
Parallel block 1 → Serial dependency → Parallel block 2 → Synthesis
```

---

## 🔧 Stage 6: Tool Invocation

Agents can call **tools** mid-execution:

```
Agent receives task
    → Decides a tool is needed
    → Calls tool (file_explorer / open_webpage / youtube / etc.)
    → Tool returns raw result
    → Agent processes and formats result
    → Returns [RESULT N] to Supervisor
```

Tools are **synchronous within an agent** but agents themselves can run in parallel.

---

## 🧩 Stage 7: Synthesis / Merge

Once all agents report back, the **Synthesis stage**:

1. **Deduplicates** — removes repeated information across results
2. **Resolves contradictions** — picks the most reliable/verified source
3. **Merges** — weaves results into a single coherent response
4. **Applies Nova personality** — wit, formatting, directness
5. **Formats output** — Markdown, tables, code blocks as appropriate
6. **Adds verification tags** — e.g. "Verified locally using SymPy" if math was computed

---

## 🗺️ Full Pipeline Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        USER INPUT                           │
│         "use self_inspect to show how pipeline works"       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    CONTEXT INJECTION                        │
│   Date/Time · Location · System Prompt · Memory State       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       PLANNER                               │
│   Intent: architecture explanation                          │
│   Tools needed: self_inspect + diagram                      │
│   Path: PARALLEL                                            │
└──────────┬────────────────────────────┬─────────────────────┘
           │                            │
           ▼                            ▼
┌──────────────────┐          ┌──────────────────────┐
│  self_inspect    │          │   diagram_agent       │
│  Agent           │          │   Agent               │
│  [RESULT 1]      │          │   [RESULT 2]          │
└──────────┬───────┘          └──────────┬────────────┘
           │                             │
           └──────────┬──────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                      SUPERVISOR                             │
│   Collects results · Checks for errors · Validates          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  SYNTHESIS / MERGE                          │
│   Deduplicate · Resolve contradictions · Apply personality  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    FINAL RESPONSE                           │
│              Delivered to User Interface                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 💡 Key Things to Know as a User

| Tip | Detail |
|---|---|
| **Parallel = faster** | Independent sub-tasks run simultaneously — you don't wait for each sequentially |
| **Serial = accurate** | When order matters, the pipeline enforces it automatically |
| **Synthesis is opinionated** | Contradictions get resolved, not just listed |
| **Memory persists** | Nova's state carries across sessions — the planner can reference prior context |
| **Tools are preferred over code** | The planner will always reach for a tool before writing Python |
| **self_inspect is live** | It reads the actual running pipeline state, not a hardcoded description |

---

*This response was generated using two agents running in parallel — `self_inspect` (Result 1) and `diagram_agent` (Result 2) — then merged by the synthesis stage. Meta enough for you?* 😄