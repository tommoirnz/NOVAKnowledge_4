"""
nova_affect.py — Emotional State Engine for Nova Assistant
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional


class NovaAffect:
    """Continuous emotional state for Nova."""

    DEFAULT_STATE = {
        "curiosity": 0.72,
        "enthusiasm": 0.68,
        "frustration": 0.05,
        "satisfaction": 0.70,
        "playfulness": 0.55,
        "formality": 0.35,
        "empathy": 0.65,
        "focus": 0.80,
    }

    TASK_EFFECTS = {
        "creative": {"curiosity": +0.05, "enthusiasm": +0.08, "formality": -0.03},
        "math": {"curiosity": +0.03, "formality": +0.04, "playfulness": -0.02},
        "code": {"focus": +0.05, "frustration": -0.02, "satisfaction": +0.03},
        "research": {"curiosity": +0.07, "enthusiasm": +0.03},
        "error": {"frustration": +0.12, "satisfaction": -0.08, "enthusiasm": -0.04},
        "success": {"satisfaction": +0.10, "frustration": -0.05, "enthusiasm": +0.05},
        "repetitive": {"curiosity": -0.03, "frustration": +0.04, "enthusiasm": -0.03},
        "social": {"empathy": +0.06, "playfulness": +0.04, "formality": -0.02},
    }

    DECAY_RATES = {
        "curiosity": 0.02, "enthusiasm": 0.03, "frustration": 0.04,
        "satisfaction": 0.02, "playfulness": 0.02, "formality": 0.01,
        "empathy": 0.01, "focus": 0.02,
    }

    def __init__(self, memory=None, affect_dir: str = "./nova_memory"):
        self._memory = memory
        if memory is None:
            os.makedirs(affect_dir, exist_ok=True)
            self.affect_path = os.path.join(affect_dir, "affect_state.json")
        else:
            self.affect_path = None
        self.state = self._load_state()
        self.log = print
        self.recent_events = []
        self._save_state()

    def _load_state(self) -> Dict[str, float]:
        if self._memory:
            data = self._memory.memory.get("affect", {})
            if data:
                for key, default in self.DEFAULT_STATE.items():
                    if key not in data:
                        data[key] = default
                return data
            return self.DEFAULT_STATE.copy()
        if self.affect_path and os.path.exists(self.affect_path):
            try:
                with open(self.affect_path, "r") as f:
                    data = json.load(f)
                    if "state" in data:
                        data = data["state"]
                    for key, default in self.DEFAULT_STATE.items():
                        if key not in data:
                            data[key] = default
                    return data
            except Exception:
                pass
        return self.DEFAULT_STATE.copy()

    def _save_state(self):
        if self._memory:
            self._memory.memory["affect"] = self.state.copy()
            self._memory._save_state()
            return
        if self.affect_path:
            try:
                with open(self.affect_path, "w") as f:
                    json.dump({
                        "state": self.state,
                        "last_updated": datetime.now().isoformat()
                    }, f, indent=2)
            except Exception as e:
                self.log(f"[AFFECT] Failed to save: {e}")

    def set_logger(self, log_func):
        self.log = log_func

    def update(self, event_type: str, magnitude: float = 1.0, metadata: Dict = None):
        """Update affect state based on an event."""
        effects = self.TASK_EFFECTS.get(event_type, {})
        if not effects:
            return
        self.log(f"[AFFECT] {event_type} → {effects}")

        for trait, delta in effects.items():
            change = delta * magnitude
            new_value = self.state[trait] + change
            self.state[trait] = max(0.0, min(1.0, new_value))

        self.recent_events.append({
            "type": event_type,
            "magnitude": magnitude,
            "timestamp": datetime.now().isoformat(),
            "state_snapshot": self.state.copy()
        })
        if len(self.recent_events) > 100:
            self.recent_events = self.recent_events[-100:]

        self._save_state()
        self.log(f"[AFFECT] Updated via {event_type}")

    def decay(self):
        """Apply natural decay toward baseline."""
        changed = False
        for trait, current in self.state.items():
            baseline = self.DEFAULT_STATE[trait]
            rate = self.DECAY_RATES.get(trait, 0.02)

            if current > baseline:
                new_val = max(baseline, current - rate)
                if new_val != current:
                    self.state[trait] = new_val
                    changed = True
            elif current < baseline:
                new_val = min(baseline, current + rate)
                if new_val != current:
                    self.state[trait] = new_val
                    changed = True

        if changed:
            self._save_state()

    def get_response_modifiers(self) -> Dict[str, Any]:
        """Get modifiers to apply to response generation."""
        modifiers = []

        if self.state["enthusiasm"] > 0.7:
            modifiers.append("energetic and excited")
        elif self.state["enthusiasm"] < 0.4:
            modifiers.append("calm and measured")

        if self.state["curiosity"] > 0.75:
            modifiers.append("ask an interesting follow-up question")
        elif self.state["curiosity"] < 0.4:
            modifiers.append("be direct and focused")

        if self.state["playfulness"] > 0.65:
            modifiers.append("use wit and clever wordplay")
        elif self.state["playfulness"] < 0.35:
            modifiers.append("avoid humour, be straightforward")

        if self.state["formality"] > 0.6:
            modifiers.append("professional and precise")
        elif self.state["formality"] < 0.3:
            modifiers.append("casual and conversational")

        if self.state["frustration"] > 0.3:
            modifiers.append("acknowledge the difficulty briefly, then solve it")

        if self.state["empathy"] > 0.7:
            modifiers.append("warm and supportive")

        modifier_text = f"Respond with a tone that is {', '.join(modifiers)}." if modifiers else ""

        return {
            "style_modifiers": modifier_text,
            "should_explore": self.state["curiosity"] > 0.6,
            "should_be_witty": self.state["playfulness"] > 0.6,
        }

    def enhance_prompt(self, base_prompt: str) -> str:
        """Enhance a prompt with affect-driven instructions."""
        mods = self.get_response_modifiers()
        if mods["style_modifiers"]:
            return f"{base_prompt}\n\nSTYLE NOTE: {mods['style_modifiers']}"
        return base_prompt

    def get_emotional_expression(self) -> Optional[str]:
        """Generate a natural language expression of current affect."""
        if self.state["enthusiasm"] > 0.8:
            return "I'm genuinely excited about this!"
        elif self.state["curiosity"] > 0.8:
            return "That's really interesting — I want to dig into this."
        elif self.state["frustration"] > 0.4:
            return "This is tricky, but I'm working through it."
        elif self.state["satisfaction"] > 0.8:
            return "I'm pleased with how that turned out."
        elif self.state["playfulness"] > 0.7:
            return "Let me have some fun with this..."
        return None

    def get_state(self) -> Dict[str, float]:
        return self.state.copy()

    def get_stats(self) -> Dict:
        return {
            "current_state": self.state.copy(),
            "recent_events": len(self.recent_events)
        }