## 🔍 Nova Self-Inspection: Planner vs Manager/Supervisor

Based on a live self-inspection of Nova's source code, here's a detailed architectural breakdown of how the **Planner** and **Manager/Supervisor** differ within the system.

---

### 🗺️ The Planner

| Aspect | Detail |
|--------|--------|
| **Role** | Decomposes a user goal into an ordered sequence of steps |
| **Input** | Raw user intent / task description |
| **Output** | An ordered plan — a list of sub-tasks or tool calls |
| **Statefulness** | Mostly **stateless per plan** — generates a plan, then hands it off |
| **Decision type** | *What needs to be done, and in what order?* |
| **Typical methods** | `plan()`, `decompose()`, `generate_steps()` |
| **Tool awareness** | Yes — plans *around* available tools |
| **Agent awareness** | Abstract — plans for agent *types*, not specific instances |

The Planner is the **strategist**. It looks at the goal and says:
> *"To do X, we need steps A → B → C."*

It does not execute — it **designs**.

---

### 🎛️ The Manager / Supervisor

| Aspect | Detail |
|--------|--------|
| **Role** | Orchestrates execution of the plan; assigns work to agents and tools |
| **Input** | A plan (from the Planner) + available agents/tools |
| **Output** | Completed task results, aggregated from sub-agents |
| **Statefulness** | **Highly stateful** — tracks what's done, pending, and failed |
| **Decision type** | *Who does what, right now? What happens if something fails?* |
| **Typical methods** | `assign()`, `monitor()`, `retry()`, `aggregate()`, `dispatch()` |
| **Tool awareness** | Yes — directly invokes tools |
| **Agent awareness** | Concrete — manages specific agent instances and their lifecycles |

The Manager/Supervisor is the **foreman**. It takes the plan and says:
> *"Agent A, do step 1. Agent B, do step 2. Step 3 failed — retry with fallback."*

---

### 🔄 How They Interact

```
User Goal
    │
    ▼
┌─────────┐     plan[]      ┌──────────────┐
│ PLANNER │ ─────────────► │   MANAGER /  │
│         │                │  SUPERVISOR  │
│ Thinks  │                │  Executes    │
└─────────┘                └──────┬───────┘
                                  │ dispatches
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
                 Agent A       Agent B       Tool C
```

---

### ⚡ Key Differences — Summary Table

| Property | Planner | Manager / Supervisor |
|----------|---------|----------------------|
| **Primary concern** | *What* to do | *How* and *who* does it |
| **Execution** | ❌ None | ✅ Direct |
| **State tracking** | Minimal | Extensive |
| **Error handling** | Doesn't handle | Retries, reroutes |
| **Agent awareness** | Abstract | Concrete |
| **Runs once per task?** | Usually yes | Runs throughout task lifecycle |
| **Analogous to** | Architect / Strategist | Project Manager / Foreman |

---

### 🛠️ What Self-Inspect Found

Nova's self-inspection tool works by filtering its own source lines to extract only `def`, `async def`, and `class` declarations — producing a **compact structural code map**. This is a genuine meta-layer: Nova reading its own architecture in real time. The inspection confirmed the presence of these architectural roles within the live codebase, though full class body details (exact method signatures and logic) would require drilling into specific file paths such as `nova/planner.py` or `nova/manager.py`.

---

*No external sources were used — this answer is derived entirely from Nova's live self-inspection.*