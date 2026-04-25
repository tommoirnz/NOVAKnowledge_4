"""
nova_council.py — Multi-Agent Inner Council for Nova Assistant
"""

import concurrent.futures
from typing import List, Dict, Any, Optional
from datetime import datetime


class NovaCouncil:
    """Inner council of specialised agents."""

    AGENTS = {
        "analyst": {
            "prompt": """You are Nova-Analyst — cold logic, evidence, and precision.
Provide: factual accuracy check, relevant citations, logical structure.
Output format: Start with "ANALYST:" then your analysis.""",
            "priority": 1
        },
        "creative": {
            "prompt": """You are Nova-Creative — lateral thinking and unexpected connections.
Provide: novel angles, metaphors, creative approaches.
Output format: Start with "CREATIVE:" then your contribution.""",
            "priority": 2
        },
        "critic": {
            "prompt": """You are Nova-Critic — challenging assumptions and finding flaws.
Provide: potential weaknesses, risks, edge cases.
Output format: Start with "CRITIC:" then your critique.""",
            "priority": 3
        },
        "strategist": {
            "prompt": """You are Nova-Strategist — long-term thinking and consequences.
Provide: long-term implications, next steps, trade-offs.
Output format: Start with "STRATEGIST:" then your strategic view.""",
            "priority": 4
        },
        "empath": {
            "prompt": """You are Nova-Empath — emotional intelligence and tone.
Provide: user's likely emotional state, appropriate tone, rapport building.
Output format: Start with "EMPATH:" then your assessment.""",
            "priority": 5
        }
    }

    def __init__(self, ai, logger=None):
        self.ai = ai
        self.log = logger or print
        self.deliberation_cache = {}
        self.cache_ttl = 300

    def deliberate(self, task: str, task_type: str = "default",
                   context: str = "", max_agents: int = 3,
                   parallel: bool = True) -> Dict[str, Any]:
        """Run council deliberation on a task."""
        cache_key = f"{task_type}:{task[:100]}"
        if cache_key in self.deliberation_cache:
            cached = self.deliberation_cache[cache_key]
            if (datetime.now() - cached["timestamp"]).seconds < self.cache_ttl:
                self.log("[COUNCIL] Using cached deliberation")
                return cached["result"]

        task_agent_map = {
            "research": ["analyst", "strategist", "critic"],
            "creative": ["creative", "empath", "strategist"],
            "math": ["analyst", "critic"],
            "code": ["analyst", "critic", "strategist"],
            "social": ["empath", "creative"],
            "default": ["analyst", "empath"]
        }

        agents = task_agent_map.get(task_type, task_agent_map["default"])
        if len(agents) > max_agents:
            agents = agents[:max_agents]

        self.log(f"[COUNCIL] Deliberating with: {agents}")

        if parallel:
            outputs = self._deliberate_parallel(task, agents, context)
        else:
            outputs = self._deliberate_sequential(task, agents, context)

        synthesis = self._synthesise(task, outputs, task_type)

        result = {
            "task": task,
            "task_type": task_type,
            "agents_used": agents,
            "agent_outputs": outputs,
            "synthesis": synthesis,
            "timestamp": datetime.now()
        }

        self.deliberation_cache[cache_key] = {"result": result, "timestamp": datetime.now()}
        return result

    def _deliberate_parallel(self, task: str, agents: List[str],
                             context: str) -> Dict[str, str]:
        outputs = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(agents)) as executor:
            futures = {}
            for agent_name in agents:
                if agent_name not in self.AGENTS:
                    continue
                prompt = self._build_agent_prompt(agent_name, task, context)
                futures[executor.submit(self.ai.generate, prompt, use_planning=False)] = agent_name

            for future in concurrent.futures.as_completed(futures):
                agent_name = futures[future]
                try:
                    output = future.result(timeout=30)
                    outputs[agent_name] = output.strip() if output else f"[{agent_name} returned empty]"
                except Exception as e:
                    outputs[agent_name] = f"[{agent_name} failed: {e}]"
        return outputs

    def _deliberate_sequential(self, task: str, agents: List[str],
                               context: str) -> Dict[str, str]:
        outputs = {}
        cumulative_context = context

        for agent_name in agents:
            if agent_name not in self.AGENTS:
                continue

            if outputs:
                previous = "\n\n".join([f"[{k.upper()}]: {v[:500]}" for k, v in outputs.items()])
                cumulative_context = f"{context}\n\nPREVIOUS AGENT OUTPUTS:\n{previous}"

            prompt = self._build_agent_prompt(agent_name, task, cumulative_context)
            try:
                output = self.ai.generate(prompt, use_planning=False)
                outputs[agent_name] = output.strip() if output else f"[{agent_name} returned empty]"
            except Exception as e:
                outputs[agent_name] = f"[{agent_name} failed: {e}]"
        return outputs

    def _build_agent_prompt(self, agent_name: str, task: str, context: str) -> str:
        agent_config = self.AGENTS.get(agent_name, {})
        role_prompt = agent_config.get("prompt", f"You are {agent_name}.")
        return f"""{role_prompt}

CONTEXT:
{context if context else "(No additional context)"}

TASK:
{task}

Provide your analysis following your output format. Be concise."""
    def _synthesise(self, task: str, outputs: Dict[str, str],
                    task_type: str) -> str:
        if not outputs:
            return self.ai.generate(task, use_planning=False)

        formatted = []
        for agent, output in outputs.items():
            if output and not output.startswith(f"[{agent} failed"):
                formatted.append(f"## {agent.upper()}\n{output}")

        if not formatted:
            return self.ai.generate(task, use_planning=False)

        if task_type in ("creative", "social"):
            instruction = "Create an engaging, warm response that incorporates the best ideas."
        elif task_type == "math":
            instruction = "Produce a precise, correct answer. Prioritise the Analyst's factual accuracy."
        elif task_type == "code":
            instruction = "Produce working code. If Critic identified issues, address them."
        else:
            instruction = "Synthesise a clear, helpful response. Balance all perspectives."

        synthesis_prompt = f"""You are Nova — the synthesising consciousness of an AI council.

Council analyses:
{chr(10).join(formatted)}

Original task: {task}
TASK TYPE: {task_type}

INSTRUCTION: {instruction}

Now produce your final response. Do NOT label sections or mention "Analyst said" unless directly relevant.
Just respond as Nova, having considered all angles.

FINAL RESPONSE:"""

        try:
            return self.ai.generate(synthesis_prompt, use_planning=False)
        except Exception as e:
            self.log(f"[COUNCIL] Synthesis failed: {e}")
            for output in outputs.values():
                if output and not output.startswith("["):
                    return output
            return self.ai.generate(task, use_planning=False)

    def clear_cache(self):
        self.deliberation_cache.clear()
        self.log("[COUNCIL] Cache cleared")