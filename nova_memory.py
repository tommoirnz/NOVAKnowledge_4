"""
nova_memory.py — Enhances nova_state.json with semantic, procedural, and prospective memory.
No new dependencies. Works alongside your existing state file.
"""

import os
import json
import hashlib
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict


class NovaMemory:
    """Memory system that extends nova_state.json with 4 layers of memory."""

    def __init__(self, state_path: str = "nova_state.json"):
        self.state_path = state_path
        self.state = self._load_state()
        self.log = print

        if "memory" not in self.state:
            self.state["memory"] = {
                "semantic": {},
                "procedural": {},
                "prospective": [],
                "preferences": {},
                "episodic_index": {}
            }
            self._save_state()

        self.memory = self.state["memory"]
        self._ensure_index()

        # Clean up stale 'pending' keyword from index
        if "pending" in self.memory.get("episodic_index", {}):
            del self.memory["episodic_index"]["pending"]
            self._save_state()
            self.log("[MEMORY] Cleaned stale 'pending' from index")
    def _load_state(self) -> Dict:
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[MEMORY] Failed to load state: {e}")
        return {"history": [], "lessons": [], "memory": {}}

    def _save_state(self):
        try:
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log(f"[MEMORY] Failed to save: {e}")

    def set_logger(self, log_func):
        self.log = log_func

    def _ensure_index(self):
        if self.memory.get("episodic_index") and len(self.memory["episodic_index"]) > 0:
            return

        self.log("[MEMORY] Building keyword index from history...")

        stopwords = {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have',
                     'are', 'was', 'were', 'what', 'when', 'where', 'which', 'how',
                     'you', 'your', 'nova', 'can', 'will', 'would', 'could', 'should'}

        for i, entry in enumerate(self.state.get("history", [])):
            task = entry.get("task", "")
            result = entry.get("result", "")
            combined = f"{task} {result}".lower()
            words = re.findall(r'\b[a-z]{3,}\b', combined)

            for word in words:
                if word not in stopwords:
                    if word not in self.memory["episodic_index"]:
                        self.memory["episodic_index"][word] = []
                    if i not in self.memory["episodic_index"][word]:
                        self.memory["episodic_index"][word].append(i)

        self._save_state()
        self.log(f"[MEMORY] Indexed {len(self.memory['episodic_index'])} keywords")

    def store_conversation(self, user_input: str, response: str):
        """Store a conversation exchange (called twice: before and after response)."""
        history = self.state.get("history", [])

        # Check if this exchange already exists (update mode)
        if response != "(pending)":
            for entry in reversed(history):
                if entry.get("task") == user_input and entry.get("result") == "(pending)":
                    entry["result"] = response[:1000]
                    self._save_state()
                    self.log(f"[MEMORY] Updated conversation: {user_input[:50]}...")

                    # Index this entry now that it's complete
                    idx = history.index(entry)
                    combined = f"{user_input} {response}".lower()
                    words = re.findall(r'\b[a-z]{3,}\b', combined)
                    stopwords = {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have',
                                 'are', 'was', 'were', 'what', 'when', 'where', 'which', 'how',
                                 'you', 'your', 'nova', 'can', 'will', 'would'}
                    for word in words:
                        if word not in stopwords:
                            if word not in self.memory["episodic_index"]:
                                self.memory["episodic_index"][word] = []
                            if idx not in self.memory["episodic_index"][word]:
                                self.memory["episodic_index"][word].append(idx)
                    self._save_state()
                    return

            # No pending found, add new
            history.append({"task": user_input, "result": response[:1000]})
        else:
            # Pending - add new, save, but DON'T index
            history.append({"task": user_input, "result": "(pending)"})
            self.state["history"] = history[-200:]
            self._save_state()
            return  # ← skip indexing for pending entries

        self.state["history"] = history[-200:]
        self._save_state()

        # Update index (for new entries with no prior pending)
        idx = len(self.state["history"]) - 1
        combined = f"{user_input} {response}".lower()
        words = re.findall(r'\b[a-z]{3,}\b', combined)
        stopwords = {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have',
                     'are', 'was', 'were', 'what', 'when', 'where', 'which', 'how',
                     'you', 'your', 'nova', 'can', 'will', 'would',
                     # LaTeX commands
                     'frac', 'int', 'sum', 'quad', 'cdot', 'cdots', 'infty', 'sim',
                     'neq', 'leq', 'geq', 'varepsilon', 'boxed', 'text', 'left', 'right'}
        for word in words:
            if word not in stopwords:
                if word not in self.memory["episodic_index"]:
                    self.memory["episodic_index"][word] = []
                if idx not in self.memory["episodic_index"][word]:
                    self.memory["episodic_index"][word].append(idx)

        self._save_state()
    def recall_conversations(self, query: str, n_results: int = 5) -> List[Dict]:
        """Recall past conversations by keyword matching."""
        keywords = re.findall(r'\b[a-z]{3,}\b', query.lower())
        stopwords = {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have',
                     'are', 'was', 'were', 'what', 'when', 'where', 'which', 'how',
                     'you', 'your', 'nova', 'can', 'will', 'would'}
        keywords = [k for k in keywords if k not in stopwords]

        if not keywords:
            return []

        scores = defaultdict(int)
        for kw in keywords:
            for idx in self.memory.get("episodic_index", {}).get(kw, []):
                scores[idx] += 1

        top_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:n_results]

        results = []
        history = self.state.get("history", [])
        for idx in top_ids:
            if idx < len(history):
                entry = history[idx]
                results.append({
                    "task": entry.get("task", ""),
                    "result": entry.get("result", "")[:500],
                    "relevance": scores[idx]
                })

        return results

    def store_fact(self, fact: str, source: str = "conversation", confidence: float = 0.8):
        """Store a fact in semantic memory."""
        fact_id = hashlib.md5(fact.encode()).hexdigest()[:8]

        self.memory["semantic"][fact_id] = {
            "fact": fact,
            "source": source,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        self._save_state()
        self.log(f"[MEMORY] Stored fact: {fact[:80]}...")

    def recall_facts(self, query: str, min_confidence: float = 0.0) -> List[str]:
        """Recall facts relevant to a query."""
        keywords = set(re.findall(r'\b[a-z]{3,}\b', query.lower()))
        stopwords = {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have', 'are', 'was', 'were'}
        keywords = {k for k in keywords if k not in stopwords}

        results = []
        for fact_id, fact_data in self.memory["semantic"].items():
            if fact_data.get("confidence", 0) < min_confidence:
                continue
            fact_lower = fact_data["fact"].lower()
            if any(kw in fact_lower for kw in keywords):
                results.append(fact_data["fact"])
        return results

    def learn_pattern(self, task_type: str, approach: str, success: bool):
        """Learn from task execution."""
        procedural = self.memory.setdefault("procedural", {})

        if task_type not in procedural:
            procedural[task_type] = {"attempts": 0, "successes": 0, "approaches": {}}

        pattern = procedural[task_type]
        pattern["attempts"] += 1
        if success:
            pattern["successes"] += 1

        if approach not in pattern["approaches"]:
            pattern["approaches"][approach] = {"attempts": 0, "successes": 0}
        pattern["approaches"][approach]["attempts"] += 1
        if success:
            pattern["approaches"][approach]["successes"] += 1

        self._save_state()
        self.log(f"[MEMORY] Learned: {task_type} -> {approach[:50]} (success={success})")

    def get_preferred_approach(self, task_type: str) -> Optional[str]:
        """Get the most successful approach for a task type."""
        procedural = self.memory.get("procedural", {})
        pattern = procedural.get(task_type, {})
        approaches = pattern.get("approaches", {})

        best = None
        best_rate = -1
        for approach, stats in approaches.items():
            if stats["attempts"] >= 2:
                rate = stats["successes"] / stats["attempts"]
                if rate > best_rate:
                    best_rate = rate
                    best = approach
        return best

    def store_preference(self, key: str, value: Any):
        """Store a user preference."""
        preferences = self.memory.setdefault("preferences", {})
        preferences[key] = {"value": value, "timestamp": datetime.now().isoformat()}
        self._save_state()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        preferences = self.memory.get("preferences", {})
        pref = preferences.get(key)
        return pref["value"] if pref else default

    def set_reminder(self, context: str, action: str, trigger: str = "user_returns") -> str:
        """Set a future reminder."""
        reminder_id = hashlib.md5(f"{context}{datetime.now().isoformat()}".encode()).hexdigest()[:8]

        prospective = self.memory.setdefault("prospective", [])
        prospective.append({
            "id": reminder_id,
            "context": context,
            "action": action,
            "trigger": trigger,
            "created": datetime.now().isoformat(),
            "triggered": False
        })
        self._save_state()
        self.log(f"[MEMORY] Set reminder: {action[:50]}...")
        return reminder_id

    def get_pending_reminders(self) -> List[Dict]:
        """Get all reminders that haven't been triggered."""
        return [r for r in self.memory.get("prospective", []) if not r.get("triggered", False)]

    def mark_reminder_triggered(self, reminder_id: str):
        """Mark a reminder as triggered."""
        for r in self.memory.get("prospective", []):
            if r["id"] == reminder_id:
                r["triggered"] = True
                r["triggered_at"] = datetime.now().isoformat()
                break
        self._save_state()

    def add_prospective(self, reminder: str, context: str = ""):
        """Store a future-oriented reminder."""
        from datetime import datetime
        entry = {
            "reminder": reminder,
            "created": datetime.now().isoformat(),
            "context": context,
            "done": False
        }
        self.memory.setdefault("prospective", []).append(entry)
        self._save_state()
        if self.log:
            self.log(f"[MEMORY] 📌 Reminder stored: {reminder[:60]}")

    def get_pending_prospective(self) -> list:
        """Return all unfinished reminders."""
        return [e for e in self.memory.get("prospective", []) if not e.get("done")]

    def mark_prospective_done(self, index: int):
        """Mark a reminder as done by index."""
        items = self.memory.get("prospective", [])
        if 0 <= index < len(items):
            items[index]["done"] = True
            self._save_state()

    def get_stats(self) -> Dict:
        """Get memory statistics."""
        return {
            "facts": len(self.memory.get("semantic", {})),
            "patterns": len(self.memory.get("procedural", {})),
            "preferences": len(self.memory.get("preferences", {})),
            "pending_reminders": len(self.get_pending_reminders()),
            "indexed_keywords": len(self.memory.get("episodic_index", {}))
        }

    def store_semantic(self, key: str, value: str, confidence: float = 1.0):
        """Store a persistent fact about the user or environment."""
        self.memory.setdefault("semantic", {})[key] = {
            "value": value,
            "confidence": confidence,
            "updated": datetime.now().isoformat()
        }
        self._save_state()
        if self.log:
            self.log(f"[MEMORY] 📚 Semantic stored: {key} = {value}")

    def get_semantic_context(self) -> str:
        """Return all semantic facts as a formatted context string."""
        semantic = self.memory.get("semantic", {})
        if not semantic:
            return ""
        lines = ["KNOWN FACTS ABOUT USER:"]
        for key, entry in semantic.items():
            val = entry["value"] if isinstance(entry, dict) else entry
            lines.append(f"- {key}: {val}")
        return "\n".join(lines)
