"""
nova_router.py — Request routing mixin for Nova Assistant.

Contains NovaRouter: all input processing, intent classification,
planner invocation, ReAct agent handling, and internet search logic.

Usage:
    from nova_router import NovaRouter

    class NovaAssistant(NovaTTS, NovaSelfImproveUI, NovaRouter):
        ...
"""

import re
import threading
from nova_memory import NovaMemory

class NovaRouter:
    """Mixin that handles all user input routing and response generation."""

    # ──────────────────────────────────────────────────────────────────────────
    # MAIN ROUTER
    # ──────────────────────────────────────────────────────────────────────────

    def _process_input(self, user_input):
        """Main router — planner-first architecture."""
        try:
            # ── NEW: Store user input in memory ──
            if hasattr(self, 'memory'):
                self.memory.store_conversation(user_input, "(pending)")

            text = (user_input or "").strip().lower()

            # ── Safe state access ─────────────────────
            last_task_raw = self.state.get("last_task")
            last_result = self.state.get("last_result") or ""
            last_task = (last_task_raw or "").strip().lower()

            # ── Cache hit ─────────────────────────────
            if last_task and text and text == last_task:
                print("[CACHE] HIT")
                self._append_conv("assistant", last_result)
                return

            # ── Follow-ups ────────────────────────────
            if text in ["repeat", "do that again", "run again"]:
                user_input = self.state.get("last_task") or user_input

            if "result" in text and "what" in text:
                numbers = re.findall(r"\b\d+(?:\.\d+)?\b", last_result)
                self._append_conv("assistant", numbers[-1] if numbers else last_result)
                return

            if "open it" in text and "http" in str(last_result):
                self._append_conv("assistant", str(self.tools.run("open_webpage", last_result)))
                return

            follow_up_phrases = ["result", "answer", "repeat", "again", "open it"]
            is_follow_up = any(p in text for p in follow_up_phrases)

            # ── Location query ────────────────────────
            location_phrases = [
                "where am i", "what city am i", "my location",
                "where are we", "what country am i", "where is this",
                "what is my location", "what's my location",
                "where are you", "where do you think i am",
                "what location", "where in the world"
            ]
            if any(p in text for p in location_phrases):
                env = self.get_environment()
                answer = (
                    f"You're in {env.get('suburb') or ''} {env.get('city')}, "
                    f"{env.get('region')}, {env.get('country')}. "
                    f"Coordinates: {env.get('lat')}, {env.get('lon')}."
                )
                self._append_conv("assistant", answer.strip())
                self.conversation_history.append({"role": "assistant", "content": answer})
                self.speak_text(answer)
                if hasattr(self, 'memory'):
                    self.memory.store_conversation(user_input, answer)
                if hasattr(self, 'affect'):
                    self.affect.update("social")
                return

            # ── History commands ──────────────────────
            if "last two" in text:
                history = self.state.get("history", [])[-20:]
                if not history:
                    self._append_conv("assistant", "I don't have any previous responses yet.")
                    return
                output = "Here are your last responses:\n\n"
                for i, item in enumerate(history, 1):
                    output += f"{i}. You asked: \"{item.get('task', '')}\"\n"
                    output += f"{item.get('result', '').strip()}\n\n"
                self._append_conv("assistant", output.strip())
                if hasattr(self, 'memory'):
                    self.memory.store_conversation(user_input, output)
                return

            # ── State context ─────────────────────────
            state_context = (
                f"Last task: {self.state.get('last_task')}\n"
                f"Last result: {self.state.get('last_result')}\n"
                f"Recent history: {self.state.get('history', [])[-20:]}"
            )

            # ── BUILD FULL HISTORY FROM STATE ──
            full_history_str = self._build_full_history_string()
            self.log(f"[HISTORY] Loaded {len(full_history_str)} chars of history from state")

            # ── ReAct trigger ─────────────────────────
            if self._is_react_trigger(user_input):
                result = self._handle_react(user_input + "\n\n" + state_context, full_history_str)
                raw_output = result.get("final") if isinstance(result, dict) else result
                final_result = (raw_output if getattr(self, "debug_mode", False)
                                else self.process_agent_response(raw_output, {
                    "user_input": user_input, "history": full_history_str}))

                self._append_conv("assistant", final_result)
                self.conversation_history.append({"role": "assistant", "content": final_result})
                self.speak_text(final_result)
                if hasattr(self, 'memory'):
                    self.memory.store_conversation(user_input, final_result)
                if not is_follow_up:
                    self.state["last_task"] = user_input
                self.state["last_result"] = final_result
                self.state["last_type"] = "react"
                self._save_history(user_input, final_result)
                if hasattr(self, 'affect'):
                    self.affect.update("research")
                self._check_for_prospective(user_input, final_result)
                self._extract_semantic_facts(user_input, final_result)
                return

            # ── Simple vs complex ─────────────────────
            info_keywords = ["weather", "news", "time", "price", "stock"]
            tool_keywords = ["list", "find", "open", "play", "search"]
            plot_keywords = ["plot", "graph", "chart"]
            is_tool_like = any(k in text for k in tool_keywords)
            is_plot = any(k in text for k in plot_keywords)
            is_simple = (
                    len((user_input or "").split()) < 4 and
                    not any(k in text for k in info_keywords) and
                    not is_tool_like and not is_plot
            )

            internet_ctx = ""
            if not is_simple:
                internet_ctx, _ = self._handle_internet_search_nonblocking(user_input, full_history_str)

            # ── Compound image+make → planner ─────────
            compound_image_kw = ["download", "find", "get", "search for"]
            compound_make_kw = ["poster", "collage", "layout", "make", "create", "build",
                                "combine", "arrange", "design", "put", "place", "display",
                                "cube", "sphere", "slideshow", "gallery", "animate", "rotating"]
            image_words = ["picture", "pictures", "image", "images", "photo", "photos"]

            if (any(w in text for w in compound_image_kw) and
                    any(w in text for w in image_words) and
                    any(w in text for w in compound_make_kw)):
                self.log("[ROUTER] Compound image+make request → planner")
                handled = self._handle_planner(user_input, full_history_str, internet_ctx)
                if handled:
                    self._append_conv("assistant", handled)
                    self.conversation_history.append({"role": "assistant", "content": handled})
                    self.speak_text(handled)
                    self._maybe_render_latex(handled)
                    self.state["last_result"] = handled
                    self.state["last_type"] = "planner"
                    self._save_history(user_input, handled)
                    if hasattr(self, 'affect'):
                        self.affect.update("creative")
                    if hasattr(self, 'memory'):
                        self.memory.store_conversation(user_input, handled)
                    self._check_for_prospective(user_input, handled)
                    self._extract_semantic_facts(user_input, handled)
                return

            # ── Tool ──────────────────────────────────
            tool_result = self.try_tool(user_input)
            if tool_result:
                self._deliver_tool_result(tool_result)
                if not is_follow_up:
                    self.state["last_task"] = user_input
                self.state["last_result"] = tool_result
                self.state["last_type"] = "tool"
                self._save_history(user_input, tool_result)
                if hasattr(self, 'affect'):
                    self.affect.update("success")
                if hasattr(self, 'memory'):
                    self.memory.store_conversation(user_input, str(tool_result)[:1000])
                self._check_for_prospective(user_input, str(tool_result))
                self._extract_semantic_facts(user_input, str(tool_result))
                return

            # ── Planner ───────────────────────────────
            if not is_simple:
                self.log("[PLANNER] Primary decision-maker")
                handled = self._handle_planner(user_input, full_history_str, internet_ctx)
                self.log(f"[PLANNER RETURNED] {handled}")

                if handled:
                    if hasattr(self, "_last_results") and self._last_results:
                        last = (self._last_results[-1]
                                if isinstance(self._last_results, list)
                                else self._last_results)
                        if isinstance(last, str) and last.startswith("IMAGE_GRID:"):
                            self._append_conv("assistant", last)
                            self.conversation_history.append({"role": "assistant", "content": last})
                            if hasattr(self, 'affect'):
                                self.affect.update("creative")
                            if hasattr(self, 'memory'):
                                self.memory.store_conversation(user_input, last)
                            self._check_for_prospective(user_input, last)
                            self._extract_semantic_facts(user_input, last)
                            return

                    self._append_conv("assistant", handled)
                    self.conversation_history.append({"role": "assistant", "content": handled})
                    self.speak_text(handled)
                    self._maybe_render_latex(handled)
                    self.state["last_result"] = handled
                    self.state["last_type"] = "planner"
                    self._save_history(user_input, handled)
                    if hasattr(self, 'affect'):
                        if any(k in text for k in ["integrate", "solve", "derive", "calculate",
                                                   "equation", "proof", "differentiate"]):
                            self.affect.update("math")
                        elif any(k in text for k in ["search", "find", "news", "weather",
                                                     "research", "latest", "current"]):
                            self.affect.update("research")
                        else:
                            self.affect.update("creative")
                    if hasattr(self, 'memory'):
                        self.memory.store_conversation(user_input, handled)
                    self._check_for_prospective(user_input, handled)
                    self._extract_semantic_facts(user_input, handled)
                    return

            # ── Final AI fallback ─────────────────────
            final = self.ai.generate(state_context + "\n\nUser:\n" + str(user_input)) or \
                    "No response generated."

            self._append_conv("assistant", final)
            self.conversation_history.append({"role": "assistant", "content": final})
            if hasattr(self, 'memory'):
                self.memory.store_conversation(user_input, final)
            if not is_follow_up:
                self.state["last_task"] = user_input
            self.state["last_result"] = final
            self.state["last_type"] = "final"
            self._save_history(user_input, final)
            if hasattr(self, 'affect'):
                self.affect.update("social")
            self._check_for_prospective(user_input, final)
            self._extract_semantic_facts(user_input, final)
            self.speak_text(final)
            self._maybe_render_latex(final)

        except Exception as e:
            self.log(f"[ERROR] _process_input: {e}")
            self._append_conv("assistant", f"I encountered an error: {e}")

        finally:
            self._thinking = False
            self._dot_cycle = self._dot_generator()
            self.root.after(0, self._stop_nova_flash)
            self.root.after(0, lambda: self._draw_send_btn(False))

    def _build_full_history_string(self):
        """Build a complete history string from state for planner/agents."""
        try:
            if not hasattr(self, 'state') or 'history' not in self.state:
                self.log("[HISTORY] No history in state")
                return ""

            history = self.state.get('history', [])
            if not history:
                self.log("[HISTORY] History array is empty")
                return ""

            self.log(f"[HISTORY] Building from {len(history)} entries")

            formatted = []
            for entry in history[-100:]:  # Last 100 exchanges
                task = entry.get('task', '')
                result = entry.get('result', '')
                # Truncate long results
                if len(result) > 500:
                    result = result[:500] + "..."
                formatted.append(f"User: {task}\nAssistant: {result}")

            result = "\n\n".join(formatted)
            self.log(f"[HISTORY] Built string length: {len(result)}")
            return result

        except Exception as e:
            self.log(f"[ERROR] _build_full_history_string: {e}")
            import traceback
            self.log(traceback.format_exc())
            return ""

    def _save_history(self, user_input, result):
        """Update state and persist — NovaMemory handles its own indexing."""
        self.state.setdefault("history", []).append({
            "task": user_input,
            "result": str(result)[:1000]
        })
        self.state["history"] = self.state["history"][-200:]
        self.save_state()  # save_state now preserves memory block

    # ──────────────────────────────────────────────────────────────────────────
    # REACT
    # ──────────────────────────────────────────────────────────────────────────

    def _handle_react(self, user_input, history_str):
        """Run the ReAct agent loop and return its response string."""
        self.log("[AGENT] ReAct reasoning engaged")
        return self.ai.react_agent(
            user_prompt=user_input,
            history=history_str,
            tools=self.ai.internet,
            internet_ctx=""
        ) or "I couldn't complete that request."

    def _is_react_trigger(self, user_input):
        """Return True if the input looks like a URL, DOI, arXiv ID, or PDF reference."""
        t = user_input.lower()
        return (
            "http" in t or "www" in t or
            "research paper" in t or "arxiv" in t or ".pdf" in t or
            re.search(r"\b\d{4}\.\d{4,5}\b", user_input) or
            re.search(r"https?://", user_input)
        )

    def process_agent_response(self, raw_response, context):
        """Clean and stabilise ReAct agent output, extracting the final answer."""
        if not raw_response:
            return ""

        final_match  = re.search(r"Final:\s*(.*)", raw_response, re.IGNORECASE | re.DOTALL)
        final_answer = final_match.group(1).strip() if final_match else ""

        observations = re.findall(r"Observation:\s*(.*)", raw_response, re.IGNORECASE)
        if final_answer and observations:
            for obs in observations:
                obs_lower = obs.lower()
                if "error" in obs_lower:
                    return "The task encountered an error and could not be completed."
                if "not found" in obs_lower and not final_answer:
                    return "The requested information was not found."

        if not final_answer:
            lines = [l.strip() for l in raw_response.splitlines() if l.strip()]
            for line in reversed(lines):
                if not any(x in line.lower() for x in ["thought:", "action:", "observation:"]):
                    final_answer = line
                    break

        final_answer = re.sub(r"\(.*?date.*?\)",   "", final_answer, flags=re.IGNORECASE)
        final_answer = re.sub(r"\(.*?future.*?\)", "", final_answer, flags=re.IGNORECASE)
        final_answer = re.sub(r"\n{2,}", "\n", final_answer)
        return final_answer.strip()

    # ──────────────────────────────────────────────────────────────────────────
    # INTERNET SEARCH
    # ──────────────────────────────────────────────────────────────────────────

    def _handle_internet_search_nonblocking(self, user_input, history_str):
        """Generate a search query, run it, and return (context_str, did_search)."""
        import inspect
        caller = inspect.stack()[1]
        self.log(f"[DEBUG] INTERNET CALLED BY → {caller.function} (line {caller.lineno})")

        try:
            raw = self.ai.generate(
                f"""Generate a precise search query for this task.

User request: {user_input}

Rules:
- Return ONLY the search query — no labels, no quotes, no markdown
- If not needed, return SKIP
- Return SKIP for: historical facts, definitions, well-known people,
  scientific concepts, anything that doesn't change over time
- Only search for: current prices, live data, recent news,
  today's events, real-time information

If in doubt, return SKIP.""",
                use_planning=False
            ).strip()

            if raw.upper() == "SKIP" or not raw:
                return "", False

            raw = re.sub(r"\*+", "", raw)
            raw = re.sub(r'"+', "", raw)
            raw = re.sub(r"`+", "", raw)
            raw = re.sub(r"^\s*\w[\w\s]*query\s*:?\s*", "", raw, flags=re.IGNORECASE)
            raw = next((line.strip() for line in raw.splitlines() if line.strip()), "")
            raw = raw[:120]
            raw = re.sub(r"\b\w+:\S+\s*", "", raw).strip()

            if not raw or raw.upper() == "SKIP":
                return "", False

            self.log(f"[INTERNET] 🔍 {raw}")
            self.root.after(0, lambda: self._set_internet_indicator(True))
            self.ai.internet.override_search_query = raw
            ctx = self.ai.internet.enrich_task(raw)
            self.log(f"[INTERNET CTX] length={len(ctx)} preview={ctx[:100] if ctx else 'EMPTY'}")
            self.root.after(0, lambda: self._set_internet_indicator(False))
            return ctx, True

        except Exception as e:
            self.log(f"[INTERNET ERROR] {e}")
            self.root.after(0, lambda: self._set_internet_indicator(False))
            return "", False

    def _handle_internet_search(self, user_input, history_str):
        """Run a full iterative internet search and ReAct pass. Returns (ctx, True)."""
        import datetime as _dt
        year = _dt.datetime.now().year
        env  = self.get_environment()

        force_words = ["news", "latest", "today", "current", "breaking",
                       "headline", "sports", "weather", "temperature",
                       "score", "price", "population"]

        if any(w in user_input.lower() for w in force_words):
            raw = user_input
            self.log("[INTERNET] 🔎 Forced search trigger")
        else:
            raw = self.ai.generate(
                f"Does answering this question require current real-world data?\n"
                f"Answer with a short 2-5 word search query including {year} if relevant, "
                f"OR the single word: SKIP\n\nQuestion: {user_input}\nAnswer:",
                use_planning=False
            ).strip()

        raw = re.sub(r"[^a-zA-Z0-9\s]", "", raw).strip()

        local_words = ["bus", "train", "weather", "restaurant", "near",
                       "traffic", "flights", "timetable", "university"]
        if any(w in user_input.lower() for w in local_words):
            suburb = env.get("suburb")
            city   = env.get("city")
            if suburb and city:
                raw = f"{raw} {suburb} {city}"
            elif city:
                raw = f"{raw} {city}"

        self.log(f"[INTERNET] Decision raw: '{raw}'")

        if raw.upper() == "SKIP" or not raw or len(raw) <= 2:
            self.log("[INTERNET] SKIP — no search needed")
            self.root.after(0, lambda: self._set_internet_indicator(False))
            return "", False

        self.log(f"[INTERNET] 🔍 Query: '{raw}'")
        self.root.after(0, lambda: self._set_internet_indicator(True))

        internet_ctx = ""
        self.ai.internet.override_search_query = raw

        for _ in range(2):
            ctx = self.ai.internet.enrich_task(raw)
            if ctx:
                internet_ctx += "\n\n" + ctx
            if len(internet_ctx) > 15000:
                break
            followup = self.ai.generate(
                f"QUESTION: {user_input}\nCURRENT INFO: {internet_ctx}\n"
                f"Need more info? Reply SEARCH: <query> or DONE",
                use_planning=False
            ).strip()
            if followup.startswith("SEARCH:"):
                raw = followup.replace("SEARCH:", "").strip()
            else:
                break

        self.ai.internet.override_search_query = None

        response = self.ai.react_agent(
            user_prompt=user_input,
            history=history_str,
            tools=self.ai.internet,
            internet_ctx=internet_ctx
        ) or "I couldn't complete that request."

        self._internet_response = response
        return internet_ctx, True

    # ──────────────────────────────────────────────────────────────────────────
    # PLANNER
    # ──────────────────────────────────────────────────────────────────────────

    def _handle_planner(self, user_input, history_str, internet_ctx):
        """Create and execute a multi-agent plan, then supervise the results."""
        from nova_manager import ManagerAgent

        # ── NEW: Recall relevant past conversations from memory ──
        if hasattr(self, 'memory'):
            recalled = self.memory.recall_conversations(user_input, n_results=3)
            if recalled:
                memory_context = "\n\nRELEVANT PAST CONVERSATIONS:\n"
                for i, entry in enumerate(recalled, 1):
                    memory_context += f"[{i}] {entry.get('task', '')[:100]}\n    → {entry.get('result', '')[:200]}\n"
                history_str = memory_context + history_str
                self.log(f"[MEMORY] Recalled {len(recalled)} relevant exchanges")

        # ── If user_input contains uploaded file content, inject into history ──
        if "Content of " in user_input and "```" in user_input:
            history_str = f"[UPLOADED FILE CONTENT]\n{user_input}\n\n{history_str}"
            self.log("[PLANNER] Injected file content into history_str")
        # Inject semantic memory into history context
        if hasattr(self, 'memory'):
            semantic_ctx = self.memory.get_semantic_context()
            if semantic_ctx:
                history_str = semantic_ctx + "\n\n" + history_str
                self.log(f"[MEMORY] Injected semantic context")

        affect_note = self._get_affect_modifier()
        if affect_note:
            history_str = f"STYLE NOTE: {affect_note}\n\n{history_str}"

        plan_data = self.planner.create_plan(user_input, history_str, last_exchanges=50)
        if isinstance(plan_data, dict):
            mode = plan_data.get("mode", "parallel")
            tasks = plan_data.get("tasks", [])
        else:
            mode = "parallel"
            tasks = plan_data

        if not tasks:
            return None

        self.log(f"[PLANNER] Mode: {mode} | Tasks: {len(tasks)}")
        self.log(f"[PLANNER TASKS] {tasks}")

        manager = ManagerAgent(self.ai, self.log, nova=self)
        plan = manager.analyse({"mode": mode, "tasks": tasks})
        plan = manager.supervise_plan(plan, user_input)

        self.log(f"[PLAN] {plan}")

        results = manager.execute(plan, self.executor, internet_ctx, history_str)
        self._last_results = results
        self.log(f"[RESULTS] {str(results)[:200]}")

        # ── Extract SymPy results before synthesis swallows them ──
        sympy_results = []
        for i, task in enumerate(plan.get("tasks", [])):
            if task.get("agent") == "sympy_exec" and i < len(results):
                sympy_results.append(results[i])

        response = manager.supervise(results, user_input)
        self._last_plan = plan

        # ── Append SymPy result separately ONLY if supervise didn't include it ──
        if sympy_results and len(results) > 1:
            for sr in sympy_results:
                if sr and not str(sr).startswith("Error") and str(sr) not in str(response):
                    response = (response or "") + f"\n\n---\n{sr}"

        # Append source URLs (skip self_inspect and sympy_exec)
        is_self_inspect = any(t.get("agent") == "self_inspect" for t in plan.get("tasks", []))
        is_sympy = any(t.get("agent") == "sympy_exec" for t in plan.get("tasks", []))
        if not is_self_inspect and not is_sympy:
            urls = []
            for r in results:
                urls.extend(re.findall(r"https?://\S+", str(r)))
            if urls:
                response += "\n\n---\n🔗 Sources:\n" + "\n".join(set(urls[:5]))

        # Don't override code execution results
        if any("CODE EXECUTED" in str(r) for r in results):
            response = None

        # Safe fallback if response is empty
        if not response or not str(response).strip():
            self.log("[FALLBACK] Empty response — recovering")
            if results:
                response = "\n\n".join([str(r) for r in results if r and str(r).strip()])
                if not response.strip():
                    response = None
            elif internet_ctx:
                response = internet_ctx[:2000]

        self.state["last_result"] = response
        self.state["last_task"] = user_input
        self.state["last_type"] = "planner"
        return response

    # ──────────────────────────────────────────────────────────────────────────
    # INTENT CLASSIFICATION
    # ──────────────────────────────────────────────────────────────────────────

    def _classify_intent(self, user_input, history_str):
        """Classify the user input as TEXT, MATH, or CODE."""
        prompt = (
            f"Classify the latest message into ONE category:\n"
            f"TEXT — conversational answer\n"
            f"MATH — equations or mathematical working\n"
            f"CODE — runnable program (plot, simulation, animation)\n\n"
            f"CONVERSATION:\n{history_str}\n\n"
            f"Latest message: {user_input}\nCategory:"
        )
        intent = self.ai.generate(prompt, use_planning=False).strip().upper()
        if "MATH" in intent: return "MATH"
        if "CODE" in intent: return "CODE"
        return "TEXT"

    def _needs_reasoning(self, text: str) -> bool:
        """Return True if the question likely requires step-by-step reasoning."""
        text = text.lower()
        keywords = [
            "step by step", "solve", "puzzle", "logic", "prove",
            "derive", "calculate", "deduce", "jug", "how do you get", "explain why"
        ]
        return any(k in text for k in keywords)

    # ──────────────────────────────────────────────────────────────────────────
    # HISTORY / ENVIRONMENT
    # ──────────────────────────────────────────────────────────────────────────

    def _build_history_context(self):
        """Build a combined environment + conversation history string for prompts."""
        env = self.get_environment()
        history_str = ""
        for entry in self.conversation_history[-100:]:
            if "content" not in entry:
                continue
            role = "You" if entry["role"] == "user" else "Nova"
            history_str += f"{role}: {entry['content']}\n"

        env_context = (
            f"CURRENT DATE: {env['date']}\n"
            f"CURRENT TIME: {env['time']}\n"
            f"TIMEZONE: {env['timezone']}\n"
            f"Suburb: {env.get('suburb')}  City: {env.get('city')}  "
            f"Region: {env.get('region')}  Country: {env.get('country')}\n"
            f"Lat: {env.get('lat')}  Lon: {env.get('lon')}"
        )
        return f"ENVIRONMENT:\n{env_context}\n\n{history_str}"

    def build_recent_history(self, n=100):
        """Return the last n conversation turns formatted for tool prompts."""
        history = ""
        # Use state history (persistent) instead of conversation_history (in-memory)
        state_history = self.state.get('history', [])
        for entry in state_history[-n:]:
            task = entry.get('task', '')
            result = entry.get('result', '')[:200]
            history += f"[USER] {task}\n[NOVA] {result}\n"
        return history.strip()

    def build_env_context(self):
        """Return a formatted environment context block for planner prompts."""
        import json
        env = self.get_environment()

        music_dir = "D:/Music"
        video_dir = "D:/TV"
        try:
            with open("music.json", "r") as f:
                cfg = json.load(f)
                music_dir = cfg.get("music_dir", music_dir)
                video_dir = cfg.get("video_dir", video_dir)
        except:
            pass

        return (
            f"\nSYSTEM CONTEXT:\n"
            f"- Current date: {env.get('date')}\n"
            f"- Current time: {env.get('time')}\n"
            f"- Location: {env.get('suburb')}, {env.get('city')}, {env.get('country')}\n"
            f"- Coordinates: {env.get('lat')}, {env.get('lon')}\n"
            f"- Music directory: {music_dir}\n"
            f"- Video directory: {video_dir}\n\n"
            f"RULES:\n"
            f"- Treat this information as correct and current\n"
            f"- Use it when answering location-based or time-based queries\n"
            f"- When searching for music by artist name, use: search <artist> in {music_dir}\n"
            f"- When searching for video by title, use: search <title> in {video_dir}\n"
            f"- NEVER use find *.mp3 or find *.mp4 to search for a specific artist or title — it returns all files and truncates\n"
        )


    # ──────────────────────────────────────────────────────────────────────────
    # RESPONSE HANDLERS
    # ──────────────────────────────────────────────────────────────────────────

    def _handle_text_intent(self, user_input, history_str, internet_ctx=""):
        """Generate a plain conversational response."""
        from datetime import datetime
        reasoning_mode = self._needs_reasoning(user_input)
        env      = self.get_environment()
        location = f"{env.get('city')}, {env.get('country')}"
        system   = self.SYSTEM_PROMPT.format(
            date=datetime.now().strftime("%A %d %B %Y"),
            location=location
        )
        internet_note       = f"\n\nCURRENT DATA:\n{internet_ctx}" if internet_ctx else ""
        reasoning_instruction = ""
        if reasoning_mode:
            self.log("[REASONING] Step-by-step reasoning mode activated")
            reasoning_instruction = (
                "\nIMPORTANT:\nSolve the problem step-by-step.\n"
                "Do NOT jump directly to the final answer.\n"
                "Show intermediate reasoning before the final answer.\n"
            )

        prompt = (
            f"{system}\n\n{reasoning_instruction}\n\n"
            f"CONVERSATION SO FAR:\n{history_str}\n\n"
            f"{internet_note}\n\nUser: {user_input}\nNova:"
        )
        response = self.ai.generate(prompt) or "I'm sorry, I couldn't generate a response. Please try again."

        self._append_conv("assistant", response)
        self.conversation_history.append({"role": "assistant", "content": response})
        self.speak_text(response)
        self._maybe_play_contextual_sound(user_input, response)
        self._maybe_render_latex(response)

    def _handle_math_intent(self, user_input, history_str, internet_ctx=""):
        """Generate a mathematical response with LaTeX notation."""
        from datetime import datetime
        env      = self.get_environment()
        location = f"{env.get('city')}, {env.get('country')}"
        system   = self.SYSTEM_PROMPT.format(
            date=datetime.now().strftime("%A %d %B %Y"),
            location=location
        )
        prompt = (
            f"{system}\n\nCONVERSATION SO FAR:\n{history_str}\n\n"
            f"The user has asked a mathematical question.\n"
            f"Use LaTeX: inline $expression$, display \\[expression\\]\n\n"
            f"User: {user_input}\nNova:"
        )
        response = self.ai.generate(prompt) or "I couldn't solve that. Please rephrase."
        self._append_conv("assistant", response)
        self.conversation_history.append({"role": "assistant", "content": response})
        self.root.after(0, lambda: self.latex_win.show())
        self.root.after(100, lambda: self.latex_win.append_document(response))
        self.log("[LATEX] Math response rendered")
        self.speak_text(response, is_math=True)

    def _handle_text_preview(self, user_input, history_str, internet_ctx=""):
        """Quick text preview — generate without planning."""
        return self.ai.generate(
            f"{history_str}\n\n{internet_ctx}\n\nUser: {user_input}\nAnswer:",
            use_planning=False
        )

    def _handle_math_preview(self, user_input, history_str):
        """Quick math preview — generate without planning."""
        return self.ai.generate(f"Solve step-by-step:\n{user_input}", use_planning=False)

    def _handle_pdf_qa(self, user_input):
        """Answer a question about the currently loaded PDF paper."""
        response = self.ai.generate(
            f"You are answering questions about a loaded research paper.\n\n"
            f"PAPER CONTENT:\n{self.loaded_paper_text[:12000]}\n\n"
            f"Question:\n{user_input}",
            use_planning=False
        )
        if response:
            self._append_conv("assistant", response)
            self.conversation_history.append({"role": "assistant", "content": response})
            self.speak_text(response)

    def _handle_code_intent(self, user_input, internet_ctx="", history_str=""):
        """Confirm the coding task with the user then launch the autocoder."""
        has_maths = bool(re.search(r"\$|\\\[|\\\(|\\frac|\\int|\\sum|\\sqrt", history_str))
        math_rules = (
            "IMPORTANT — MATHEMATICAL DISPLAY RULES:\n"
            "- Use matplotlib mathtext r'$...$' for labels\n"
            "- NEVER use plt.tight_layout() when ax.axis('off')\n\n"
        ) if has_maths else ""

        internet_note = (
            f"\n\nREAL DATA ALREADY RETRIEVED — USE THIS IN THE CODE:\n{internet_ctx[:3000]}"
            if internet_ctx else ""
        )
        enriched_task = f"{math_rules}Based on this conversation:\n{history_str}{internet_note}\n\nACTUAL TASK TO CODE: {user_input}"

        explain_prompt = (
            f"You are Nova. The user wants something coded or plotted.\n"
            f"Briefly confirm what you will plot/code (1-2 sentences).\n"
            f"Then say: 'Shall I Run the Python program?'\n\n"
            f"CONVERSATION SO FAR:\n{history_str}{internet_note}\n\nUser: {user_input}\nNova:"
        )
        explanation = self.ai.generate(explain_prompt)
        if explanation:
            self._append_conv("assistant", explanation)
            self.conversation_history.append({"role": "assistant", "content": explanation})
            self.speak_text(explanation)

        self.root.after(0, lambda: self._ask_code_permission(enriched_task, internet_ctx))

    # ──────────────────────────────────────────────────────────────────────────
    # SOUND / CODE HELPERS
    # ──────────────────────────────────────────────────────────────────────────

    def _maybe_play_contextual_sound(self, user_input, response):
        """If the user asked what something sounds like, play that sound."""
        text = user_input.lower()
        sound_question_phrases = [
            "what noise does", "what sound does", "what does a",
            "what noise do", "what sound do", "how does a",
            "what does it sound like", "sound of a",
            "describe what sound", "what sounds do",
        ]
        if not any(p in text for p in sound_question_phrases):
            return

        if hasattr(self, "_last_auto_sound") and self._last_auto_sound:
            _, last_input = self._last_auto_sound
            if last_input == text:
                self.log("[AUTO SOUND] Skipping — identical question")
                return

        sound_query = self.ai.generate(
            f'The user asked: "{user_input}"\n'
            f"What is the most iconic sound associated with the subject?\n"
            f"Reply with ONLY 1-3 words. If no clear sound exists, reply: NONE",
            use_planning=False
        ).strip()

        if not sound_query or sound_query.upper() == "NONE":
            return

        self._last_auto_sound = (sound_query, text)
        self.log(f"[AUTO SOUND] Playing contextual sound: {sound_query}")

        def _play():
            try:
                self.tools.run("search_and_play_sound", sound_query,
                               self.download_dir, self.ai.internet)
            except Exception as e:
                self.log(f"[AUTO SOUND] Failed: {e}")

        threading.Thread(target=_play, daemon=True).start()

    def _extract_and_send_code(self, response):
        """Extract a Python code block from a ReAct response and run it."""
        if "```python" not in response:
            return
        try:
            start = response.find("```python") + 9
            end   = response.find("```", start)
            if end <= start:
                return
            code = response[start:end].strip()
            if not code:
                return

            def _show():
                try:
                    self.code_display.config(state="normal")
                    self.code_display.delete("1.0", "end")
                    self.code_display.insert("1.0", code)
                    self.code_display.config(state="disabled")
                except Exception:
                    pass

            self.root.after(0, _show)
            self.log("[CODE] 📋 Code block extracted from agent response → running...")
            task = f"PREVIOUS CONTEXT:\nRun this exact code as-is:\n\n```python\n{code}\n```"
            threading.Thread(target=self._run_autocoder, args=(task,), daemon=True).start()
        except Exception as e:
            self.log(f"[CODE] Extract error: {e}")

    def _handle_story_intent(self, user_input):
        """Write a short story with embedded sound effect tags and play them."""
        self._append_conv("system", "Writing story with sound effects...")
        story_prompt = (
            f"Write a short dramatic story (150-200 words) on this theme: {user_input}\n\n"
            f"Rules:\n"
            f"- At dramatic moments insert [SOUND: description] tags\n"
            f"- Keep sound descriptions to 1-3 words e.g. [SOUND: thunder]\n"
            f"- Use 3-5 sounds spread through the story\n"
            f"- Write in present tense, vivid prose"
        )
        story = self.ai.generate(story_prompt, use_planning=False)
        if not story:
            self._append_conv("assistant", "Could not generate story.")
            return

        self._append_conv("assistant", story)
        self.conversation_history.append({"role": "assistant", "content": story})
        clean_story = re.sub(r"\[SOUND:[^\]]+\]", "", story)
        self.speak_text(clean_story)

        def _play_sounds():
            import time
            time.sleep(len(clean_story.split()) * 0.4)
            for m in re.finditer(r"\[SOUND:([^\]]+)\]", story):
                query = m.group(1).strip()
                self.log(f"[STORY] Playing sound: {query}")
                try:
                    self.tools.run("search_and_play_sound", query,
                                   self.download_dir, self.ai.internet)
                    time.sleep(3)
                except Exception as e:
                    self.log(f"[STORY] Sound failed: {e}")

        threading.Thread(target=_play_sounds, daemon=True).start()

    def _exit_with_state(self, user_input, result, result_type, text):
        """Update state after a tool or agent result."""
        follow_up_phrases = ["result", "answer", "repeat", "again", "open it"]
        is_follow_up = any(p in text for p in follow_up_phrases)
        if not is_follow_up:
            self.state["last_task"] = user_input
        self.state["last_result"] = result
        self.state["last_type"]   = result_type
        self._save_history(user_input, result)

    def _is_story_request(self, text):
        """Return True if the input is a request for a story with sound."""
        story_phrases = [
            "tell me a story", "tell a story", "write a story",
            "story with sound", "narrate a story",
        ]
        return any(p in text for p in story_phrases) and "sound" in text

    def _get_affect_modifier(self) -> str:
        """Get current affect style modifier for prompts."""
        if not hasattr(self, 'affect'):
            return ""
        mods = self.affect.get_response_modifiers()
        return mods.get("style_modifiers", "")
    def _check_for_prospective(self, user_input: str, response: str):
        """Detect if the conversation contains something worth remembering later."""
        if not hasattr(self, 'memory') or not hasattr(self, 'ai'):
            return

        triggers = [
            "remind me", "don't forget", "next time", "revisit",
            "follow up", "come back to", "check back", "by friday",
            "tomorrow", "next week", "should look into", "want to",
            "need to", "must remember"
        ]

        text = (user_input + " " + response).lower()
        if not any(t in text for t in triggers):
            return

        prompt = f"""From this conversation, extract ONE specific thing worth remembering for later.
    User said: {user_input[:200]}
    Nova said: {response[:200]}
    
    Return ONLY a single sentence reminder, or NONE if nothing is worth storing."""

        reminder = self.ai.generate(prompt, use_planning=False)
        if reminder and reminder.strip().upper() != "NONE" and len(reminder.strip()) > 10:
            self.memory.add_prospective(
                reminder.strip(),
                context=user_input[:100]
            )
            self.log(f"[MEMORY] 📌 Prospective stored from conversation")

    def _extract_semantic_facts(self, user_input: str, response: str):
        """Scan conversation for persistent facts worth storing."""
        if not hasattr(self, 'memory') or not hasattr(self, 'ai'):
            return

        self.log(f"[MEMORY] Semantic check triggered for: {user_input[:50]}")  # ← ADD THIS

        # Only run occasionally — not every message
        import random
        if random.random() > 0.3:  # 30% chance per message
            self.log("[MEMORY] Semantic extraction skipped (probability)")  # ← ADD THIS
            return

        self.log("[MEMORY] Semantic extraction RUNNING")  # ← ADD THIS

        prompt = f"""Extract any persistent facts about the user from this conversation.
    
    User said: {user_input[:300]}
    Assistant said: {response[:300]}

    Return a JSON object with fact_key: fact_value pairs.
    Only include concrete, persistent facts — preferences, tools, locations, projects.
    If nothing worth storing, return: {{}}
    Return ONLY valid JSON, nothing else.

    Examples of good facts:
    {{"preferred_editor": "PyCharm", "gpu": "RTX 5070 Ti", "location": "Birkdale Auckland"}}

    Examples of what NOT to store:
    - Questions asked
    - Temporary requests
    - Things that change daily"""

        try:
            raw = self.ai.generate(prompt, use_planning=False)
            raw = raw.strip()
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            import json
            facts = json.loads(raw)
            if isinstance(facts, dict):
                for key, value in facts.items():
                    if key and value and len(str(value)) < 200:
                        self.memory.store_semantic(key, str(value))
        except Exception as e:
            self.log(f"[MEMORY] Semantic extraction failed: {e}")


