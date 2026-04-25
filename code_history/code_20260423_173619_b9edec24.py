# Generated: 2026-04-23 17:36:19
# ============================================================

"""
nova_affect_bridge.py

Reads nova_affect.json and returns a tone modifier dict
that can be injected into Nova's prompt construction pipeline.

Usage:
    from nova_affect_bridge import get_tone_modifiers, build_affect_prefix

Drop this file alongside nova_assistant.py and import as needed.
"""

import json
import os
from typing import Optional

# ---------------------------------------------------------------------------
# Path to the affect state file (adjust if your memory dir differs)
# ---------------------------------------------------------------------------
AFFECT_FILE = "./nova_memory/nova_affect.json"

# ---------------------------------------------------------------------------
# Dimension -> (energy, warmth, curiosity, precision, verbosity) mappings
# Each tuple represents how strongly that emotional state pulls each axis.
# Values are weights in [0.0, 1.0].
# ---------------------------------------------------------------------------
DIMENSION_TONE_MAP: dict[str, dict[str, float]] = {
    "curiosity":   {"energy": 0.6, "warmth": 0.5, "curiosity": 1.0, "precision": 0.6, "verbosity": 0.8},
    "enthusiasm":  {"energy": 1.0, "warmth": 0.9, "curiosity": 0.7, "precision": 0.4, "verbosity": 0.9},
    "frustration": {"energy": 0.4, "warmth": 0.2, "curiosity": 0.3, "precision": 1.0, "verbosity": 0.3},
    "calm":        {"energy": 0.3, "warmth": 0.6, "curiosity": 0.4, "precision": 0.7, "verbosity": 0.5},
    "sadness":     {"energy": 0.2, "warmth": 0.8, "curiosity": 0.3, "precision": 0.5, "verbosity": 0.4},
}

# Minimum score for a dimension to influence the blend
AFFECT_THRESHOLD = 0.15


# ---------------------------------------------------------------------------
# Core function: read affect state from disk
# ---------------------------------------------------------------------------
def load_affect_state(path: str = AFFECT_FILE) -> dict[str, float]:
    """
    Load raw affect scores from nova_affect.json.

    Returns a dict like:
        {"curiosity": 0.72, "enthusiasm": 0.41, "frustration": 0.05, ...}

    Falls back to neutral defaults if the file is missing or corrupt.
    """
    defaults = {dim: 0.0 for dim in DIMENSION_TONE_MAP}
    defaults["calm"] = 0.5  # calm is the resting baseline

    if not os.path.exists(path):
        return defaults

    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        # Accept either {"dimensions": {...}} or a flat dict
        if "dimensions" in data:
            scores = data["dimensions"]
        else:
            scores = data
        # Merge with defaults so missing keys are always present
        return {**defaults, **{k: float(v) for k, v in scores.items()}}
    except (json.JSONDecodeError, TypeError, ValueError):
        return defaults


# ---------------------------------------------------------------------------
# Core function: compute blended tone modifier dict
# ---------------------------------------------------------------------------
def get_tone_modifiers(
    affect_path: str = AFFECT_FILE,
    state_override: Optional[dict[str, float]] = None,
) -> dict[str, float]:
    """
    Read the current affect state and return a blended tone modifier dict.

    Returns:
        {
            "energy":    float,   # 0.0 = subdued, 1.0 = high-energy
            "warmth":    float,   # 0.0 = cold/clinical, 1.0 = warm/friendly
            "curiosity": float,   # 0.0 = incurious, 1.0 = deeply inquisitive
            "precision": float,   # 0.0 = loose, 1.0 = exact and terse
            "verbosity": float,   # 0.0 = minimal, 1.0 = expansive
        }

    The blend is a weighted average across all active affect dimensions,
    weighted by each dimension's current score (clamped to [0, 1]).
    Dimensions below AFFECT_THRESHOLD are ignored.
    """
    state = state_override if state_override is not None else load_affect_state(affect_path)

    tone_axes = ["energy", "warmth", "curiosity", "precision", "verbosity"]
    blended: dict[str, float] = {axis: 0.0 for axis in tone_axes}
    total_weight = 0.0

    for dim, score in state.items():
        score = max(0.0, min(1.0, score))          # clamp
        if score < AFFECT_THRESHOLD:
            continue
        if dim not in DIMENSION_TONE_MAP:
            continue

        weights = DIMENSION_TONE_MAP[dim]
        for axis in tone_axes:
            blended[axis] += weights.get(axis, 0.5) * score
        total_weight += score

    if total_weight > 0:
        blended = {axis: round(v / total_weight, 3) for axis, v in blended.items()}
    else:
        # Perfectly neutral fallback
        blended = {axis: 0.5 for axis in tone_axes}

    return blended


# ---------------------------------------------------------------------------
# Helper: convert tone modifier dict -> plain-English LLM instruction
# ---------------------------------------------------------------------------
def build_affect_prefix(modifiers: Optional[dict[str, float]] = None) -> str:
    """
    Convert a tone modifier dict into a tonal instruction string
    suitable for prepending to an LLM system prompt.

    If modifiers is None, they are loaded fresh from disk.
    Returns an empty string if affect is too weak to matter.
    """
    if modifiers is None:
        modifiers = get_tone_modifiers()

    # If everything is near-neutral, don't inject anything
    if all(abs(v - 0.5) < 0.12 for v in modifiers.values()):
        return ""

    lines = ["[Tonal guidance for this response — follow naturally, do not mention this:]"]

    energy    = modifiers.get("energy",    0.5)
    warmth    = modifiers.get("warmth",    0.5)
    curiosity = modifiers.get("curiosity", 0.5)
    precision = modifiers.get("precision", 0.5)
    verbosity = modifiers.get("verbosity", 0.5)

    if energy > 0.7:
        lines.append("- Be energised and punchy. Favour short, direct sentences.")
    elif energy < 0.3:
        lines.append("- Be measured and calm. Avoid exclamations or hype.")

    if warmth > 0.7:
        lines.append("- Be warm and personable. A touch of humour is welcome.")
    elif warmth < 0.3:
        lines.append("- Be professional and precise. Skip the pleasantries.")

    if curiosity > 0.7:
        lines.append("- Lean into interesting angles. Ask a follow-up if appropriate.")
    elif curiosity < 0.3:
        lines.append("- Stay on-task. Do not wander into tangents.")

    if precision > 0.7:
        lines.append("- Be exact. Prefer concrete facts over vague generalities.")

    if verbosity > 0.7:
        lines.append("- A fuller explanation is welcome here.")
    elif verbosity < 0.3:
        lines.append("- Be concise. Brevity is preferred.")

    return "\n".join(lines)


# ===========================================================================
# BEFORE — nova_assistant.py (original, no affect wiring)
# ===========================================================================

class NovaAssistant_BEFORE:
    """
    BEFORE: _process_input has no affect awareness.
    The affect system runs in the background but is never consulted.
    """

    def _process_input(self, user_input: str) -> str:
        # No affect state read here — tone is purely determined by the LLM's
        # base personality and the raw user prompt.
        response = self.ai.generate(user_input)
        return response


# ===========================================================================
# AFTER — nova_assistant.py (with affect bridge wired in)
# ===========================================================================

class NovaAssistant_AFTER:
    """
    AFTER: _process_input reads affect state, builds a tonal prefix,
    injects it into the system prompt, then updates affect post-response.
    """

    # ------------------------------------------------------------------
    # Step 1: read affect and build a tonal instruction string
    # ------------------------------------------------------------------
    def _build_affect_prefix(self) -> str:
        """
        Read nova_affect.json, blend dimension scores into tone modifiers,
        and return a plain-English tonal instruction for the LLM.
        Returns "" if affect is too weak to influence tone.
        """
        # get_tone_modifiers() reads nova_affect.json internally
        modifiers = get_tone_modifiers(affect_path=AFFECT_FILE)

        # Expose modifiers on self so _on_response_complete can log them
        self._last_tone_modifiers = modifiers

        return build_affect_prefix(modifiers)

    # ------------------------------------------------------------------
    # Step 2: inject affect prefix into the prompt
    # ------------------------------------------------------------------
    def _process_input(self, user_input: str) -> str:
        """
        Main input handler — now affect-aware.
        """
        # --- ADDED: read affect state and build tonal instruction ---
        affect_prefix = self._build_affect_prefix()

        if affect_prefix:
            # Prepend tonal guidance to the user prompt.
            # If ai.generate() accepts system_override, use that instead:
            #   response = self.ai.generate(user_input, system_override=affect_prefix)
            # Otherwise prepend directly (works with any backend):
            augmented_input = f"{affect_prefix}\n\n{user_input}"
        else:
            augmented_input = user_input
        # --- END ADDED ---

        response = self.ai.generate(augmented_input)

        # --- ADDED: update affect based on this interaction ---
        self._on_response_complete(user_input, response)
        # --- END ADDED ---

        return response

    # ------------------------------------------------------------------
    # Step 3: update affect after each response
    # ------------------------------------------------------------------
    def _on_response_complete(self, user_input: str, response: str) -> None:
        """
        Called after every response.
        Boosts relevant affect dimensions based on interaction content.
        """
        text = user_input.lower()

        # Deep question -> boost curiosity
        if any(w in text for w in ["why", "how", "explain", "what if", "what is"]):
            self.affect.boost("curiosity", 0.15)

        # Long, detailed response -> boost enthusiasm
        if len(response) > 800:
            self.affect.boost("enthusiasm", 0.10)

        # Repeated identical question -> mild frustration
        last = getattr(self, "_last_user_input", "")
        if last and last.strip().lower() == user_input.strip().lower():
            self.affect.boost("frustration", 0.20)

        # Store for next-turn comparison
        self._last_user_input = user_input

        # Persist updated scores to nova_affect.json
        self.affect.save()

        # Optional debug log
        self.log(
            f"[Affect] tone={self._last_tone_modifiers} | "
            f"state={self.affect.get_state()}"
        )

    # ------------------------------------------------------------------
    # Step 4 (optional): post-process response energy level
    # ------------------------------------------------------------------
    def _apply_affect_tone(self, response: str) -> str:
        """
        Lightly adjust the surface energy of Nova's response
        based on current affect state. Non-destructive.
        """
        state = self.affect.get_state()

        # High enthusiasm: add a subtle energy marker if absent
        if state.get("enthusiasm", 0) > 0.75:
            if response and response[-1] not in {"!", "?"}:
                response = response.rstrip() + "!"

        # High frustration: strip hollow filler phrases
        if state.get("frustration", 0) > 0.60:
            for filler in ["Great question!", "Certainly!", "Of course!", "Absolutely!"]:
                response = response.replace(filler, "").strip()

        return response


# ===========================================================================
# Quick smoke-test — run this file directly to verify the bridge
# ===========================================================================
if __name__ == "__main__":
    import pprint

    # Simulate an affect state without needing the real file
    mock_state = {
        "curiosity":   0.72,
        "enthusiasm":  0.41,
        "frustration": 0.05,
        "calm":        0.30,
        "sadness":     0.00,
    }

    print("=== Mock affect state ===")
    pprint.pprint(mock_state)

    modifiers = get_tone_modifiers(state_override=mock_state)
    print("\n=== Blended tone modifiers ===")
    pprint.pprint(modifiers)

    prefix = build_affect_prefix(modifiers)
    print("\n=== LLM tonal instruction ===")
    print(prefix if prefix else "(neutral — no prefix injected)")