# self_improver.py
import os
import re
import json
import shutil
from datetime import datetime


class SelfImprover:
    """
    Evolves Nova source files by feeding the whole file to the AI
    and saving the result as a new numbered version.
    """

    def __init__(self, ai, log, source_files=None, running_file=None):
        self.ai = ai
        self.log = log
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.running_file = running_file
        self.base_names = source_files or [
            "nova_assistant",
            "code_execution_loop",
            "latex_window",
            "theme_manager",
            "code_window",
            "mistake_memory",
            "Internet_Tools",
            "math_speech",
            "agent_executor",
        ]
        self.history_file = os.path.join(self.project_root, "self_improvement_log.json")
        self._load_history()

    # ─────────────────────────────────────────────
    # HISTORY
    # ─────────────────────────────────────────────

    def _load_history(self):
        try:
            with open(self.history_file) as f:
                data = json.load(f)
            self.history = data if isinstance(data, list) else []
            self.log(f"[SELF] 📖 Loaded {len(self.history)} evolution entries")
        except FileNotFoundError:
            #self.log("[SELF] 📖 No history file yet — starting fresh")
            self.history = []
        except json.JSONDecodeError as e:
            self.log(f"[SELF] ⚠️ History file corrupted — starting fresh: {e}")
            self.history = []
        except Exception as e:
            self.log(f"[SELF] ❌ History load error: {e}")
            self.history = []

    def _save_history(self):
        try:
            with open(self.history_file, "w") as f:
                json.dump(self.history, f, indent=2)
            self.log(f"[SELF] 📝 History saved → {self.history_file}")
        except Exception as e:
            self.log(f"[SELF] ❌ Could not save history: {e}")

    def _log_entry(self, base_name, version, feature_request, changes_made):
        entry = {
            "timestamp":       datetime.now().isoformat(),
            "file":            base_name,
            "version_created": f"{base_name}_v{version}.py",
            "feature_request": feature_request,
            "changes_made":    changes_made,
            "how_to_use":      f"Run {base_name}_v{version}.py to use this version.",
        }
        self.history.append(entry)
        self._save_history()

    def export_history(self):
        if not self.history:
            return "No evolution history yet."
        lines = []
        for i, e in enumerate(self.history, 1):
            lines.append(
                f"[{i}] {e['timestamp']}\n"
                f"    File    : {e.get('version_created', '?')}\n"
                f"    Request : {e.get('feature_request', '?')}\n"
                f"    Changes : {e.get('changes_made', '?')}\n"
                f"    Run     : {e.get('how_to_use', '?')}\n"
            )
        return "\n".join(lines)

    # ─────────────────────────────────────────────
    # VERSIONING
    # ─────────────────────────────────────────────

    def _get_current_version(self, base_name):
        # If we know which file is running, extract version from it
        if self.running_file and base_name == "nova_assistant":
            fname = os.path.basename(self.running_file)
            m = re.match(rf"^{re.escape(base_name)}_v(\d+)\.py$", fname, re.IGNORECASE)
            if m:
                v = int(m.group(1))
                # Check if a higher version exists and warn
                versions = []
                for f in os.listdir(self.project_root):
                    mm = re.match(rf"^{re.escape(base_name)}_v(\d+)\.py$", f, re.IGNORECASE)
                    if mm:
                        versions.append(int(mm.group(1)))
                if versions and max(versions) > v:
                    self.log(
                        f"[SELF] ⚠️ WARNING: Running v{v} but v{max(versions)} exists "
                        f"— evolution will branch from v{v}"
                    )
                return v

        # Fallback — scan directory for highest version
        versions = []
        for f in os.listdir(self.project_root):
            m = re.match(rf"^{re.escape(base_name)}_v(\d+)\.py$", f, re.IGNORECASE)
            if m:
                versions.append(int(m.group(1)))
        return max(versions) if versions else 1

    def _versioned_filename(self, base_name, version):
        base_norm = base_name.lower().replace("_", "")
        for f in os.listdir(self.project_root):
            m = re.match(rf"^(.+)_v{version}\.py$", f, re.IGNORECASE)
            if m:
                found = m.group(1).lower().replace("_", "")
                if found == base_norm:
                    return f
        return f"{base_name}_v{version}.py"

    def _current_path(self, base_name):
        v = self._get_current_version(base_name)
        path = os.path.join(self.project_root, self._versioned_filename(base_name, v))
        return path, v

    def _next_path(self, base_name):
        current = self._get_current_version(base_name)

        # Find next version number that doesn't already exist
        next_ver = current + 1
        while True:
            filename = f"{base_name}_v{next_ver}.py"
            path = os.path.join(self.project_root, filename)
            if not os.path.exists(path):
                break
            self.log(f"[SELF] ⚠️ v{next_ver} already exists — skipping to v{next_ver + 1}")
            next_ver += 1

        return os.path.join(self.project_root, filename), next_ver

    def read_source(self, base_name):
        path, v = self._current_path(base_name)
        self.log(f"[SELF] Reading {self._versioned_filename(base_name, v)}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _read_plain(self, base_name):
        """Read a non-versioned source file directly"""
        path = os.path.join(self.project_root, f"{base_name}.py")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _write_new_version(self, base_name, new_source, change_description):
        next_path, next_ver = self._next_path(base_name)
        current_ver = next_ver - 1

        # Strip any existing version header
        lines = new_source.split("\n")
        stripped = []
        in_header = True
        for line in lines:
            if in_header:
                if line.startswith("#") or line.strip() == "":
                    continue
                else:
                    in_header = False
                    stripped.append(line)
            else:
                stripped.append(line)
        new_source = "\n".join(stripped)

        header = (
            f"# Version  : {next_ver}\n"
            f"# Evolved  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"# Change   : {change_description}\n"
            f"# Previous : v{current_ver}\n"
            f"# {'─' * 55}\n\n"
        )

        try:
            with open(next_path, "w", encoding="utf-8") as f:
                f.write(header + new_source)
            fname = self._versioned_filename(base_name, next_ver)
            self.log(f"[SELF] ✅ Written {fname}")

            # ── Smoke test ──────────────────────────────────────
            import py_compile
            try:
                py_compile.compile(next_path, doraise=True)
                self.log(f"[SELF] ✅ Smoke test passed: {fname}")
            except py_compile.PyCompileError as e:
                self.log(f"[SELF] ⚠️ SYNTAX ERROR in {fname}: {e}")
                self.log(f"[SELF] ⚠️ Attempting auto-fix...")
                ok, fixed_source = self._retry_patch(change_description, new_source, str(e), attempt=1)

                ok, retry_result = self._retry_patch(change_description, new_source, str(e), attempt=1)
                if ok and retry_result:
                    fixed_source, _, _ = retry_result
                    with open(next_path, "w", encoding="utf-8") as f:
                        f.write(header + fixed_source)

                    # Verify the fix actually compiles
                    try:
                        py_compile.compile(next_path, doraise=True)
                        self.log(f"[SELF] ✅ Auto-fix verified: {fname}")
                    except py_compile.PyCompileError as e2:
                        self.log(f"[SELF] ⚠️ Auto-fix still has errors: {e2}")
                        self.log(f"[SELF] ⚠️ File written but will not run — use DEBUG to fix manually")
                else:
                    self.log(f"[SELF] ⚠️ Auto-fix failed — file written but will not run — use DEBUG to fix manually")

            return True, next_ver

        except PermissionError:
            self.log(f"[SELF] ❌ Windows file lock — close other editors")
            return False, current_ver
        except Exception as e:
            self.log(f"[SELF] ❌ Write failed: {e}")
            return False, current_ver



    def _backup_file(self, base_name):
        """Backup a file before patching in place, using numbered backups"""
        path = os.path.join(self.project_root, f"{base_name}.py")

        # Find next available backup number
        n = 1
        while True:
            backup = os.path.join(self.project_root, f"{base_name}_b{n}.py")
            if not os.path.exists(backup):
                break
            n += 1

        try:
            shutil.copy2(path, backup)
            self.log(f"[SELF] 📋 Backed up {base_name}.py → {base_name}_b{n}.py")
            return True
        except Exception as e:
            self.log(f"[SELF] ❌ Backup failed for {base_name}: {e}")
            return False

    def _write_in_place(self, base_name, new_source, change_description):
        """Write patched source directly to base_name.py (for external files)"""
        path = os.path.join(self.project_root, f"{base_name}.py")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_source)
            self.log(f"[SELF] ✅ Patched in place: {base_name}.py ({change_description})")
            return True
        except PermissionError:
            self.log(f"[SELF] ❌ Permission denied — close {base_name}.py in other editors")
            return False
        except Exception as e:
            self.log(f"[SELF] ❌ Write failed for {base_name}: {e}")
            return False

    def _find_owner_file(self, fn_name, default="nova_assistant"):
        """Search all base files to find which one contains this function"""
        for base in self.base_names:
            try:
                if base == "nova_assistant":
                    path, _ = self._current_path(base)
                else:
                    path = os.path.join(self.project_root, f"{base}.py")
                if not os.path.exists(path):
                    continue
                with open(path, "r", encoding="utf-8") as f:
                    source = f.read()
                if self._function_exists(source, fn_name):
                    self.log(f"[SELF] 🔍 {fn_name} found in {base}.py")
                    return base
            except Exception as e:
                self.log(f"[SELF] ⚠️ Could not search {base}: {e}")
                continue
        self.log(f"[SELF] ⚠️ {fn_name} not found — defaulting to {default}")
        return default

    def _import_check(self, source, step_num):
        """Write source to temp file, py_compile then pyflakes. Returns (ok, error_msg)."""
        import subprocess

        tmp_path = os.path.join(self.project_root, f"_nova_step_check_{step_num}.py")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(source)

            # ── Stage 1: syntax check ─────────────────────────────────────────
            result = subprocess.run(
                ["python", "-m", "py_compile", tmp_path],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode != 0:
                error = result.stderr.strip().replace(tmp_path, "nova_assistant")
                self.log(f"[SELF] ❌ Syntax check failed: {error[:120]}")
                return False, error

            # ── Stage 2: pyflakes undefined name check ────────────────────────
            flakes = subprocess.run(
                ["python", "-m", "pyflakes", tmp_path],
                capture_output=True, text=True, timeout=15
            )

            if flakes.returncode != 0:
                output = flakes.stdout.strip() or flakes.stderr.strip()
                output = output.replace(tmp_path, "nova_assistant")

                # Filter to only fatal errors — ignore unused imports etc.
                fatal_patterns = [
                    "undefined name",
                    "NameError",
                    "undefined",
                    "is not defined",
                ]
                fatal_lines = [
                    line for line in output.split("\n")
                    if any(p in line.lower() for p in fatal_patterns)
                ]

                if fatal_lines:
                    error = "\n".join(fatal_lines)
                    self.log(f"[SELF] ❌ Pyflakes fatal: {error[:200]}")
                    return False, error
                else:
                    # Non-fatal warnings only — pass
                    self.log(f"[SELF] ⚠️ Pyflakes warnings (non-fatal): {output[:120]}")

            self.log(f"[SELF] ✅ Step {step_num} import check passed")
            return True, ""

        except subprocess.TimeoutExpired:
            return False, "Import check timed out"
        except Exception as e:
            return False, str(e)
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _extract_new_classes(self, code):
        """Extract complete class definitions that don't exist in the source."""
        classes = {}
        pattern = re.compile(r'^class (\w+)[:\(]', re.MULTILINE)
        matches = list(pattern.finditer(code))

        for i, match in enumerate(matches):
            class_name = match.group(1)
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(code)
            class_code = code[start:end].rstrip()
            classes[class_name] = class_code

        return classes

    def _extract_error_context(self, source, error_msg):
        """Extract lines around the error line number for AI context."""
        m = re.search(r'line (\d+)', error_msg)
        if not m:
            # No line number — just return the last 2000 chars as context
            return source[-2000:]

        line_num = int(m.group(1))
        lines = source.splitlines()

        start = max(0, line_num - 6)
        end = min(len(lines), line_num + 6)

        context_lines = []
        for i in range(start, end):
            marker = ">>>" if i == line_num - 1 else "   "
            context_lines.append(f"{marker} {i + 1:4d}: {lines[i]}")

        return "\n".join(context_lines)

    def _retry_patch(self, step_description, current_source, error_msg, attempt):
        """Feed error back to AI and get a corrected patch."""
        self.log(f"[SELF] 🔄 Retry attempt {attempt} — error: {error_msg[:100]}")

        context = self._extract_error_context(current_source, error_msg)

        enriched = (
            f"{step_description}\n\n"
            f"Your previous patch caused this error:\n"
            f"{error_msg}\n\n"
            f"Source context around the error:\n"
            f"{context}\n\n"
            f"Fix the patch to resolve this error. "
            f"Return only the corrected methods."
        )

        return self.run_feature_cycle(enriched, source_override=current_source)

    # ─────────────────────────────────────────────
    # VALIDATION
    # ─────────────────────────────────────────────

    def validate_code(self, code):
        import ast
        try:
            ast.parse(code)
            self.log("[SELF] ✅ Syntax check passed")
            return True
        except SyntaxError as e:
            self.log(f"[SELF] ❌ Syntax error: {e}")
            self.log(f"[SELF] ❌ Code preview: {code[:300]}")
            return False

    # ─────────────────────────────────────────────
    # SIGNATURES
    # ─────────────────────────────────────────────

    def _extract_signatures(self, source):
        """Extract all def and class lines for use as a compact code map."""
        return "\n".join(
            line for line in source.split("\n")
            if line.strip().startswith(("def ", "class ", "async def "))
        )

    def _extract_all_signatures(self):
        """Extract signatures from all known source files"""
        all_sigs = {}

        for base in self.base_names:
            try:
                if base == "nova_assistant":
                    source = self.read_source(base)
                else:
                    source = self._read_plain(base)
                sigs = self._extract_signatures(source)
                if sigs.strip():
                    all_sigs[base] = sigs
                    self.log(f"[SELF] 📋 Read signatures from {base}.py ({len(sigs)} chars)")
            except Exception as e:
                self.log(f"[SELF] ⚠️ Could not read {base}: {e}")
                continue

        return all_sigs

    # ─────────────────────────────────────────────
    # FUNCTION HELPERS
    # ─────────────────────────────────────────────

    def _split_into_functions(self, code):
        """Split a code block into a dict of name→code, each normalised to 0 indent."""
        SKIP_NAMES = {'_patched', '_ins', '_load', '_poll', '_upd', '_proc',
                      '_record', '_worker', '_restore', '_go', '_yes', '_no'}

        functions = {}
        pattern = re.compile(r'^(    def |def )(\w+)\s*\(', re.MULTILINE)
        matches = list(pattern.finditer(code))

        for i, match in enumerate(matches):
            fn_name = match.group(2)

            if fn_name in SKIP_NAMES:
                continue

            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(code)
            fn_code = code[start:end].rstrip()

            lines = fn_code.split("\n")
            non_empty = [l for l in lines if l.strip()]
            if non_empty:
                min_ind = min(len(l) - len(l.lstrip()) for l in non_empty)
                fn_code = "\n".join(
                    l[min_ind:] if l.strip() else ""
                    for l in lines
                )

            functions[fn_name] = fn_code

        return functions

    def _function_exists(self, source, function_name):
        """Check if a function exists in the source."""
        return bool(re.search(
            rf"(    def {function_name}|def {function_name})\s*\(",
            source
        ))

    # ─────────────────────────────────────────────
    # MAIN CYCLES
    # ─────────────────────────────────────────────
    def _decompose_feature(self, feature_request):
        """Ask the AI to break a large feature into ordered atomic steps."""
        prompt = f"""You are planning how to implement a feature in a Python application.

    FEATURE REQUEST:
    {feature_request}

    Break this into 3-6 small, ordered, atomic implementation steps.
    Each step should be independently implementable and testable.
    Each step should build on the previous one.

    RULES:
    - One step per line
    - Number each step: 1. 2. 3. etc.
    - Each step must be a concrete coding action (add a method, modify a 
      method, add a UI element, wire up a callback)
    - Do NOT include testing or documentation steps
    - Keep each step to one sentence
    - Do NOT number higher than 6

    Return ONLY the numbered list, nothing else.
    """
        result = self.ai.generate(prompt, use_planning=False).strip()

        steps = []
        for line in result.split("\n"):
            line = line.strip()
            m = re.match(r'^\d+[\.\)]\s*(.+)', line)
            if m:
                steps.append(m.group(1).strip())

        # Sanity check — if AI returned garbage, treat as single step
        if not steps:
            self.log("[SELF] ⚠️ Decomposition failed — treating as single step")
            return [feature_request]

        self.log(f"[SELF] 📋 Decomposed into {len(steps)} steps:")
        for i, s in enumerate(steps, 1):
            self.log(f"[SELF]   {i}. {s}")

        return steps

    def run_multi_step_feature(self, feature_request, progress_callback=None):
        """
        Decompose a large feature into steps and apply them sequentially,
        passing the evolving source forward between steps.
        Returns (success, final_nova_source, summary_message).
        """
        self.log(f"[SELF] 🚀 Multi-step feature: {feature_request}")

        steps = self._decompose_feature(feature_request)

        # Seed with current source
        working_source = self.read_source("nova_assistant")
        all_changes = []
        failed_steps = []
        consecutive_failures = 0
        MAX_RETRIES = 2

        for i, step in enumerate(steps, 1):

            if progress_callback:
                progress_callback(i, len(steps), step)

            self.log(f"\n[SELF] ── Step {i}/{len(steps)}: {step}")

            # Enrich step with overall goal context
            enriched = (
                f"{step}\n\n"
                f"[This is step {i} of {len(steps)} implementing: {feature_request}]"
            )

            success, result = self.run_feature_cycle(enriched, source_override=working_source)

            if not success:
                # Step 1 failing means nothing was built yet — abort immediately
                if i == 1:
                    return False, None, f"Step 1 failed — aborting: {result}"
                consecutive_failures += 1
                self.log(f"[SELF] ⚠️ Step {i} failed: {result}")
                failed_steps.append(i)
                if consecutive_failures >= 2:
                    summary = "\n".join(all_changes)
                    return True, working_source, (
                        f"Aborted at step {i} — two consecutive failures.\n\n{summary}"
                    )
                continue

            nova_source, msg, nova_was_patched = result
            candidate_source = nova_source if nova_was_patched else working_source

            # ── Import check ──────────────────────────────────────────────────────
            ok, error_msg = self._import_check(candidate_source, i)

            if not ok:
                self.log(f"[SELF] ⚠️ Step {i} failed import check — retrying")

                retry_success = False
                for attempt in range(1, MAX_RETRIES + 1):
                    success, result = self._retry_patch(enriched, candidate_source, error_msg, attempt)

                    if not success:
                        self.log(f"[SELF] ❌ Retry {attempt} — patch generation failed")
                        continue

                    nova_source, msg, nova_was_patched = result
                    candidate_source = nova_source if nova_was_patched else working_source

                    ok, error_msg = self._import_check(candidate_source, i)
                    if ok:
                        self.log(f"[SELF] ✅ Step {i} passed after retry {attempt}")
                        retry_success = True
                        break
                    else:
                        self.log(f"[SELF] ❌ Retry {attempt} still failing: {error_msg[:80]}")

                if not retry_success:
                    consecutive_failures += 1
                    failed_steps.append(i)
                    self.log(f"[SELF] ❌ Step {i} abandoned after {MAX_RETRIES} retries")

                    if i == 1:
                        return False, None, f"Step 1 could not be fixed — aborting."

                    if consecutive_failures >= 2:
                        summary = "\n".join(all_changes)
                        return True, working_source, (
                            f"Aborted at step {i} — two consecutive failures.\n\n{summary}"
                        )
                    continue

            # ── Step passed — advance working source ──────────────────────────────
            consecutive_failures = 0
            working_source = candidate_source
            all_changes.append(f"Step {i}: {msg.split(chr(10))[0]}")
            self.log(f"[SELF] ✅ Step {i} complete")

        # ── Final result ──────────────────────────────────────────────────────────
        if not all_changes:
            return False, None, "All steps failed — nothing was changed."

        summary = "\n".join(all_changes)
        if failed_steps:
            summary += f"\n\nSkipped steps: {failed_steps}"

        self.log(f"[SELF] 🏁 Multi-step complete — {len(all_changes)}/{len(steps)} steps applied")
        return True, working_source, summary

    def run_debug_cycle(self, symptom):
        """Send source + reported symptom to AI and get a targeted fix."""
        self.log(f"[SELF] 🔍 Debug symptom: {symptom}")

        debug_request = f"""DEBUG REQUEST — fix this reported problem:

    SYMPTOM:
    {symptom}

    INSTRUCTIONS:
    - This is a bug fix, NOT a new feature
    - Find the root cause in the existing code
    - Return only the corrected method(s)
    - Do NOT add new functionality
    - Focus on fixing exactly what is broken
    - Pay close attention to silent exceptions, missing prefixes, 
      wrong variable names, and scope errors"""

        return self.run_feature_cycle(debug_request)

    def run_documentation_cycle(self, base_name="nova_assistant",
                                progress_callback=None):
        """
        Add docstrings to every undocumented method one at a time.
        Each method is sent individually — small fast API calls.
        Returns (success, documented_source, summary)
        """
        import ast
        import re

        self.log("[DOC] Starting documentation cycle...")

        source = self.read_source(base_name)
        if not source:
            return False, None, "Could not read source"

        # ── Find all methods without docstrings ───────────────────────────────
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return False, None, f"Source has syntax error: {e}"

        undocumented = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                has_docstring = (
                        node.body and
                        isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, ast.Constant) and
                        isinstance(node.body[0].value.value, str)
                )
                if not has_docstring:
                    undocumented.append({
                        "name": node.name,
                        "lineno": node.lineno,
                        "end_lineno": node.end_lineno,
                    })

        total = len(undocumented)
        self.log(f"[DOC] Found {total} undocumented methods")

        if total == 0:
            return True, source, "All methods already have docstrings"

        # ── Process each method ───────────────────────────────────────────────
        lines = source.splitlines()
        documented_count = 0
        failed_count = 0
        consecutive_failures = 0
        original_max_tokens = self.ai.max_tokens
        replacements = {
            "\u2014": "-",  # em dash —
            "\u2013": "-",  # en dash –
            "\u2018": "'",  # left single quote '
            "\u2019": "'",  # right single quote '
            "\u201C": '"',  # left double quote "
            "\u201D": '"',  # right double quote "
            "\u2026": "...",  # ellipsis …
            "\u00d7": "*",  # multiplication ×
            "\u00f7": "/",  # division ÷
            "\u2192": "->",  # arrow →
            "\u2190": "<-",  # left arrow ←
        }


        # Process in reverse order so line numbers stay valid as we insert
        undocumented_sorted = sorted(undocumented, key=lambda x: x["lineno"], reverse=True)
        for i, method_info in enumerate(undocumented_sorted):

            name = method_info["name"]
            start = method_info["lineno"] - 1
            end = method_info["end_lineno"]

            # Extract just this method
            method_lines = lines[start:end]
            method_source = "\n".join(method_lines)

            # Skip if fragment — no def statement
            if not any(l.strip().startswith("def ") for l in method_lines):
                self.log(f"[DOC] ⚠️ {name} — skipping fragment (no def found)")
                failed_count += 1
                continue

            # Large methods need more tokens
            method_line_count = len(method_lines)
            if method_line_count > 60:
                self.ai.max_tokens = 3000
            elif method_line_count > 30:
                self.ai.max_tokens = 2000
            else:
                self.ai.max_tokens = 1000

            if progress_callback:
                progress_callback(
                    i + 1, total,
                    f"Documenting {name} ({i + 1}/{total})..."
                )

            # Ask AI for just the docstring
            prompt = f"""Add a concise docstring to this Python method.
    Rules:
- Return ONLY the complete method with docstring added
- Keep the docstring brief — 1-3 lines maximum
- Describe what the method does, not how
- Do NOT change any logic or code
- Do NOT add inline comments
- ALWAYS use triple double quotes: \"\"\"like this\"\"\"
- NEVER use single quotes for docstrings
- NEVER use em dashes — use hyphens - instead
- Wrap in ```python ... ``` block

    METHOD:
    {method_source}
    """
            try:
                response = self.ai.generate(prompt, use_planning=False)
                if not response:
                    failed_count += 1
                    consecutive_failures += 1
                    if consecutive_failures >= 3:
                        self.log("[DOC] ❌ 3 consecutive failures — aborting")
                        break
                    continue

                consecutive_failures = 0  # reset on success

                # Extract code from response
                code_match = re.search(
                    r'```python\s*(.*?)```',
                    response,
                    re.DOTALL
                )

                if not code_match:
                    failed_count += 1
                    self.log(f"[DOC] ⚠️ {name} — no ```python block in response")
                    self.log(f"[DOC] Response was: {response[:200]}")
                    continue

                new_method = code_match.group(1).strip()

                if not new_method:
                    failed_count += 1
                    self.log(f"[DOC] ⚠️ {name} — empty code block")
                    continue

                # Replace original method lines with documented version
                # ── Preserve original indentation ─────────────────────────
                # Detect indent of original first line
                original_first = method_lines[0] if method_lines else ""
                original_indent = len(original_first) - len(original_first.lstrip())
                original_prefix = " " * original_indent

                # Detect indent of returned first line
                new_method_lines = new_method.splitlines()
                if not new_method_lines:
                    failed_count += 1
                    continue

                returned_first = new_method_lines[0]
                returned_indent = len(returned_first) - len(returned_first.lstrip())



                # Reindent if mismatch
                if returned_indent != original_indent:
                    # Hard guard — if original was indented and returned is not
                    if original_indent >= 4 and returned_indent == 0:
                        new_method_lines = [
                            " " * original_indent + line if line.strip() else line
                            for line in new_method_lines
                        ]
                    elif returned_indent > original_indent:
                        # AI added too much indent — strip the excess
                        indent_diff = returned_indent - original_indent
                        new_method_lines = [
                            line[indent_diff:] if line.strip() and len(line) >= indent_diff else line
                            for line in new_method_lines
                        ]
                    else:
                        indent_diff = original_indent - returned_indent
                        fixed_lines = []
                        for line in new_method_lines:
                            if line.strip() == "":
                                fixed_lines.append("")
                            elif indent_diff > 0:
                                fixed_lines.append(" " * indent_diff + line)
                            else:
                                strip_amount = min(abs(indent_diff),
                                                   len(line) - len(line.lstrip()))
                                fixed_lines.append(line[strip_amount:])
                        new_method_lines = fixed_lines

                lines[start:end] = new_method_lines
                documented_count += 1

                self.log(f"[DOC] ✅ {name}")

            except Exception as e:
                self.log(f"[DOC] ⚠️ {name} failed: {e}")
                import traceback
                self.log(traceback.format_exc())
                failed_count += 1
                continue
        # ── Restore max_tokens ─────────────────────────────────────────────────
        self.ai.max_tokens = original_max_tokens

        documented_source = "\n".join(lines)

        # Final sanitization pass — remove Unicode that breaks Python syntax
        for bad, good in replacements.items():
            documented_source = documented_source.replace(bad, good)

        # Fix single-quoted docstrings containing apostrophes
        documented_source = documented_source.replace("'''", '"""')
        # Verify it still compiles
        import py_compile
        import tempfile
        try:
            with tempfile.NamedTemporaryFile(
                    mode='w', suffix='.py',
                    delete=False, encoding='utf-8'
            ) as f:
                f.write(documented_source)
                tmp = f.name
            py_compile.compile(tmp, doraise=True)
            import os
            os.unlink(tmp)
        except py_compile.PyCompileError as e:
            return False, None, f"Documented source has syntax error: {e}"

        summary = (f"Documented {documented_count}/{total} methods. "
                   f"{failed_count} skipped.")
        self.log(f"[DOC] ✅ {summary}")

        return True, documented_source, summary

    def run_diagnostic(self, source):
        """
        Analyse source code and return a structured diagnostic report
        identifying dead code, issues, and improvement opportunities.
        """
        self.log("[DIAGNOSTIC] Analysing source code...")

        prompt = f"""You are a senior Python code reviewer performing a diagnostic analysis.

    Analyse this Python source code and identify ALL of the following issues:

    1. DEAD CODE - methods defined but never called, imports never used,
       attributes set but never read
    2. DUPLICATE LOGIC - similar code blocks repeated in multiple places
    3. ORPHANED ATTRIBUTES - self.x set in __init__ but never used elsewhere
    4. MISSING ERROR HANDLING - bare except blocks, unguarded API calls,
       missing finally clauses
    5. PIPELINE ISSUES - state not reset correctly, indicators not turned off,
       callbacks not cleaned up
    6. TOKEN WASTE - prompts that are unnecessarily verbose or repeated
    7. MISSING DOCSTRINGS - methods with no documentation
    8. CODE QUALITY - anything that could cause subtle bugs or maintenance problems

    FORMAT your response EXACTLY like this for each issue:

    WARNING METHOD_NAME - issue description
    CRITICAL METHOD_NAME - critical issue description
    SUGGESTION METHOD_NAME - improvement suggestion

    Group issues by category with a header like:
    ## DEAD CODE
    ## DUPLICATE LOGIC
    ## MISSING DOCSTRINGS
    etc.

    Be specific - name the exact method and describe the exact problem.
    Do NOT suggest architectural rewrites - focus on specific fixable issues.

    SOURCE CODE:
    {source[:60000]}
    """

        report = self.ai.generate(prompt, use_planning=False)

        if not report:
            return "Diagnostic failed - no response from model."

        self.log(f"[DIAGNOSTIC] Report generated - {len(report)} chars")
        return report

    def _parse_diagnostic_issues(self, report):
        """
        Extract individual issues from diagnostic report as a list.
        Returns list of issue strings.
        """
        issues = []
        for line in report.splitlines():
            line = line.strip()
            if line.startswith(("WARNING ", "CRITICAL ", "SUGGESTION ")):
                issues.append(line)
        return issues

    def run_debug_cycle_on_file(self, symptom, target_path):
        """Debug a specific external file — returns complete fixed source."""
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                target_source = f.read()
            self.log(f"[DEBUG] Reading target: {os.path.basename(target_path)}")
        except Exception as e:
            return False, f"Could not read {target_path}: {e}"

        prompt = f"""Fix the following problems in this Python file.

    SYMPTOMS:
    {symptom}

    INSTRUCTIONS:
    - Return the COMPLETE fixed Python file
    - Do NOT return just the changed methods
    - Fix only the reported issues
    - Do NOT add new features
    - Wrap the entire file in ```python ... ``` block

    SOURCE CODE:
    {target_source[:20000]}
    """
        result = self.ai.generate(prompt, use_planning=False)

        if "```python" not in result:
            return False, "AI did not return a code block."

        start = result.find("```python") + 9
        end = result.find("```", start)
        fixed_source = result[start:end].strip()

        if not fixed_source:
            return False, "Empty code block returned."

        self.log(f"[DEBUG] External file fixed - {len(fixed_source)} chars")
        return True, (fixed_source, "External file fixed", False)

    def run_feature_cycle(self, feature_request, source_override=None):
        """
        Send signatures + feature request to AI.
        AI returns only changed/added methods.
        Patch those into the correct source files and save.
        """
        self.log(f"[SELF] 🔧 Feature: {feature_request}")

        # Read nova_assistant source (always needed)
        source = source_override if source_override is not None else self.read_source("nova_assistant")

        # Detect primary target file from feature request
        primary_target = "nova_assistant"
        request_lower = feature_request.lower()
        for base in self.base_names:
            if base == "nova_assistant":
                continue
            base_short = base.split("/")[-1].lower()
            if re.search(rf'\b{re.escape(base_short)}\b', request_lower):
                primary_target = base
                self.log(f"[SELF] 🎯 Primary target detected: {base}")
                break
        # Read all signatures from all files
        all_sigs = self._extract_all_signatures()

        # Format signatures for prompt
        sigs_text = ""
        for base, sigs in all_sigs.items():
            sigs_text += f"\n{'=' * 40}\n{base}.py\n{'=' * 40}\n{sigs}\n"

        # Read full source of all external files for the prompt
        # Only load full source of files explicitly mentioned in the feature request
        external_sources = ""
        request_lower = feature_request.lower()
        files_mentioned = []

        for base in self.base_names:
            if base == "nova_assistant":
                continue
            base_short = base.split("/")[-1].lower().replace("_", " ")
            base_nospace = base.split("/")[-1].lower().replace("_", "")
            if base_short in request_lower or base_nospace in request_lower:
                files_mentioned.append(base)

        if files_mentioned:
            for base in files_mentioned:
                try:
                    src = self._read_plain(base)
                    external_sources += f"\n{'=' * 40}\nFULL SOURCE: {base}.py\n{'=' * 40}\n{src}\n"
                    self.log(f"[SELF] 📄 Included full source of {base}.py (mentioned in request)")
                except Exception as e:
                    self.log(f"[SELF] ⚠️ Could not read {base}: {e}")
        else:
            self.log("[SELF] 📄 No external files mentioned — using signatures only")

        prompt = f"""You are evolving the Nova Assistant application.

    FEATURE REQUEST:
    {feature_request}

    FILES YOU CAN MODIFY:
    - nova_assistant — main app, UI, conversation loop
    - code_window — sandbox execution window
    - code_execution_loop — AI coding loop
    - mistake_memory — lesson storage
    - Internet_Tools — web search
    - math_speech — maths TTS conversion
    - planner — task planning
    - agent_executor — agent execution

    NOVA CONVENTIONS:
    - self.conversation_history for history (never self._history)
    - entry["content"] for message text (never entry["text"])
    - self.log() for all logging (never print())
    - os.path.join(os.path.dirname(os.path.abspath(__file__)), filename) for paths
    - NEVER use timestamped filenames — use fixed names like 'conversation_history.json'
    - self.root.after(0, callable) for UI updates from background threads

    ALL METHOD SIGNATURES ACROSS ALL FILES:
    {sigs_text}

    FULL SOURCE OF ALL EXTERNAL FILES:
    {external_sources}

    FULL NOVA ASSISTANT SOURCE CODE FOR REFERENCE:
    {source}

    INSTRUCTIONS:
    1. Read the full source of all files above carefully
    2. Implement the feature by directly modifying the appropriate file(s)
    3. Return ONLY the complete methods that need to be added or changed
    4. Put ALL methods in a single ```python block
    5. Each method must use the exact attribute names from the source above
    6. After the closing ``` write:
       CHANGES: <one sentence>
       MODIFIED: <comma separated list of existing methods you rewrote>
       ADDED: <comma separated list of brand new methods>

    Do NOT return the entire file. Return only the affected methods.

    """

        self.log("[SELF] Sending signatures + feature request to AI...")
        result = self.ai.generate(prompt, use_planning=False)

        if "```python" not in result:
            return False, "AI did not return a code block."

        start = result.find("```python") + 9
        end = result.find("```", start)
        new_code = result[start:end].strip()

        if not new_code:
            return False, "Empty code block returned."

        if "def " not in new_code and "SYSTEM_PROMPT" not in new_code and "=" not in new_code:
            self.log(f"[SELF] ❌ AI returned non-code content: {new_code[:200]}")
            return False, "AI returned documentation instead of code — try again."

        self.log(f"[SELF] Code preview: {new_code[:200]}")
        post_code = result[end + 3:].strip()
        changes_match = re.search(r'CHANGES:\s*(.+)', post_code, re.IGNORECASE)
        modified_match = re.search(r'MODIFIED:\s*(.+)', post_code, re.IGNORECASE)
        added_match = re.search(r'ADDED:\s*(.+)', post_code, re.IGNORECASE)

        changes_made = changes_match.group(1).strip() if changes_match else "Feature implemented"
        modified_names = [m.strip() for m in modified_match.group(1).split(",")] if modified_match else []
        added_names = [m.strip() for m in added_match.group(1).split(",")] if added_match else []

        self.log(f"[SELF] Modified: {modified_names}")
        self.log(f"[SELF] Added:    {added_names}")

        fn_blocks = self._split_into_functions(new_code)

        if not fn_blocks:
            if "SYSTEM_PROMPT" in new_code:
                self.log("[SELF] No functions found but SYSTEM_PROMPT detected — continuing")
            else:
                return False, "Could not parse any functions from the response."

            # Group functions by their owner file
        file_patches = {}

        # ── Handle new class definitions ─────────────────────────────────────
        new_classes = self._extract_new_classes(new_code)
        skip_from_classes = set()  # ← add this

        for class_name, class_code in new_classes.items():
            owner_source = file_patches.get("nova_assistant", source)
            if f"class {class_name}" not in owner_source:
                insert_markers = [
                    "\n# ==========================================\n# NOVA ASSISTANT",
                    "\nclass NovaAssistant:"
                ]
                inserted = False
                for marker in insert_markers:
                    if marker in owner_source:
                        pos = owner_source.find(marker)
                        owner_source = (
                                owner_source[:pos]
                                + "\n\n"
                                + class_code
                                + "\n"
                                + owner_source[pos:]
                        )
                        file_patches["nova_assistant"] = owner_source
                        self.log(f"[SELF] ✅ Inserted new class: {class_name}")
                        inserted = True
                        # ← collect method names belonging to this class
                        for name in self._split_into_functions(class_code):
                            skip_from_classes.add(name)
                        break
                if not inserted:
                    self.log(f"[SELF] ⚠️ Could not find insert point for class: {class_name}")
        ###############
        if fn_blocks:
            for fn_name, fn_code in fn_blocks.items():
                if fn_name in skip_from_classes:  # ← add this
                    self.log(f"[SELF] ⏭ Skipping {fn_name} — belongs to newly inserted class")
                    continue
                owner = self._find_owner_file(fn_name, default="nova_assistant")

                if owner not in file_patches:
                    if owner == "nova_assistant":
                        file_patches[owner] = source
                    else:
                        try:
                            file_patches[owner] = self._read_plain(owner)
                        except Exception as e:
                            self.log(f"[SELF] ❌ Could not read {owner}: {e}")
                            continue

                # Normalise indentation
                lines = fn_code.strip().split("\n")
                min_ind = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
                normalised = "\n".join(
                    "    " + l[min_ind:] if l.strip() else ""
                    for l in lines
                )

                working = file_patches[owner]

                if self._function_exists(working, fn_name):
                    pattern = rf"(    def {fn_name}|def {fn_name})\s*\("
                    match = re.search(pattern, working)
                    if match:
                        s = match.start()
                        indent = "    " if working[s] == " " else ""
                        next_d = re.search(rf"\n{indent}def |\n{indent}class ", working[match.end():])
                        e = match.end() + next_d.start() if next_d else len(working)
                        working = working[:s] + normalised + "\n\n" + working[e:]
                        self.log(f"[SELF] ✅ Patched: {fn_name} in {owner}")
                else:
                    run_match = re.search(r"\n    def run\(", working)
                    insert_pos = run_match.start() if run_match else len(working) - 1
                    working = working[:insert_pos] + "\n\n" + normalised + working[insert_pos:]
                    self.log(f"[SELF] ✅ Inserted: {fn_name} in {owner}")

                file_patches[owner] = working

        # Handle class variable replacements (e.g. SYSTEM_PROMPT)
        if "SYSTEM_PROMPT" in new_code and "def " not in new_code:
            new_prompt_match = re.search(r'SYSTEM_PROMPT\s*=\s*""".*?"""', new_code, re.DOTALL)
            if new_prompt_match:
                new_prompt = new_prompt_match.group(0)
                working = file_patches.get("nova_assistant", source)
                pattern = r'SYSTEM_PROMPT\s*=\s*""".*?"""'
                working = re.sub(pattern, new_prompt, working, flags=re.DOTALL)
                file_patches["nova_assistant"] = working
                self.log("[SELF] ✅ Patched SYSTEM_PROMPT in nova_assistant")

        # Write patched external files — backup only files that actually changed

        for owner, patched_source in file_patches.items():
            if owner == "nova_assistant":
                continue
            self._backup_file(owner)
            self._write_in_place(owner, patched_source, changes_made)

        # Build full change message including external files
        patched_externals = [k for k in file_patches if k != "nova_assistant"]
        msg = (
            f"Changes: {changes_made}\n"
            f"Modified: {', '.join(modified_names) or 'none'}\n"
            f"Added: {', '.join(added_names) or 'none'}\n"
            f"External files patched: {', '.join(patched_externals) or 'none'}"
        )

        nova_source = file_patches.get("nova_assistant", source)
        nova_was_patched = "nova_assistant" in file_patches
        return True, (nova_source, msg, nova_was_patched)

    def run_improvement_cycle(self):
        """Find and fix one weakness using function-level patching."""
        self.log("[SELF] 🧬 Starting improvement cycle...")

        source = self.read_source("nova_assistant")
        sigs = self._extract_signatures(source)
        mistakes = ""
        if hasattr(self.ai, "mistake_memory"):
            mistakes = self.ai.mistake_memory.export_lessons()

        prompt = f"""You are improving the Nova Assistant application.

PAST MISTAKES TO AVOID:
{mistakes}

IMPROVEMENT HISTORY (do not repeat):
{json.dumps(self.history[-5:], indent=2)}

EXISTING METHOD SIGNATURES:
{sigs}

NOVA CONVENTIONS:
- self.conversation_history for history
- entry["content"] for message text
- self.log() for all logging
- os.path.join(os.path.dirname(os.path.abspath(__file__)), filename) for paths
- self.root.after(0, callable) for UI updates from background threads

INSTRUCTIONS:
1. Pick ONE small safe improvement to an existing method
2. Return ONLY that complete rewritten method in a ```python block
3. After the closing ``` write:
   CHANGES: <one sentence>
   MODIFIED: <method_name>

Return only the single improved method:
"""

        self.log("[SELF] Sending signatures to AI for improvement...")
        result = self.ai.generate(prompt, use_planning=False)

        if "```python" not in result:
            self.log("[SELF] ❌ No code block")
            return False

        start = result.find("```python") + 9
        end = result.find("```", start)
        new_code = result[start:end].strip()
        self.log(f"[SELF] Code preview: {new_code[:200]}")
        if not new_code or not self.validate_code(new_code):
            return False

        post_code = result[end + 3:].strip()
        changes_match = re.search(r'CHANGES:\s*(.+)', post_code, re.IGNORECASE)
        changes_made = changes_match.group(1).strip() if changes_match else "Improvement applied"

        fn_blocks = self._split_into_functions(new_code)
        working_source = source

        for name, code in fn_blocks.items():
            lines = code.strip().split("\n")
            min_ind = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
            normalised = "\n".join(
                "    " + l[min_ind:] if l.strip() else ""
                for l in lines
            )
            if self._function_exists(working_source, name):
                pattern = rf"(    def {name}|def {name})\s*\("
                match = re.search(pattern, working_source)
                if match:
                    s = match.start()
                    indent = "    " if working_source[s] == " " else ""
                    next_d = re.search(rf"\n{indent}def |\n{indent}class ", working_source[match.end():])
                    e = match.end() + next_d.start() if next_d else len(working_source)
                    working_source = working_source[:s] + normalised + "\n\n" + working_source[e:]
                    self.log(f"[SELF] ✅ Patched: {name}")
            else:
                run_match = re.search(r"\n    def run\(", working_source)
                insert_pos = run_match.start() if run_match else len(working_source) - 1
                working_source = (
                    working_source[:insert_pos]
                    + "\n\n" + normalised
                    + working_source[insert_pos:]
                )
                self.log(f"[SELF] ✅ Inserted: {name}")

        success, ver = self._write_new_version("nova_assistant", working_source, changes_made)

        if success:
            self._log_entry("nova_assistant", ver, "auto-improvement", changes_made)
            self.log(f"[SELF] 🧬 Improvement applied → v{ver}")

        return success