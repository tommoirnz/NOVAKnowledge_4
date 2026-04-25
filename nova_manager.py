"""
nova_manager.py — Multi-agent manager for Nova Assistant.

Contains ManagerAgent: responsible for analysing, supervising,
and executing multi-agent task plans via the executor.

Usage:
    from nova_manager import ManagerAgent

    self.manager = ManagerAgent(self.ai, logger=self.log, nova=self)
"""


import warnings
from typing import Any


class ManagerAgent:
    def __init__(self, ai, logger=None, nova=None):
        """Initialize the ManagerAgent.

        Args:
            ai: AI model instance for generating responses
            logger: Optional logging function
            nova: Reference to the main NovaAssistant instance
        """
        self.ai = ai
        self.log = logger
        self.nova = nova

    SEQUENTIAL_PAIRS: list[tuple[str, str]] = [
        ("research", "code"),
        ("search_and_show_image", "code"),
        ("file_explorer", "text"),
        ("self_inspect", "text"),
    ]
    MAX_AGENTS = 3

    def analyse(self, plan, force_mode=None):
        """
        Validate the plan dict, enforce safe agent combinations, and cap task count.

        Args:
            plan:       dict with 'mode' and 'tasks', or a list of task dicts
            force_mode: optional override ('parallel' | 'sequential') applied
                        AFTER safety checks — use with care

        Returns:
            Sanitised plan dict. If tasks were truncated, a 'dropped' key
            is added containing the removed task dicts.
        """
        if isinstance(plan, dict):
            mode = plan.get("mode", "parallel")
            tasks = plan.get("tasks") or []
        else:
            mode = "parallel"
            tasks = list(plan) if isinstance(plan, list) else []

        # ── Collect ALL validation errors before raising ──────────────────────
        errors = []
        for i, t in enumerate(tasks):
            if not isinstance(t, dict):
                errors.append(f"Task {i}: must be a dict, got {type(t).__name__}")
                continue
            if "agent" not in t:
                errors.append(f"Task {i}: missing 'agent' key")
            elif not isinstance(t["agent"], str):
                errors.append(f"Task {i}: 'agent' must be str, got {type(t['agent']).__name__}")
            if not isinstance(t.get("task"), str) or not t.get("task"):
                errors.append(f"Task {i}: 'task' must be a non-empty string")

        if errors:
            raise ValueError("Plan validation failed:\n" + "\n".join(errors))

        plan = {"mode": mode, "tasks": tasks}

        # ── Check ALL sequential pairs, not just the first ────────────────────
        triggered_pairs = []
        agent_types = {t["agent"] for t in tasks}
        for a, b in self.SEQUENTIAL_PAIRS:
            if a in agent_types and b in agent_types:
                triggered_pairs.append((a, b))

        if triggered_pairs:
            plan["mode"] = "sequential"
            if self.log:
                self.log(f"[MANAGER] Sequential forced by pairs: {triggered_pairs}")

        # ── Apply force_mode AFTER safety checks ──────────────────────────────
        if force_mode in ("parallel", "sequential"):
            plan["mode"] = force_mode
            if self.log:
                self.log(f"[MANAGER] Mode manually overridden to: {force_mode}")

        # ── Cap task count — preserve dropped tasks for caller ────────────────
        if len(tasks) > self.MAX_AGENTS:
            dropped = tasks[self.MAX_AGENTS:]
            plan["tasks"] = tasks[:self.MAX_AGENTS]
            plan["dropped"] = dropped
            dropped_names = [t["agent"] for t in dropped]
            if self.log:
                self.log(
                    f"[MANAGER] ⚠️ Truncated to {self.MAX_AGENTS}. "
                    f"Dropped: {dropped_names}"
                )
            warnings.warn(
                f"Task list truncated from {len(tasks)} to {self.MAX_AGENTS}. "
                f"Dropped agents: {dropped_names}",
                UserWarning,
                stacklevel=2
            )

        if self.log:
            self.log(f"[MANAGER] Mode: {plan['mode']} | Tasks: {len(plan['tasks'])}")

        return plan



    def execute(
        self,
        plan: dict,
        executor: Any,
        internet_ctx: str = "",
        history_str: str = "",
    ) -> list:
        """Dispatch tasks to the executor in the mode specified by the plan."""
        tasks = plan.get("tasks", [])
        mode  = plan.get("mode", "parallel")

        if not tasks:
            if self.log:
                self.log("[MANAGER] No tasks to execute — returning empty list")
            return []

        if mode == "parallel":
            if self.log:
                self.log(f"[MANAGER] Running {len(tasks)} tasks in parallel")
            return executor.run_tasks(tasks, internet_ctx, history_str)

        if self.log:
            self.log(f"[MANAGER] Running {len(tasks)} tasks sequentially")
        return executor.run_tasks_sequential(tasks, internet_ctx, history_str)
    # ──────────────────────────────────────────────────────────────────────────
    # 3. SUPERVISE OUTPUTS
    # ──────────────────────────────────────────────────────────────────────────

    def supervise(self, results, user_input):
        """Merge multiple agent results into one coherent answer."""
        clean_results = [
            r for r in results
            if r
            and not str(r).startswith("[RUNNING CODE")
            and not str(r).startswith("[AGENT ERROR]")
        ]

        if not clean_results:
            return None

        if len(clean_results) == 1:
            return clean_results[0]

        combined = "\n\n".join(
            f"[RESULT {i + 1}]\n{r}" for i, r in enumerate(clean_results)
        )

        env_ctx = self.nova.build_env_context() if self.nova else ""

        prompt = f"""
{env_ctx}

You are a supervisor AI.

User question:
{user_input}

Agent results:
{combined}

Tasks:
- Remove contradictions
- Merge into one detailed and comprehensive answer
- Preserve important facts, numbers, and explanations
- DO NOT over-summarise
- ALWAYS include source links if present
- Preserve URLs exactly
- Add a "Sources:" section at the end with links
- If a sympy_exec result is present, use THAT as the verification —
  do NOT invent or substitute your own verification
- NEVER use illustrative code snippets from math explanations as verification
- Verification means the actual computed result from sympy_exec only
- NEVER invent or fabricate source links
- If a result came from sympy_exec, say "Verified locally using SymPy" — no link needed
- Only include URLs that actually appeared in the agent results

Final answer:
"""
        return self.ai.generate(prompt, use_planning=False)

    # ──────────────────────────────────────────────────────────────────────────
    # 4. SUPERVISE PLAN (pre-execution)
    # ──────────────────────────────────────────────────────────────────────────

    def supervise_plan(self, plan, user_input):
        """Validate and improve the plan BEFORE execution."""
        if self.log:
            self.log("[SUPERVISOR] Reviewing plan before execution")

        tasks  = plan.get("tasks", [])
        agents = [t.get("agent") for t in tasks]

        # Respect planner's media decisions — never override
        if len(tasks) == 1 and agents[0] in [
            "play_local_music", "play_local_video", "play_youtube_video"
        ]:
            self.log(f"[SUPERVISOR] Respecting planner → {agents[0]}")
            return plan

        # Ensure research runs before code
        if "research" in agents and "code" in agents:
            plan["mode"] = "sequential"
            priority = {
                "research": 0,
                "file_explorer": 1,
                "search_and_show_image": 2,
                "code": 3,
                "text": 4
            }
            tasks = sorted(tasks, key=lambda t: priority.get(t["agent"], 99))
            plan["tasks"] = tasks
            if self.log:
                self.log("[SUPERVISOR] Enforced order: research → code")

        # Cap total tasks
        MAX_TASKS = 4
        if len(tasks) > MAX_TASKS:
            plan["tasks"] = tasks[:MAX_TASKS]
            if self.log:
                self.log(f"[SUPERVISOR] Trimmed tasks → {MAX_TASKS}")

        # Redirect code/file_explorer tasks that should use media tools
        available_tools = self.nova.tools.list_tools() if self.nova else []

        for i, t in enumerate(tasks):
            agent = t.get("agent")
            job   = t.get("task", "").lower()

            if agent in ["code", "file_explorer"]:
                if any(w in job for w in ["play", "open", "launch", "start"]):
                    if any(w in job for w in ["video", "film", "movie", "mp4", "mkv"]):
                        if "play_local_video" in available_tools:
                            tasks[i] = {"agent": "play_local_video", "task": job}
                            self.log("[SUPERVISOR] Redirected code → play_local_video")
                    elif any(w in job for w in ["music", "song", "mp3", "audio", "track"]):
                        if "play_local_music" in available_tools:
                            tasks[i] = {"agent": "play_local_music", "task": job}
                            self.log("[SUPERVISOR] Redirected code → play_local_music")

        plan["tasks"] = tasks
        return plan