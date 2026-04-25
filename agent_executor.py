import copy
from concurrent.futures import ThreadPoolExecutor
import re
import os
from typing import List, Any, Dict


class AgentExecutor:

    def __init__(self, nova):
        self.nova = nova

    # ─────────────────────────────────────────
    # PARALLEL EXECUTION
    # ─────────────────────────────────────────
    def run_tasks(self, tasks, internet_ctx="", history_str=""):
        results = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = []
            for t in tasks:
                futures.append(pool.submit(self._run_agent, t, internet_ctx, history_str))
            for f in futures:
                results.append(f.result())
        return results

    # ─────────────────────────────────────────
    # SEQUENTIAL EXECUTION
    # ─────────────────────────────────────────





    MAX_CONTEXT_CHARS = 100_000
    TASK_CONTEXT_SLICE = 10_000
    MAX_IMAGES = 12

    def run_tasks_sequential(self, tasks: List[Dict[str, Any]], internet_ctx: str = "", history_str: str = "") -> List[
        Any]:
        results: List[Any] = []
        accumulated_context: str = ""
        early_exit = False

        tasks = copy.deepcopy(tasks)

        patched: List[Dict[str, Any]] = []
        for idx, task in enumerate(tasks):
            patched.append(task)
            if task.get("agent") == "self_inspect":
                next_task = tasks[idx + 1] if idx + 1 < len(tasks) else None
                if next_task is None or next_task.get("agent") != "text":
                    patched.append({
                        "agent": "text",
                        "task": f"Based on the source code inspection, answer: {task.get('task', '')}"
                    })
        tasks = patched

        i = 0
        while i < len(tasks):
            t = tasks[i]
            agent = t.get("agent", "text")

            if accumulated_context and agent in ("code", "text", "write_file"):
                t = dict(t)
                prefix = (
                    "REAL DATA RETRIEVED — YOU MUST USE THESE EXACT VALUES:"
                    if agent == "code"
                    else "CONTEXT FROM PREVIOUS INSPECTION:"
                )
                # FIX: write_file gets full accumulated context — no slice limit
                slice_size = len(accumulated_context) if agent == "write_file" else self.TASK_CONTEXT_SLICE
                t["task"] = f"{prefix}\n{accumulated_context[-slice_size:]}\n\nTASK: {t['task']}"

            if agent == "code" and i > 0 and tasks[i - 1].get("agent") == "search_and_show_image":
                img_dir = self.nova.image_dir
                try:
                    individual = sorted(
                        [
                            os.path.join(img_dir, f)
                            for f in os.listdir(img_dir)
                            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif'))
                               and '_grid' not in f
                        ],
                        key=os.path.getmtime,
                        reverse=True
                    )[:self.MAX_IMAGES]
                except Exception:
                    individual = []

                paths = individual or re.findall(
                    r'(?:[A-Za-z]:[/\\]|/)[^\n"\'<>|*?]+\.(?:jpg|png|jpeg|gif|webp)',
                    str(results[-1]) if results else "",
                    re.IGNORECASE
                )
                paths = [p.rstrip('.,;)\'"') for p in paths if os.path.exists(p)]

                if paths:
                    t = dict(t)
                    t["task"] = (
                            "USE THESE EXACT LOCAL IMAGE FILES — DO NOT SEARCH FOR NEW ONES:\n"
                            + "\n".join(paths)
                            + f"\n\nTASK: {t['task']}"
                    )

            self.nova.log(f"[EXECUTOR] Sequential → {agent}")

            try:
                result = self._run_agent(t, internet_ctx, history_str)
            except Exception as e:
                self.nova.log(f"[AGENT ERROR] {agent}: {e}")
                result = f"[AGENT ERROR] {str(e)}"

            results.append(result)

            if agent == "text" and result:
                accumulated_context += f"\n{result}"
                accumulated_context = accumulated_context[-self.MAX_CONTEXT_CHARS:]

            if agent == "file_explorer" and result:
                if i + 1 < len(tasks):
                    next_task = tasks[i + 1]
                    if next_task.get("agent") == "file_explorer" and "open" in next_task.get("task", "").lower():
                        paths = re.findall(
                            r'[A-Za-z]:[/\\][^\s\n(]+\.(?:mp3|wav|flac|ogg|mp4|mkv)',
                            str(result),
                            re.IGNORECASE
                        )
                        paths = [p.rstrip('.,;)\'"') for p in paths if os.path.exists(p)]
                        if paths:
                            tasks[i + 1] = dict(next_task)
                            tasks[i + 1]["task"] = f"open {paths[0]}"
                            self.nova.log(f"[EXECUTOR] Injected path: open {paths[0]}")

                result_str = str(result)
                audio_match = re.search(
                    r'([A-Za-z]:[/\\][^\n]+?\.(?:mp3|wav))',
                    result_str,
                    re.IGNORECASE
                )

                if audio_match:
                    file_path = audio_match.group(1).rstrip('.,;)\'"')
                    if os.path.exists(file_path):
                        self.nova.log(f"[AUTO] Playing → {file_path}")
                        play_result = self._run_agent(
                            {"agent": "play_local_music", "task": f"play {file_path}"},
                            internet_ctx,
                            history_str
                        )
                        results.append(play_result)
                        early_exit = True
                        break

                elif i + 1 < len(tasks) and tasks[i + 1].get("agent") == "text":
                    tasks[i + 1] = dict(tasks[i + 1])
                    tasks[i + 1]["task"] = (
                        f"FILE SEARCH RESULTS:\n{result}\n\nTASK: {tasks[i + 1]['task']}"
                    )

            if agent == "self_inspect" and isinstance(result, str):
                clean = result.split("||", 1)[1].strip() if "||" in result else result
                accumulated_context += f"\nSOURCE CODE INSPECTION RESULT:\n{clean}"
                accumulated_context = accumulated_context[-self.MAX_CONTEXT_CHARS:]
                self.nova.log(f"[SELF_INSPECT] Accumulated {len(clean)} chars")
                results[-1] = f"[Self-inspection complete — {len(clean)} chars passed to next agent]"
                i += 1
                continue

            if agent == "research":
                self.nova.log(f"[RESEARCH RESULT] {str(result)[:300] if result else 'EMPTY'}")
                if result and not str(result).startswith("[AGENT ERROR]"):
                    is_failure = any(p in str(result).lower() for p in [
                        "no valid url", "not available", "not found", "cannot find",
                        "recommend searching", "unable to"
                    ])
                    if is_failure and not re.search(r'https?://', str(result)):
                        self.nova.log("[EXECUTOR] Research found nothing actionable — stopping")
                        early_exit = True
                        break
                    accumulated_context += f"\n{result}"
                    accumulated_context = accumulated_context[-self.MAX_CONTEXT_CHARS:]

            i += 1

        if early_exit:
            self.nova.log(f"[EXECUTOR] Early exit after {len(results)} of {len(tasks)} tasks")

        return results

    # ─────────────────────────────────────────
    # AGENT RUNNER
    # ─────────────────────────────────────────
    def _run_agent(self, task, internet_ctx="", history_str=""):
        """
        Execute a single agent task

        Args:
            task: Dictionary with 'agent' and 'task' keys
            internet_ctx: Internet context string
            history_str: Conversation history to provide context
        """
        agent = task.get("agent", "text")
        job = task.get("task", "")

        self.nova.log(f"[DEBUG] RUN AGENT → {agent}")

        formatted_history = ""
        if history_str and agent in ["text", "math", "research"]:
            formatted_history = self._format_history_for_agent(history_str)
            self.nova.log(f"[AGENT] {agent} received {len(formatted_history)} chars of history")

        try:
            tool_map = {
                "play_local_music": "play_local_music",
                "play_local_video": "play_local_video",
                "youtube_tools": "play_youtube_video",
                "file_explorer": "file_explorer",
                "open_webpage": "open_webpage",
                "self_inspect": "self_inspect",
                "search_and_show_image": "search_and_show_image"
            }

            if agent == "file_explorer":
                job = self._translate_file_command(job)

            # ── TOOL EXECUTION ─────────────────
            if agent in tool_map:
                tool_name = tool_map[agent]
                self.nova.log(f"[TOOL EXEC] {agent} → {tool_name}")

                if tool_name == "search_and_show_image":
                    clean_job = job.lower()

                    count_map = {"two": 2, "three": 3, "four": 4, "five": 5,
                                 "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
                    requested_count = 6
                    for word, num in count_map.items():
                        if word in clean_job:
                            requested_count = num
                            break
                    digit_match = re.search(r'\b(\d+)\b', clean_job)
                    if digit_match:
                        requested_count = int(digit_match.group(1))

                    strip_phrases = [
                        "find", "search for", "get", "download", "fetch",
                        "images of", "pictures of", "photos of", "image of",
                        "four", "three", "two", "five", "six",
                        "and put them on a poster", "for a poster", "poster",
                        "collage", "display", "layout", "arrange",
                        "and display", "and show", "and arrange"
                    ]
                    for phrase in strip_phrases:
                        clean_job = clean_job.replace(phrase, "")

                    and_pos = clean_job.find(" and ")
                    if and_pos != -1:
                        after_and = clean_job[and_pos + 5:]
                        instruction_words = ["put", "place", "make", "create", "build", "arrange",
                                             "display", "show", "use", "combine", "design"]
                        if any(after_and.startswith(w) for w in instruction_words):
                            clean_job = clean_job[:and_pos]

                    clean_job = re.sub(r'\s+', ' ', clean_job).strip()
                    clean_job = f"{requested_count} {clean_job}"
                    self.nova.log(f"[IMAGE SEARCH] Cleaned query: '{clean_job}' count={requested_count}")

                    return self.nova.tools.run(
                        tool_name,
                        clean_job,
                        self.nova.ai.internet,
                        self.nova.image_dir,
                    )

                elif tool_name == "open_webpage":
                    return self.nova.tools.run(
                        tool_name,
                        job,
                        internet_tools=self.nova.ai.internet
                    )

                else:
                    return self.nova.tools.run(tool_name, job)

            # ── DIAGRAM ────────────────────────
            if agent == "diagram":
                self.nova.log(f"[AGENT] diagram → {job}")
                result = self.nova.tools.run("diagram", job, self.nova.ai)
                if isinstance(result, str) and result.startswith("DIAGRAM:"):
                    path = result.split(":", 1)[1].strip()
                    self.nova.root.after(0, lambda p=path: self.nova.show_graphviz_diagram(p))
                    return "[DIAGRAM GENERATED]"
                return result or "[DIAGRAM FAILED]"

            # ── WRITE FILE ─────────────────────
            if agent == "write_file":

                # Extract the file path — anchored to end of string, Windows paths only
                path_match = re.search(
                    r'\bto\s+([A-Za-z]:[/\\][^\n\s]+\.[\w]+)\s*$',
                    job,
                    re.IGNORECASE
                )
                if not path_match:
                    self.nova.log("[WRITE_FILE] No file path found in task")
                    return "❌ Write failed: No file path found in task"

                file_path = path_match.group(1).strip().rstrip('.,;)\'"')

                # If context was prepended, extract the original task after TASK:
                if "TASK:" in job:
                    task_body = job.split("TASK:", 1)[1].strip()
                else:
                    task_body = job

                # If task body is just a short description, content is in the context block
                if "TASK:" in job and len(task_body.split("\n")[0]) < 200:
                    context_block = job.split("TASK:")[0]
                    context_block = re.sub(
                        r'^CONTEXT FROM PREVIOUS INSPECTION:\s*',
                        '',
                        context_block,
                        flags=re.IGNORECASE
                    ).strip()
                    # FIX: no slice — write_file gets full context
                    content = context_block
                else:
                    # Content embedded in task body — strip everything up to and including the path
                    content = re.sub(
                        r'^.*?[A-Za-z]:[/\\][^\n]+\.[\w]+\s*:?\s*',
                        '',
                        task_body,
                        flags=re.IGNORECASE | re.DOTALL
                    ).strip()

                # Strip markdown code fences if present
                content = re.sub(r"^```[\w]*\n?", "", content)
                content = re.sub(r"\n?```$", "", content).strip()

                # If content still too short, use full task_body
                if len(content) < 20:
                    self.nova.log("[WRITE_FILE] Content too short — using full task body")
                    content = task_body

                # If still short, try pulling last assistant response from history
                if len(content) < 100 and history_str:
                    history_match = re.search(
                        r'Assistant:\s*(.*?)(?=User:|$)',
                        history_str,
                        re.DOTALL
                    )
                    if history_match:
                        history_content = history_match.group(1).strip()
                        if len(history_content) > len(content):
                            content = history_content
                            self.nova.log(f"[WRITE_FILE] Using history content ({len(content)} chars)")

                # Unescape JSON-encoded strings (literal \n → real newlines)
                if '\\n' in content and '\n' not in content:
                    content = content.encode('utf-8').decode('unicode_escape')

                self.nova.log(f"[WRITE_FILE] → {file_path} ({len(content)} chars)")
                return self.nova.tools.run("write_file", file_path, content)
            # ── RESEARCH ───────────────────────
            if agent == "research":
                job = re.sub(r'\b\w+:\S+\s*', '', job).strip()

                # Build research prompt with history context
                research_prompt = job
                if formatted_history:
                    research_prompt = f"""
CONTEXT FROM RECENT CONVERSATION:
{formatted_history}

CURRENT RESEARCH QUERY:
{job}

Use the context to understand what information is being sought.
"""

                return self.nova.ai.react_agent(
                    research_prompt,
                    self.nova.ai.internet,
                    history=self.nova.build_recent_history(),
                    internet_ctx=internet_ctx,
                    max_steps=6
                )

            # ── CODE ───────────────────────────
            if agent == "code":
                self.nova.log("[CODE] Generating + executing")

                # Build code generation prompt with history context
                code_prompt = job
                if formatted_history:
                    code_prompt = f"""
CONTEXT FROM RECENT CONVERSATION:
{formatted_history}

CODE REQUEST:
{job}

Generate Python code that addresses the request in the context of the conversation.
"""

                code = self.nova.ai.generate_code(code_prompt)
                self.nova.code_window.set_code(code)

                def _update_preview(c=code):
                    try:
                        clean = re.sub(r"```(?:python)?\s*", "", c)
                        clean = re.sub(r"```", "", clean).strip()
                        self.nova.code_display.config(state="normal")
                        self.nova.code_display.delete("1.0", "end")
                        self.nova.code_display.insert("1.0", clean)
                        self.nova.code_display.see("1.0")
                        self.nova.code_display.config(state="disabled")
                    except Exception as e:
                        self.nova.log(f"[CODE PREVIEW] {e}")

                self.nova.root.after(0, _update_preview)

                import threading

                def run_code():
                    success, output, attempts, meta = self.nova.smart_loop.run(code)
                    result = output if success else f"[CODE FAILED] {output}"
                    self.nova.root.after(
                        0,
                        lambda: self.nova._deliver_tool_result(result)
                    )

                threading.Thread(target=run_code, daemon=True).start()
                return "[RUNNING CODE...]"

            # ── SYMPY ──────────────────────────
            if agent == "sympy_exec":
                self.nova.log("[SYMPY] Generating SymPy code...")
                code = self.nova.ai.generate(
                    f"Write executable Python SymPy code only.\n"
                    f"Task: {job}\n"
                    f"Requirements:\n"
                    f"- ONLY Python code, no English text anywhere\n"
                    f"- No comments, no explanations, no prose\n"
                    f"- Define all variables with symbols()\n"
                    f"- End with print(latex(result))\n"
                    f"- If you write anything other than Python code the program will crash",
                    use_planning=False
                )
                code = re.sub(r"```(?:python)?\s*", "", code)
                code = re.sub(r"```", "", code).strip()

                # Always prepend safe imports
                header = "from sympy import *\nfrom sympy import latex\n"
                if "from sympy" not in code:
                    code = header + code
                else:
                    code = "from sympy import latex\n" + code

                result = self.nova.tools.run("sympy_exec", code)
                if result:
                    # Strip any existing formatting the tool may have added
                    clean = result.replace("**SymPy Verification Result:**", "").strip()
                    clean = clean.replace("$$", "").strip()
                    return f"**SymPy Verification Result:**\n\n$$\n{clean}\n$$"
                return "SymPy returned no result"

            # ── MATH / TEXT / FALLBACK ─────────
            if agent == "math":
                # Build math prompt with history context
                math_prompt = job
                if formatted_history:
                    math_prompt = f"""
CONTEXT FROM RECENT CONVERSATION:
{formatted_history}

MATH QUERY:
{job}

IMPORTANT: Do NOT include Python or SymPy code examples. Use LaTeX notation only. 
Verification is handled separately.
"""
                return self.nova.ai.generate(math_prompt, use_planning=False)

            if agent == "text":
                # Build text prompt with history context
                text_prompt = job
                if formatted_history:
                    text_prompt = f"""
RECENT CONVERSATION HISTORY:
{formatted_history}

CURRENT TASK:
{job}

Complete the task using the context from the conversation history. If this is a follow-up question, reference what was discussed.
"""
                self.nova.log(f"[TEXT AGENT] Prompt length: {len(text_prompt)} chars")
                return self.nova.ai.generate(text_prompt, use_planning=False)

            return self.nova.ai.generate(job, use_planning=False)

        except Exception as e:
            return f"[AGENT ERROR] {agent}: {e}"

    # ─────────────────────────────────────────
    # HISTORY FORMATTING
    # ─────────────────────────────────────────
    def _format_history_for_agent(self, history_str, max_exchanges=50):
        """
        Format conversation history for agent consumption

        Args:
            history_str: Raw history string or JSON
            max_exchanges: Maximum number of exchanges to include

        Returns:
            Formatted history string
        """
        if not history_str:
            return ""

        try:
            # Try to parse as JSON if it's a history object
            import json
            if isinstance(history_str, str) and (
                    history_str.strip().startswith('{') or history_str.strip().startswith('[')):
                data = json.loads(history_str)
                if isinstance(data, dict) and 'history' in data:
                    # Extract from nova_state.json format
                    exchanges = []
                    for entry in data['history'][-max_exchanges:]:
                        task = entry.get('task', '')
                        result = entry.get('result', '')
                        # Truncate long results
                        if len(result) > 500:
                            result = result[:500] + "..."
                        exchanges.append(f"User: {task}\nAssistant: {result}")
                    return "\n\n".join(exchanges)
        except:
            pass

        # If it's a string, just return it (truncated)
        if isinstance(history_str, str):
            if len(history_str) > 10000:
                return history_str[:10000] + "\n...[truncated]"
            return history_str

        return str(history_str)

    # ─────────────────────────────────────────
    # FILE COMMAND NORMALIZATION
    # ─────────────────────────────────────────
    def _translate_file_command(self, text):
        text = (text or "").lower().strip()

        noise_phrases = [
            "contents of", "directory of", "folder of", "files in",
            "files and folders in", "list files in",
            "list files and folders in", "show files in",
            "show contents of", "display contents of",
            "display files in", "and folders", "files and",
        ]

        for phrase in noise_phrases:
            text = text.replace(phrase, "")

        text = text.strip()

        if re.match(r"^[a-z]:/", text):
            return f"list {text}"

        if text.startswith("list"):
            parts = text.split()
            for p in parts:
                if re.match(r"^[a-z]:/", p):
                    return f"list {p}"

        if "text file" in text or ".txt" in text:
            return "find *.txt in C:/Users/OEM/Desktop"

        if "desktop" in text and "list" in text:
            return "list C:/Users/OEM/Desktop"

        return text