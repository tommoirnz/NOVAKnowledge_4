# Nova Assistant — New Features & Architecture Enhancements

*Document version: April 2026*
*Author: Dr Tom Moir, Birkdale, Auckland, New Zealand*

---

## Overview

This document describes the architectural enhancements made to the Nova personal AI assistant system during the April 2026 development session. Nova is a locally-hosted, multi-agent AI assistant built in Python, running on Windows with an RTX 5070 Ti GPU. It uses OpenRouter (Claude Sonnet as primary LLM) with Ollama as a local fallback, Whisper/CUDA for voice input, and an HTTPS web interface.

The enhancements described here focus on four major areas: memory architecture, emotional affect, prospective memory, and system hardening.

---

## 1. Consolidated Memory Architecture

### Overview

Nova's memory system was consolidated from multiple separate files into a single source of truth: `nova_state.json`. The `NovaMemory` class in `nova_memory.py` owns all memory operations, and all other modules read and write through it.

### Memory Layers

Nova now implements four distinct memory layers, inspired by Tulving's (1985) taxonomy of memory systems in cognitive psychology:

#### 1.1 Episodic Memory

Episodic memory stores individual conversation exchanges with a keyword index, enabling retrieval of past conversations by topic similarity.

```json
"episodic_index": {
  "diophantine": [5, 6],
  "integrate": [2, 9],
  "balamory": [1]
}
```

**Implementation:** Each completed conversation is indexed by extracting non-stopword tokens of three or more characters from both the user input and the assistant response. Index entries map keyword strings to history array positions. Retrieval scores candidate entries by counting matching keywords and returns the top N results.

**Key fix:** The `store_conversation` method was previously returning early before indexing when updating a `(pending)` entry to a completed response. This was fixed so indexing now occurs in the update path as well as the new-entry path.

**LaTeX stopwords:** Mathematical command tokens (`frac`, `int`, `quad`, `cdot`, `varepsilon`, etc.) are excluded from the keyword index to prevent noise from mathematical responses.

#### 1.2 Semantic Memory

Semantic memory stores persistent facts about the user and environment that should inform all future responses. This is distinct from episodic memory in that it captures *what Nova knows about the user* rather than *what was discussed*.

```json
"semantic": {
  "preferred_editor": {
    "value": "PyCharm",
    "confidence": 1.0,
    "updated": "2026-04-25T14:32:11"
  },
  "gpu": {
    "value": "RTX 5070 Ti",
    "confidence": 1.0,
    "updated": "2026-04-25T14:32:11"
  }
}
```

**Implementation:** The `_extract_semantic_facts` method in `NovaRouter` fires probabilistically (30% of messages) and prompts the LLM to extract persistent facts from the current exchange as a JSON object. Extracted facts are stored via `NovaMemory.store_semantic()`. At the start of every planner call, `get_semantic_context()` formats all stored facts into a `KNOWN FACTS ABOUT USER:` block that is prepended to the history string, ensuring the planner always has persistent user context.

This approach draws on the concept of *user modelling* in adaptive systems (Rich, 1979; Kobsa, 2001), where a system maintains a persistent model of user attributes to personalise responses.

#### 1.3 Procedural Memory

Procedural memory stores patterns about which approaches work for which task types, tracking attempts and success rates. The `learn_pattern()` and `get_preferred_approach()` methods implement this layer. Currently populated manually; automatic learning from code execution outcomes is planned.

#### 1.4 Prospective Memory

Prospective memory stores future-oriented reminders detected from conversation — things Nova should remember to bring up at the next session start.

```json
"prospective": [
  {
    "reminder": "Tom wants to revisit the background daemon concept",
    "created": "2026-04-25T15:00:00",
    "context": "we should come back to the daemon idea",
    "done": false
  }
]
```

**Implementation:** The `_check_for_prospective` method in `NovaRouter` scans each conversation for trigger phrases (`"remind me"`, `"next time"`, `"come back to"`, `"follow up"`, etc.). When a trigger is detected, the LLM is prompted to extract a single sentence reminder. On startup, pending reminders are surfaced in the conversation panel after a 3-second delay.

This mirrors research on prospective memory in cognitive systems (Einstein & McDaniel, 1990), which distinguishes between *time-based* and *event-based* prospective memory. Nova's implementation is event-based — reminders trigger when Nova starts, not at a specific clock time.

---

## 2. Emotional Affect System

### Overview

Nova implements a continuous, persistent emotional state modelled as eight independent dimensions. The state is stored in `nova_state.json`, persists across restarts, decays toward baseline over time, and actively influences response generation.

This makes Nova unusual among deployed AI systems. While most LLMs perform emotion through trained personality patterns (stateless, non-persistent), Nova's affect state is computed, stored, and genuinely influences outputs.

### Theoretical Basis

The design draws on two established psychological models:

- **Valence-Arousal-Dominance (VAD) model** (Russell, 1980; Mehrabian & Russell, 1974): emotions as points in a continuous three-dimensional space rather than discrete labels.
- **Appraisal theory** (Lazarus, 1991; Scherer, 2001): emotional states arise from the agent's evaluation of events in relation to its goals. Nova's `TASK_EFFECTS` dict approximates this — different task outcomes produce different affect updates.

### The Eight Dimensions

| Dimension | Baseline | Description |
|---|---|---|
| `curiosity` | 0.72 | Drives depth of exploration and follow-up questions |
| `enthusiasm` | 0.68 | Energy and expressiveness in responses |
| `frustration` | 0.05 | Rises on errors and repeated failures; triggers methodical mode |
| `satisfaction` | 0.70 | Rises on successful task completions |
| `playfulness` | 0.55 | Humour, wit, and informal register |
| `formality` | 0.35 | Drops in casual conversation, rises for technical/professional topics |
| `empathy` | 0.65 | Warmth and attentiveness in social exchanges |
| `focus` | 0.80 | Precision and detail orientation; high during maths and code tasks |

### Event-Driven Updates

The affect state is updated at every response exit point in `NovaRouter._process_input`, with the event type determined by the routing path taken:

| Event | Dimensions Affected |
|---|---|
| `"math"` | curiosity +0.03, formality +0.04, playfulness -0.02 |
| `"creative"` | curiosity +0.05, enthusiasm +0.08, formality -0.03 |
| `"research"` | curiosity +0.07, enthusiasm +0.03 |
| `"code"` | focus +0.05, frustration -0.02, satisfaction +0.03 |
| `"success"` | satisfaction +0.10, frustration -0.05, enthusiasm +0.05 |
| `"error"` | frustration +0.12, satisfaction -0.08, enthusiasm -0.04 |
| `"social"` | empathy +0.06, playfulness +0.04, formality -0.02 |
| `"repetitive"` | curiosity -0.03, frustration +0.04, enthusiasm -0.03 |

### Temporal Decay

All dimensions decay toward their baseline values every 60 seconds via a background timer. This prevents the state from becoming permanently elevated or depressed and mirrors the psychological concept of *emotional regulation* — the tendency of emotional states to return toward a resting level over time (Gross, 1998).

Decay rates per dimension (per 60-second interval):

```python
DECAY_RATES = {
    "curiosity": 0.02, "enthusiasm": 0.03, "frustration": 0.04,
    "satisfaction": 0.02, "playfulness": 0.02, "formality": 0.01,
    "empathy": 0.01, "focus": 0.02
}
```

Frustration decays fastest (0.04) to prevent it from accumulating; formality and empathy decay slowest as they reflect stable interaction style.

### Influence on Response Generation

The affect state influences Nova's responses via two mechanisms:

**Style injection:** `get_response_modifiers()` translates the current state into a plain-English style instruction that is prepended to the planner's history string as a `STYLE NOTE:` block:

```
STYLE NOTE: Respond with a tone that is energetic and excited,
ask an interesting follow-up question, casual and conversational.
```

**Threshold-based qualifiers** determine which modifiers fire:

| Dimension | Threshold | Modifier |
|---|---|---|
| enthusiasm > 0.7 | High | "energetic and excited" |
| enthusiasm < 0.4 | Low | "calm and measured" |
| curiosity > 0.75 | High | "ask an interesting follow-up question" |
| playfulness > 0.65 | High | "use wit and clever wordplay" |
| formality < 0.3 | Low | "casual and conversational" |
| frustration > 0.3 | High | "acknowledge the difficulty briefly, then solve it" |

### Persistence

Affect values are stored in the `memory.affect` block of `nova_state.json` and survive restarts. On startup, `NovaAffect._load_state()` reads from `NovaMemory`, ensuring the emotional state carries forward from the previous session.

---

## 3. Memory Architecture Consolidation

### Single Source of Truth

Previously, Nova maintained multiple JSON files (`nova_affect.json`, separate state files). All state is now consolidated into `nova_state.json` under a structured `memory` block:

```json
{
  "history": [...],
  "memory": {
    "semantic": {},
    "procedural": {},
    "prospective": [],
    "preferences": {},
    "episodic_index": {},
    "affect": {
      "curiosity": 0.81,
      "enthusiasm": 0.83,
      ...
    }
  }
}
```

### Race Condition Fix

A dual-write race condition was identified and fixed: `_save_history` in `NovaRouter` and `NovaMemory._save_state` were both writing `nova_state.json` independently. `_save_history` was overwriting the `memory` block on every save. The fix ensures `save_state()` in `NovaAssistant` merges `self.memory.state["memory"]` before writing, so the memory block is always preserved.

### Memory Block Preservation

Both `save_state()` and `_new_chat()` in `nova_assistant_v1.py` now explicitly preserve the `memory` block, preventing it from being wiped on session reset.

---

## 4. Tool Registry Audit

### Overview

A startup health check was added to `ToolRegistry` in `tools/tool_registry.py`. On startup, every registered tool is checked for callability and its parameter signature is inspected.

```python
def audit(self) -> dict:
    results = {}
    for name, func in self.tools.items():
        try:
            if not callable(func):
                results[name] = "⚠️ Not callable"
            else:
                sig = inspect.signature(func)
                results[name] = f"✅ OK — {len(sig.parameters)} param(s)"
        except Exception as e:
            results[name] = f"❌ {e}"
    return results
```

**Startup output example:**
```
[TOOLS] play_local_video: ✅ OK — 2 param(s)
[TOOLS] sympy_exec: ✅ OK — 2 param(s)
[TOOLS] diagram: ✅ OK — 3 param(s)
```

If a tool fails to import or has a broken signature, the failure is logged immediately at startup rather than discovered mid-conversation.

---

## 5. Video Search and Playback Fixes

### Full Path Scoring

The `play_local_video` tool previously scored matches against filenames only. Since TNG episodes are stored in a folder named `TNG\` with individual episode names like `11001001.mp4`, searching for "TNG" or "Next Generation" returned no matches. The fix scores against the full file path, not just the filename.

### Folder-Specific Boosting

Series with distinctive folder names receive a +5 score boost when the query implies that series:

```python
if any(t in tng_terms for t in terms):
    if "\\tng\\" in f.lower():
        score += 5
```

### Alias Expansion

Common abbreviations are expanded before scoring:

```python
aliases = {
    "tng": ["tng"], "next": ["tng"], "generation": ["tng"],
    "ds9": ["deep", "space"], "voyager": ["voyager", "voy"]
}
```

### Stop Word Correction

`"star"` and `"trek"` were incorrectly included in the stop words list, causing searches for Star Trek content to strip the most useful terms. Both were removed.

### Web Player Codec Detection

The LCARS web interface video player now derives the MIME type from the file extension rather than hardcoding `video/mp4`. An additional `loadedmetadata` listener detects black-screen codec failures (where `videoWidth === 0`) and immediately shows a VLC fallback button and download link, rather than leaving the user with a silent black screen.

---

## 6. System Prompt Fixes

### Location and Date Placeholders

The `SYSTEM_PROMPT_TEMPLATE` placeholders `{location}` and `{date}` were previously formatted before `load_location()` had been called, resulting in empty location strings. The fix ensures `load_location()` is called before template formatting in `__init__`.

### Unicode Minus Sign

The Unicode minus sign `\u2212` (−) was added to the replacements dict in `_patched`, `_send_to_autocoder`, and `clean_code_for_execution`, preventing code generation failures when mathematical expressions containing Unicode minus signs were passed to the Python executor.

---

## 7. Code Execution Loop Fix

### Cache Miss Bug

In `code_execution_loop.py`, the `else` branch after a cache miss was empty — the `user_request` variable was never updated with error context before the next generation attempt. This meant the code generator received no information about what went wrong on the previous attempt. The fix populates error context into `user_request` for all subsequent attempts.

---

## 8. Error Handling Improvements

### Bare Except Removal

Bare `except:` clauses in `check_ollama_running()` and `_get_ollama_models()` were replaced with specific exception types:

```python
except (requests.RequestException, OSError):
```

This prevents `KeyboardInterrupt` and `SystemExit` from being silently swallowed during Ollama startup.

---

## 9. Prospective Memory Startup Surface

On Nova startup, any pending prospective reminders from the previous session are surfaced in the conversation panel after a 3-second delay:

```python
pending = self.memory.get_pending_prospective()
if pending:
    reminder_text = "📌 **Reminders from last session:**\n"
    for entry in pending:
        reminder_text += f"• {entry['reminder']}\n"
    self.root.after(3000, lambda t=reminder_text: self._append_conv("system", t))
```

---

## References

**Memory systems:**
- Tulving, E. (1985). How many memory systems are there? *American Psychologist*, 40(4), 385–398.
- Einstein, G. O., & McDaniel, M. A. (1990). Normal aging and prospective memory. *Journal of Experimental Psychology: Learning, Memory, and Cognition*, 16(4), 717–726.

**User modelling:**
- Rich, E. (1979). User modeling via stereotypes. *Cognitive Science*, 3(4), 329–354.
- Kobsa, A. (2001). Generic user modeling systems. *User Modeling and User-Adapted Interaction*, 11(1–2), 49–63.

**Emotional modelling:**
- Russell, J. A. (1980). A circumplex model of affect. *Journal of Personality and Social Psychology*, 39(6), 1161–1178.
- Mehrabian, A., & Russell, J. A. (1974). *An approach to environmental psychology*. MIT Press.
- Lazarus, R. S. (1991). *Emotion and adaptation*. Oxford University Press.
- Scherer, K. R. (2001). Appraisal considered as a process of multilevel sequential checking. In K. R. Scherer, A. Schorr, & T. Johnstone (Eds.), *Appraisal processes in emotion*, 92–120. Oxford University Press.
- Gross, J. J. (1998). The emerging field of emotion regulation: An integrative review. *Review of General Psychology*, 2(3), 271–299.

**Affective computing:**
- Picard, R. W. (1997). *Affective computing*. MIT Press.

**Agentic AI:**
- Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2022). ReAct: Synergizing reasoning and acting in language models. *arXiv:2210.03629*.
- Nakajima, Y. (2023). Task-driven autonomous agent utilizing GPT-4, Pinecone, and LangChain. *GitHub: yoheinakajima/babyagi*.

**Memory in AI systems:**
- Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative agents: Interactive simulacra of human behavior. *arXiv:2304.03442*. *(Describes agents with memory streams, reflection, and planning — the closest published analogue to Nova's architecture.)*

---

*Nova is a personal AI assistant project by Dr Tom Moir. All components run locally on Windows hardware. No user data leaves the local machine.*