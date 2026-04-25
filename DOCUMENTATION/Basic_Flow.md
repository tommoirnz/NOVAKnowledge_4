# Nova Query Routing

## Flow
```
_process_input
    │
    ├── Cache hit?          → return immediately
    ├── Follow-up?          → return immediately  
    ├── Location query?     → return immediately
    ├── ReAct trigger?      → _handle_react() → return
    ├── try_tool()          → rule-based match → return
    │
    └── _handle_planner()
            │
            ├── 1. TaskPlanner.create_plan()
            │       └── returns {mode, tasks}
            │
            ├── 2. ManagerAgent.analyse()
            ├── 3. ManagerAgent.supervise_plan()
            │
            ├── 4. manager.execute()
            │       ├── parallel → ThreadPoolExecutor (4 workers)
            │       └── sequential → ordered, context-chaining
            │
            └── 5. ManagerAgent.supervise()
                    └── synthesised response → user
```

## Roles

| Component | Role |
|---|---|
| `TaskPlanner` | Decomposes query into task list |
| `ManagerAgent.analyse` | Reviews and structures the plan |
| `ManagerAgent.supervise_plan` | Pre-execution approval |
| `AgentExecutor` | Runs the actual agents |
| `ManagerAgent.supervise` | Post-execution synthesis |

## Early Exit Points

| Condition | Handler |
|---|---|
| Exact repeat query | Cache hit — returns `last_result` |
| "repeat" / "do that again" | Replays last task |
| "where am i" etc | `get_environment()` directly |
| URL / arxiv / `.pdf` | `_handle_react()` |
| YouTube / image / sound etc | `try_tool()` |
| Short simple query | Final `ai.generate()` directly |