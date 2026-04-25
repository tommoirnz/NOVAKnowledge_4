import json
import re
import traceback
from datetime import datetime


class TaskPlanner:

    def __init__(self, ai, logger=None, env_fn=None, app=None):
        self.ai = ai
        self.log = logger
        self.env_fn = env_fn
        self.app = app

        self.VALID_AGENTS = {
            "research",
            "file_explorer",
            "youtube_tools",
            "open_webpage",
            "play_local_music",
            "play_local_video",
            "play_audio_from_url",
            "play_sound_from_url",
            "search_and_play_sound",
            "search_and_show_image",
            "summarise_document_from_source",
            "download_file",
            "self_inspect",
            "read_source",
            "write_file",
            "code",
            "math",
            "text",
            "diagram",
            "sympy_exec"
        }

    # ─────────────────────────────────────────
    # FIX 3: Helpers defined BEFORE create_plan
    # ─────────────────────────────────────────

    def _split_conversation_exchanges(self, history_str):
        """Parse conversation history into exchange pairs."""
        if not history_str:
            return []

        exchanges = []
        current_exchange = []

        # FIX 2: Specific exception types, no bare except
        try:
            if history_str.strip().startswith('{') or history_str.strip().startswith('['):
                data = json.loads(history_str)
                if isinstance(data, dict) and 'history' in data:
                    for entry in data['history']:
                        task   = entry.get('task', '')
                        result = entry.get('result', '')
                        exchanges.append(f"Task: {task}\nResult: {result[:200]}...")
                    return exchanges
        except (json.JSONDecodeError, ValueError, KeyError):
            pass

        for line in history_str.split('\n'):
            if line.startswith('User:') or line.startswith('Task:') or line.startswith('AI:'):
                if current_exchange:
                    exchanges.append('\n'.join(current_exchange))
                    current_exchange = []
            current_exchange.append(line)

        if current_exchange:
            exchanges.append('\n'.join(current_exchange))

        return exchanges

    def _is_follow_up(self, user_input):
        """Detect if current input is a follow-up to previous conversation."""
        text  = user_input.lower().strip()
        words = text.split()

        # FIX 7: Expanded short-phrase check — covers up to 5 words
        if len(words) <= 5:
            short_patterns = [
                r'^yes\b', r'^yeah\b', r'^yep\b', r'^sure\b',
                r'^ok\b', r'^okay\b', r'^alright\b',
                r'^do it\b', r'^go ahead\b', r'^proceed\b',
                r'^continue\b', r'^please\b',
                r'^yes please\b', r'^yes\b.*\bdo it\b',
            ]
            if any(re.search(p, text) for p in short_patterns):
                return True

        pronoun_patterns = [
            r'\bit\b', r'\bthat\b', r'\bthis\b', r'\bthem\b', r'\bthose\b'
        ]
        action_patterns = [
            r'\bdescribe\b', r'\bexplain\b', r'\bshow\b', r'\bplot\b',
            r'\badd labels?\b', r'\blabel\b', r'\bdo it\b',
            r'\bwith labels?\b', r'\banimated?\b',
        ]
        has_pronoun = any(re.search(p, text) for p in pronoun_patterns)
        has_action  = any(re.search(p, text) for p in action_patterns)
        return has_pronoun and has_action

    def _get_current_topic(self, history_str, exchanges=None):
        """Extract the current topic from recent history.
        Returns the most recently matched topic rather than just the last one.
        """
        if not history_str and not exchanges:
            return None

        topics = []

        if exchanges:
            recent_exchanges = exchanges[-20:] if len(exchanges) > 20 else exchanges
        else:
            lines = history_str.split('\n')[-20:]
            recent_exchanges = ['\n'.join(lines)]

        # FIX 5: Walk in forward order so topics[-1] is genuinely the most recent match
        for exchange in recent_exchanges:
            exchange_lower = exchange.lower()
            if 'diagram' in exchange_lower or 'graphviz' in exchange_lower or 'block diagram' in exchange_lower:
                topics.append('diagram')
            elif 'plot' in exchange_lower or 'graph' in exchange_lower or 'chart' in exchange_lower:
                topics.append('plot')
            elif 'math' in exchange_lower or 'integral' in exchange_lower or 'derivative' in exchange_lower:
                topics.append('math')
            elif 'code' in exchange_lower or 'python' in exchange_lower:
                topics.append('code')
            elif 'image' in exchange_lower or 'picture' in exchange_lower:
                topics.append('image')
            elif 'music' in exchange_lower or 'play' in exchange_lower:
                topics.append('audio')

        return topics[-1] if topics else None

    def _extract_relevant_context(self, history_str, last_exchanges=3):
        """Extract only the most recent N exchanges from history."""
        if not history_str:
            return ""

        # FIX 12: Guard that history_str is actually a string before any operations
        if not isinstance(history_str, str):
            history_str = str(history_str)

        try:
            if history_str.strip().startswith('{'):
                try:
                    data = json.loads(history_str)
                    if 'history' in data:
                        history_list = data['history']
                        recent = history_list[-last_exchanges:] if len(history_list) > last_exchanges else history_list
                        formatted = []
                        for entry in recent:
                            task   = entry.get('task', '')
                            result = entry.get('result', '')[:300]
                            formatted.append(f"User: {task}\nAssistant: {result}")
                        return "\n\n".join(formatted)
                except (json.JSONDecodeError, ValueError, KeyError):
                    pass

            lines = history_str.split('\n')
            user_line_indices = [i for i, line in enumerate(lines) if line.startswith('User:')]
            if len(user_line_indices) > last_exchanges:
                last_exchange_start = user_line_indices[-last_exchanges]
            else:
                last_exchange_start = 0
            return "\n".join(lines[last_exchange_start:])

        except Exception as e:
            self.log(f"[CONTEXT DEBUG] Error: {e}")
            # FIX 12: Safe fallback — history_str is guaranteed a str by this point
            return "\n".join(history_str.split('\n')[-100:])

    def _should_keep_full_context(self, user_input):
        """Determine if full context is needed."""
        full_context_phrases = [
            "summarize everything",
            "all history",
            "entire conversation",
            "what did we talk about",
            "full context"
        ]
        text = user_input.lower()
        return any(phrase in text for phrase in full_context_phrases)

    def _extract_relevant_context_for_followup(self, recent_context, topic, user_input):
        """Extract the specific context needed for a follow-up task."""
        if topic == "diagram":
            dot_pattern = r'digraph\s*\{[^}]+\}'
            matches = re.findall(dot_pattern, recent_context, re.DOTALL)
            if matches:
                return f"The diagram to work with has this DOT code:\n{matches[-1][:500]}"

            for keyword in ["block diagram", "flowchart", "control system", "signal flow"]:
                if keyword in recent_context.lower():
                    lines = recent_context.split('\n')
                    for i, line in enumerate(lines):
                        if keyword in line.lower():
                            context_lines = lines[max(0, i - 10):min(len(lines), i + 10)]
                            return f"Context about the {keyword}:\n" + "\n".join(context_lines)

        elif topic == "code":
            code_pattern = r'```python\s*(.*?)\s*```'
            matches = re.findall(code_pattern, recent_context, re.DOTALL)
            if matches:
                return f"The code to work with is:\n```python\n{matches[-1][:500]}\n```"

            for keyword in ["plot", "graph", "chart", "code"]:
                if keyword in recent_context.lower():
                    lines = recent_context.split('\n')
                    for i, line in enumerate(lines):
                        if keyword in line.lower():
                            context_lines = lines[max(0, i - 2):min(len(lines), i + 3)]
                            return f"Context about the {keyword}:\n" + "\n".join(context_lines)

        elif topic == "math":
            math_pattern = r'\$[^$]+\$|\\\[.*?\\\]'
            matches = re.findall(math_pattern, recent_context, re.DOTALL)
            if matches:
                return f"The math expression to work with is: {matches[-1]}"

            for keyword in ["equation", "integral", "derivative", "solve"]:
                if keyword in recent_context.lower():
                    lines = recent_context.split('\n')
                    for i, line in enumerate(lines):
                        if keyword in line.lower():
                            context_lines = lines[max(0, i - 2):min(len(lines), i + 3)]
                            return f"Context about the {keyword}:\n" + "\n".join(context_lines)

        elif topic == "research":
            lines = recent_context.split('\n')
            for line in reversed(lines[-10:]):
                if "research" in line.lower() or "search" in line.lower():
                    return f"Research context:\n" + line

        lines = recent_context.split('\n')
        last_lines = lines[-50:] if len(lines) > 50 else lines
        return "Most recent context:\n" + "\n".join(last_lines)

    def _clean_response(self, response):
        response = response.strip()
        response = re.sub(r"^```(?:json)?\s*", "", response, flags=re.IGNORECASE)
        # FIX 10: Only strip the final fence, not any embedded backticks
        response = re.sub(r"\s*```\s*$", "", response)
        if response.lower().startswith("json"):
            response = response[4:].strip()

        if response.strip().startswith('"mode"'):
            response = "{" + response
            self.log("[PLANNER] Added missing opening brace")

        return response.strip()

    def _repair_json(self, response):
        """Try to close unclosed JSON by walking the string to track nesting order."""
        # FIX 6: Walk the string to build the correct close sequence
        stack = []
        in_string = False
        escape_next = False

        for ch in response:
            if escape_next:
                escape_next = False
                continue
            if ch == '\\' and in_string:
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch in ('{', '['):
                stack.append('}' if ch == '{' else ']')
            elif ch in ('}', ']'):
                if stack and stack[-1] == ch:
                    stack.pop()

        # Close in reverse nesting order
        response += ''.join(reversed(stack))
        return response

    def _is_bad_output(self, text):
        BAD_PATTERNS = [
            "Step 1", "Step 2",
            "First,", "Next,", "Then,", "Finally,",
            "PLAN:", "Identify:", "Execute:"
        ]
        return any(p.lower() in text.lower() for p in BAD_PATTERNS)

    # ─────────────────────────────────────────
    # MAIN ENTRY POINT
    # ─────────────────────────────────────────

    def create_plan(self, user_input, history_str="", last_exchanges=20):
        """
        Creates a task plan from user input with selective context.

        Args:
            user_input:     Current user request
            history_str:    Full conversation history (optional)
            last_exchanges: Number of recent exchanges for non-follow-up, non-full-context paths
        """
        text = (user_input or "").split("\n")[0].lower()

        # ── 0. LIGHT INTENT ROUTING ───────────
        image_keywords = ["image", "images", "picture", "pictures", "photo", "photos"]
        poster_keywords = [
            "poster", "collage", "display", "layout", "arrange", "plot them",
            "cube", "rotating", "slideshow", "gallery", "animate", "animation",
            "put them", "place them", "3d", "faces", "sides", "screensaver"
        ]
        file_operation_keywords = ["list", "contents", "directory", "folder", "open", "find", "search", "show me files"]
        is_file_operation = any(k in text for k in file_operation_keywords)
        is_image = any(k in text for k in image_keywords) and not is_file_operation
        is_image_and_code = is_image and any(k in text for k in poster_keywords)

        if is_image and not is_image_and_code:
            clean_query = text
            for phrase in ["show me", "pictures of", "images of", "photos of"]:
                clean_query = clean_query.replace(phrase, "")
            clean_query = clean_query.strip()
            # FIX 8: Prepend default count so executor receives expected format
            clean_query = f"6 {clean_query}"
            self.log("[PLANNER] Image search → routing to search_and_show_image")
            return {
                "mode": "parallel",
                "tasks": [{"agent": "search_and_show_image", "task": clean_query}]
            }

        # ── ENV ───────────────────────────────
        env_ctx = ""
        if self.env_fn:
            try:
                env_ctx = self.env_fn()
            except Exception as e:
                if self.log:
                    self.log(f"[PLANNER] Env error: {e}")

        today = datetime.now().strftime("%d %B %Y")

        # ── DETECT FOLLOW-UP ─────────────────
        is_follow_up    = self._is_follow_up(user_input)
        need_full_context = self._should_keep_full_context(user_input)

        # ── HISTORY (SELECTIVE CONTEXT) ───────
        # FIX 4: Document clearly that last_exchanges only applies to the else branch
        if is_follow_up and history_str:
            try:
                if history_str.strip().startswith('{'):
                    data = json.loads(history_str)
                    if 'history' in data:
                        full_formatted = []
                        for entry in data['history']:
                            task   = entry.get('task', '')
                            result = entry.get('result', '')[:300]
                            full_formatted.append(f"User: {task}\nAssistant: {result}")
                        recent_history = "\n\n".join(full_formatted)
                        context_note = "FULL CONVERSATION HISTORY (follow-up detected):"
                        self.log(f"[PLANNER] Follow-up — full history, {len(data['history'])} entries")
                    else:
                        recent_history = history_str
                        context_note = "FULL CONVERSATION HISTORY (follow-up detected):"
                else:
                    recent_history = history_str
                    context_note = "FULL CONVERSATION HISTORY (follow-up detected):"
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                self.log(f"[PLANNER] Error parsing history for follow-up: {e}")
                recent_history = history_str
                context_note = "FULL CONVERSATION HISTORY (follow-up detected):"
        elif need_full_context:
            recent_history = history_str or ""
            context_note   = "FULL CONVERSATION HISTORY (as requested):"
        else:
            # last_exchanges is only used here
            recent_history = self._extract_relevant_context(history_str, last_exchanges)
            context_note   = f"RECENT CONVERSATION (last {last_exchanges} exchanges):"

        self.log(f"[PLANNER DEBUG] recent_history length: {len(recent_history)}")
        self.log(f"[PLANNER DEBUG] recent_history first 300 chars: {recent_history[:300] if recent_history else 'EMPTY'}")
        self.log(f"[PLANNER DEBUG] original history_str length: {len(history_str) if history_str else 0}")

        exchanges     = self._split_conversation_exchanges(history_str) if history_str else []
        current_topic = self._get_current_topic(history_str, exchanges)

        relevant_context_for_task = ""
        if is_follow_up and recent_history and current_topic:
            relevant_context_for_task = self._extract_relevant_context_for_followup(
                recent_history, current_topic, user_input
            )

        self.log(f"[PLANNER] history_str type: {type(history_str)}")
        self.log(f"[PLANNER] history_str starts with: {history_str[:100] if history_str else 'EMPTY'}")

        # FIX 11: Only build guidance strings when they'll actually be used
        follow_up_guidance = ""
        if is_follow_up:
            follow_up_guidance = f"""
⚠️ IMPORTANT: This appears to be a FOLLOW-UP to a previous request.
- Reference the most recent task or topic from the RECENT CONVERSATION
- Focus ONLY on completing the current thread
- Do NOT create tasks for older, unrelated topics

CRITICAL - CONTEXT EMBEDDING REQUIRED:
When the user uses short follow-up phrases like "yes", "describe it", "add labels", "do it", etc.:
- You MUST embed the relevant context from RECENT CONVERSATION into the task description
- Do NOT just pass the user's short phrase as the task

Current topic: {current_topic}
Relevant context to embed:
{relevant_context_for_task if relevant_context_for_task else "Extract from RECENT CONVERSATION above"}

Example transformations:
- User: "yes describe it" → Task: "Describe the [specific thing from context]"
- User: "add labels"      → Task: "Add labels to the [specific diagram/chart from context]"
- User: "do it"           → Task: "Perform the [specific action from context]"
- User: "and plot it"     → Task: "Create a plot based on the [specific data from context]"

The task MUST be self-contained and understandable without looking back at history.
"""

        topic_guidance = ""
        if current_topic and not need_full_context:
            topic_guidance = f"""
CURRENT TOPIC DETECTED: {current_topic}
- Focus tasks on this topic
- Do not introduce unrelated topics from earlier history
"""

        # FIX 1: Prompt is NOT indented — no leading whitespace on any line
        prompt = f"""SYSTEM: You are a JSON task planner. You output ONLY valid JSON. Nothing else.
OUTPUT FORMAT: {{"mode": "parallel"|"sequential", "tasks": [{{"agent": "...", "task": "..."}}]}}
DO NOT write explanations, prose, code, or markdown. ONLY JSON.

{env_ctx}

{context_note}
{recent_history if recent_history else "(No recent conversation)"}
{topic_guidance}
{follow_up_guidance}

Today's date: {today}

Break the user's request into executable tasks.

IMPORTANT:
- Tasks must preserve detail from the user request
- Do NOT simplify or shorten the request
- Keep important keywords, context, and specificity
- Keep task descriptions concise but complete

CRITICAL - FOR FOLLOW-UP REQUESTS:
- If this is a follow-up (user said "yes", "describe it", "add labels", etc.), you MUST expand the task to include the specific subject from the conversation
- The task should be self-contained and include enough detail that the agent doesn't need to look up history
- Example: If user says "describe it" after a diagram, task should be: "Describe the closed-loop feedback control system block diagram"
- NOT: "describe it"

CRITICAL:
- Output MUST be valid JSON
- Output MUST start with {{
- Output MUST end with }}
- NO text before or after JSON
- NO markdown
- NO explanations
- ONLY output task JSON

CHAINING RULE:
- If the user asks to BOTH explain/describe AND plot/code something,
  create TWO tasks in sequential mode:
  1. {{"agent": "math" or "text", "task": "explain the concept..."}}
  2. {{"agent": "code", "task": "plot the result..."}}
- NEVER merge explanation and code into a single code task
- The explanation task always runs first

MATH + VERIFY RULE:
- If user asks to compute AND verify mathematics, use sequential:
  1. {{"agent": "math", "task": "explain and derive..."}}
  2. {{"agent": "sympy_exec", "task": "verify..."}}
- Trigger words: "verify", "check", "confirm", "make sure"
- The sympy_exec task MUST include the actual expression, e.g.:
  {{"agent": "sympy_exec", "task": "verify integral of x^3"}}
  NOT: {{"agent": "sympy_exec", "task": "verify the computed result"}}
- ALWAYS copy the exact mathematical expression from the user request into the sympy_exec task

────────────────────────────
TASK DECOMPOSITION (CRITICAL)
────────────────────────────

- If the user request contains multiple actions (e.g. "and", "then", "after"),
  you MUST split it into multiple tasks.

- Each task MUST:
  - use ONE agent only
  - perform ONE atomic action
  - NOT combine multiple actions

────────────────────────────
AVAILABLE AGENTS (STRICT)
────────────────────────────

- research          → internet search for current information
- file_explorer     → local file browsing, management, AND opening local files.
                      Use "open <path>" to open any local file with its default application.
                      For glob searches use EXACTLY: "find *.ext in C:/path"
                      For keyword searches use EXACTLY: "search keyword in C:/path"
                      NEVER use for music playback — use play_local_music instead.
- youtube_tools     → YouTube search and playback
- open_webpage      → ONLY for http:// or https:// URLs.
                      NEVER use for local file paths, images, or executables.
- play_local_music  → play local audio files by name or keyword
- play_local_video  → play local video files by name or keyword
- self_inspect      → read and explain Nova's own source code
- read_source       → read local source files
- search_and_show_image → search internet for images and display them
- code              → generate and run Python (plots, simulations, data charts)
- math              → mathematical explanation with LaTeX
- text              → plain conversational response
- diagram           → block diagram or flowchart using graphviz
- sympy_exec        → verify or compute mathematics using SymPy
- write_file        → write text content to a local file on disk.
                      Use for: saving README files, reports, notes, any generated text.
                      Task format: "write <content> to <full_path>"
                      Example: "write the README content to C:/Users/OEM/nova/README.md"
                      NEVER use file_explorer for writing — it cannot write files.
                      NEVER use code agent to generate content for writing — use text agent instead.

SAVE RULE (CRITICAL):
- When user says "save it", "save that", "write it to a file", "save as README" etc.:
  ALWAYS use write_file with the full content from the conversation.
  NEVER pretend to write a file by outputting JSON in chat.
  NEVER confirm a save without actually calling write_file.

WRITE FILE RULE (CRITICAL):
- To generate content AND save it to a file, ALWAYS use TWO sequential tasks:
1. {{"agent": "text", "task": "Write the full content of [whatever] in markdown/plain text. Output ONLY the raw file content — no preamble, no 'I'll now write...', no explanations, no tool calls. Start immediately with the content itself."}}
2. {{"agent": "write_file", "task": "write the above content to C:/full/path/to/file.ext"}}
- NEVER use "code" agent to generate content for saving — code runs asynchronously
  and cannot pass its output to write_file. It will always produce an empty file.
- The "text" agent is synchronous and passes its full output to write_file correctly.
- VALID:   text → write_file
- INVALID: code → write_file

  
DIAGRAM vs CODE (CRITICAL):
- "block diagram", "flowchart", "diagram of", "visualise the architecture" → agent: diagram
- "plot", "chart", "bar chart", "histogram", "scatter" → agent: code

LOCAL FILE OPEN RULE (CRITICAL):
- To open a local file ALWAYS use:
  {{"agent": "file_explorer", "task": "open C:/path/to/file.ext"}}
- NEVER use open_webpage for this purpose.

FIND AND OPEN RULE (CRITICAL):
- When user says "open the file called X":
  ALWAYS generate TWO sequential tasks:
  1. {{"agent": "file_explorer", "task": "search X in C:/Users/OEM/Desktop"}}
  2. {{"agent": "file_explorer", "task": "open the file found matching X"}}

FILE LISTING RULE (CRITICAL):
- When the user asks to LIST or FIND files:
  ALWAYS use TWO sequential tasks:
  1. {{"agent": "file_explorer", "task": "search <term> in <directory>"}}
  2. {{"agent": "text", "task": "Format the file search results into a clean organised table"}}

MUSIC RULE (CRITICAL):
- ALL music playback MUST use: agent: play_local_music
- VALID:   {{"agent":"play_local_music","task":"play year of the cat"}}
- INVALID: {{"agent":"file_explorer","task":"find *.mp3 in C:/..."}}

────────────────────────────
FORMAT
────────────────────────────

{{
  "mode": "parallel",
  "tasks": [
    {{"agent":"research","task":"search topic"}}
  ]
}}

CRITICAL:
- If tasks depend on each other → use "sequential"
- If tasks are independent → use "parallel"

ABSOLUTE FINAL RULE:
- Output ONLY the JSON object
- Any text outside the JSON will cause a system crash

The user request to convert into a JSON task plan is:
"{user_input}"

JSON task plan (output ONLY the JSON, starting with {{):
"""

        # ── GENERATE + RETRY ───────────────
        for attempt in range(3):
            response = self.ai.generate(prompt, use_planning=False)

            self.log(f"[PLANNER] Attempt {attempt + 1}, raw response length: {len(response)}")
            self.log(f"[PLANNER] Full raw response:\n{response}")

            response = self._clean_response(response)
            self.log(f"[PLANNER] After clean: {response[:500]}")

            if self.log:
                self.log(f"[PLANNER CLEANED] {response[:200]}")

            if not response.strip().endswith("}"):
                repaired = self._repair_json(response)
                if repaired.strip().endswith("}"):
                    self.log("[PLANNER] JSON repaired via nesting walk")
                    response = repaired
                else:
                    if self.log:
                        self.log("[PLANNER] ⚠ Truncated JSON, repair failed → retry")
                    continue

            if self._is_bad_output(response):
                self.log(f"[PLANNER] Bad output detected: {response[:100]}")
                continue

            if not response.startswith("{"):
                self.log(f"[PLANNER] Doesn't start with {{ : {response[:50]}")
                continue

            try:
                data = json.loads(response)
                self.log(f"[PLANNER] JSON parsed successfully: mode={data.get('mode')}")

                tasks = data.get("tasks", [])
                mode  = data.get("mode", "parallel")

                self.log(f"[PLANNER] Raw tasks from JSON: {tasks}")

                valid_tasks = []
                for i, t in enumerate(tasks):
                    self.log(f"[PLANNER] Processing task {i}: {t}")

                    if not isinstance(t, dict):
                        self.log(f"[PLANNER] Task {i} is not a dict: {type(t)}")
                        continue

                    agent = t.get("agent")
                    task  = t.get("task", "")

                    self.log(f"[PLANNER] Task {i} - agent: {agent}, task: {task[:100]}")

                    if agent not in self.VALID_AGENTS:
                        self.log(f"[PLANNER] Agent {agent} not in VALID_AGENTS")
                        continue

                    valid_tasks.append({
                        "agent": agent,
                        "task": task.strip()
                    })

                self.log(f"[PLANNER] Valid tasks: {valid_tasks}")

                if not valid_tasks:
                    self.log("[PLANNER] No valid tasks, retrying...")
                    continue

                return {"mode": mode, "tasks": valid_tasks}

            except Exception as e:
                if self.log:
                    self.log(f"[PLANNER] JSON parse failed: {e}")
                    # FIX 9: traceback imported at top of file
                    self.log(traceback.format_exc())

        # ── FALLBACK ──────────────────────────
        self.log("[PLANNER] All attempts failed, returning text fallback")
        return {"mode": "parallel", "tasks": [{"agent": "text", "task": user_input}]}