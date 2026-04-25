# code_execution_loop.py - FIXED CACHE READING VERSION
import datetime
import re
import time
import threading
import os
import glob
from typing import Optional, Tuple, Dict, List, Any


class CodeExecutionLoop:
    def __init__(self, ai_model, sandbox, search_handler, stop_flag_getter=None, log_callback=None,
                 progress_callback=None, mistake_memory=None):
        self._error_disk_cache = None
        self.ai = ai_model
        self.sandbox = sandbox
        self.search_handler = search_handler
        self.stop_flag_getter = stop_flag_getter or (lambda: False)
        self.log = log_callback or print
        self.progress_callback = progress_callback

        self.mistake_memory = mistake_memory


        # Task tracking
        self.original_task = None
        self.task_requirements = []

        # Error tracking - ENHANCED
        self.error_history = []  # Track all errors
        self.error_counts = {}  # Count frequency of each error type
        self.repeated_errors = set()  # Track errors that keep repeating
        self.attempt_count = 0
        self.max_attempts = 15

        # Code tracking - ENHANCED
        self.previous_codes = []  # Store full codes
        self.previous_code_hashes = set()  # Quick lookup for duplicates
        self.previous_outputs = []
        self.last_error_type = None
        self.consecutive_same_error = 0

        # Solution quality tracking
        self.best_solution = None
        self.best_score = 0
        self.consecutive_no_improvement = 0

        self.halt_requested = False
        self.response_callback = None
        self.review_already_shown = False

        self.max_no_improvement = 3  # Reduced from 5 to catch loops sooner

    # ==========================================
    # KNOWN BEHAVIOUR NOTES
    # ==========================================
    # Known bug: The coder keeps going and doesn't always halt. It still gives code but can repeat.
    # This was more of a man in the loop strategy to stop it stopping prematurely.
    # The review popup (review_already_shown) prevents duplicate lesson popups.
    # Max attempts = 15, hard-stuck exit at consecutive_same_error >= 4 or repeated_errors >= 3.
    # ==========================================

    # ADD THIS NEW METHOD FOR DUPLICATE DETECTION
    def _is_duplicate_code(self, new_code: str) -> bool:
        """Check if code is duplicate of previous attempts"""
        if not new_code or len(new_code) < 50:
            return False

        # Create a simple hash (first 500 chars + last 500 chars)
        if len(new_code) > 1000:
            code_sample = new_code[:500] + new_code[-500:]
        else:
            code_sample = new_code

        code_hash = hash(code_sample)

        if code_hash in self.previous_code_hashes:
            self.log(f"[DUPLICATE] ❌ Same code generated again (hash: {code_hash})")
            return True

        self.previous_code_hashes.add(code_hash)
        return False

    # ADD THIS NEW METHOD FOR ERROR LOOP DETECTION
    def _detect_error_loop(self, error_type: str) -> bool:
        """Detect if we're stuck in an error loop"""
        if not error_type or error_type == "UnknownError":
            return False

        # Track consecutive same errors
        if error_type == self.last_error_type:
            self.consecutive_same_error += 1
        else:
            self.consecutive_same_error = 1
            self.last_error_type = error_type

        # Count error frequency
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        # Check if we're stuck
        if self.consecutive_same_error >= 3:
            self.log(f"[LOOP] 🔄 Stuck on same error '{error_type}' for {self.consecutive_same_error} attempts")
            self.repeated_errors.add(error_type)
            return True

        if self.error_counts.get(error_type, 0) >= 4:  # Same error 4+ times total
            self.log(f"[LOOP] 🔄 Error '{error_type}' appeared {self.error_counts[error_type]} times")
            self.repeated_errors.add(error_type)
            return True

        return False

    def extract_task_requirements(self, user_request: str) -> list:
        """Extract what the code needs to do"""
        requirement_prompt = f"""Analyze this coding request: "{user_request}"

List 3-5 specific requirements this code must fulfill.
Format as bullet points starting with -"""

        try:
            requirements = self.ai.generate(requirement_prompt)
            lines = [line.strip() for line in requirements.split('\n') if line.strip().startswith('-')]
            return [line[1:].strip() for line in lines][:5]
        except:
            return ["Complete the task", "No errors", "Clear output"]
    # ADD THIS NEW METHOD TO FORCE VARIATION
    def _force_variation(self, user_request: str, error_type: str = None) -> str:
        """Modify the prompt to force a different approach"""
        variation_hints = []

        if error_type and error_type in self.repeated_errors:
            # We're stuck on this error - try radical approach
            variation_hints.append(f"""
CRITICAL: We've tried fixing '{error_type}' multiple times and failed.
Try a COMPLETELY DIFFERENT APPROACH:
1. Use different libraries or methods
2. Simplify the problem
3. Break it into smaller steps
4. Avoid the pattern that caused the error
""")

        # Add context about previous failures
        if self.error_history:
            recent_errors = self.error_history[-3:]  # Last 3 errors
            variation_hints.append(f"""
PREVIOUS FAILURES (avoid these):
{chr(10).join([f"- {e[:100]}..." for e in recent_errors])}
""")

            # Force different libraries if stuck
            if self.consecutive_same_error >= 2:
                task_lower = user_request.lower()

                if 'plot' in task_lower or '3d' in task_lower or 'cube' in task_lower:
                    variation_hints.append("""
        LIBRARY SWITCH: Try a different visualization library:
        - Instead of matplotlib, try PyGame or Plotly
        - Instead of complex 3D, try 2D visualization first
        - Use simpler primitives
        """)
                elif any(phrase in task_lower for phrase in
                         ['control system', 'transfer function', 'bode plot', 'root locus']):
                    variation_hints.append("""
        SIMPLIFY: For control systems:
        - Use transfer functions instead of state space
        - Plot simpler responses first
        - Reduce system order
        """)


            # Combine hints
            if variation_hints:
                variation_text = "\n".join(variation_hints)
                return f"{variation_text}\n\n{user_request}"

        return user_request  # ← dedented one level - always reached

    # MODIFY THE MAIN LOOP TO USE THESE NEW METHODS
    def run_with_loop_detection(self, user_request: str) -> Tuple[bool, str, int, Dict[str, Any]]:
        """Main execution loop with ENHANCED loop prevention"""
        self.sandbox.execution_complete.clear()
        self.sandbox._last_output = ""
        self.sandbox._last_had_error = False

        self.log("### ENHANCED LOOP PREVENTION VERSION ###")

        # ===== INITIALIZATION =====
        self.log(f"\n🎯 CodeExecutionLoop.run_with_loop_detection CALLED!")
        self.original_task = user_request

        # Strip embedded code blocks so evaluation uses task description not code
        clean_task = re.sub(r'```[\s\S]*?```', '', user_request).strip()
        # Also strip lines that look like Python code
        clean_lines = [l for l in clean_task.split('\n')
                       if not l.strip().startswith('import ')
                       and not l.strip().startswith('def ')
                       and not l.strip().startswith('# Generated')]
        clean_task = '\n'.join(clean_lines).strip()
        if len(clean_task) > 10:
            self.original_task = clean_task

        self.task_requirements = self.extract_task_requirements(user_request)

        # Reset tracking variables
        self.attempt_count = 0
        self.error_history = []
        self.error_counts = {}
        self.repeated_errors = set()
        self.previous_codes = []
        self.previous_code_hashes = set()
        self.previous_outputs = []
        self.last_error_type = None
        self.consecutive_same_error = 0
        self.best_solution = None
        self.best_score = 0
        self.consecutive_no_improvement = 0
        self.review_already_shown = False

        metadata = {
            "attempts": [],
            "scores": [],
            "final_score": 0,
            "stopping_reason": "",
            "errors_seen": [],
            "duplicates_prevented": 0
        }

        # ===== MAIN EXECUTION LOOP =====
        while self.attempt_count < self.max_attempts:
            self.attempt_count += 1
            self.log(f"\n{'=' * 60}")
            self.log(f"[Attempt {self.attempt_count}/{self.max_attempts}]")
            self.log(f"{'=' * 60}")

            # STEP 0: Clear old plots
            self._clear_old_plots()

            # ===== HALT CHECK =====
            if getattr(self, 'halt_requested', False):
                self.log("🛑 Halted by user request")
                metadata["halted_by_user"] = True
                metadata["stopping_reason"] = "User pressed HALT"
                if self.best_solution:
                    return False, self.best_solution, self.attempt_count, metadata
                return False, "", self.attempt_count, metadata

            # ===== STOP CHECKS =====
            if self.stop_flag_getter():
                self.log(f"[HALT] 🛑 Stopped by main app stop flag")
                metadata["stopping_reason"] = "Stopped by user"
                return False, "Stopped by user", self.attempt_count, metadata

            if getattr(self.sandbox, 'halt_code_generation', False):
                self.log(f"[HALT] 🛑 Code generation halted by user")
                current_code = self.sandbox.code_text.get("1.0", "end").strip()
                metadata["stopping_reason"] = "User halted"
                return True, current_code, self.attempt_count, metadata

            # ===== STEP 1: Generate Code =====
            self.log(f"[STEP 1] Generating code...")

            # Apply variation if needed
            current_request = user_request
            if self.attempt_count > 1 and (self.consecutive_same_error >= 2 or len(self.repeated_errors) > 0):
                current_request = self._force_variation(user_request, self.last_error_type)
                self.log(f"[VARIATION] Forcing different approach due to repeated errors")

            code = self._extract_code_from_ai_response(current_request)

            # Check for duplicates BEFORE executing
            if not code:
                self.log("[ERROR] No code generated")
                continue

            if self._is_duplicate_code(code):
                metadata["duplicates_prevented"] += 1
                self.log("[DUPLICATE] ⚠️ Skipping duplicate code generation")
                # Reduce attempt count since this wasn't a real attempt
                self.attempt_count -= 1
                # Force more variation
                user_request = self._force_variation(user_request, self.last_error_type)
                continue

            self.previous_codes.append(code)
            self.log(f"[STEP 1] ✓ Generated {len(code)} chars")

            # ===== STEP 2: Execute Code =====
            self.log(f"[STEP 2] Executing in sandbox...")
            self.sandbox.execution_complete.clear()
            self.sandbox.set_code(code, auto_run=True, from_smart_loop=True)

            execution_timeout = 600
            if not self.sandbox.execution_complete.wait(timeout=execution_timeout):
                self.log(f"[STEP 2] ⚠️ TIMEOUT after {execution_timeout}s")
                output = f"[TIMEOUT] Execution exceeded {execution_timeout}s"
                error = True
                error_type = "TimeoutError"
            else:
                output = getattr(self.sandbox, '_last_output', '')
                error = getattr(self.sandbox, '_last_had_error', False)
                error_type = self._extract_error_type(output) if error else None

            self.previous_outputs.append(output)
            self.log(f"[STEP 2] ✓ Completed - {len(output)} chars output")

            # After execution - report to UI
            if hasattr(self, 'response_callback') and self.response_callback:
                if error:
                    self.response_callback(
                        f"Attempt {self.attempt_count}: hit a {error_type or 'unknown'} error. "
                        f"Looking up the fix and trying again..."
                    )
                else:
                    self.response_callback(
                        f"Attempt {self.attempt_count}: code ran without errors. Checking the result..."
                    )

            # ===== STEP 3: Track Errors for Loop Detection =====
            if error:
                self.error_history.append(output[:500])  # Store error snippet
                metadata["errors_seen"].append(error_type or "UnknownError")

                # Check for error loops
                if error_type and self._detect_error_loop(error_type):
                    self.log(f"[LOOP DETECTED] Stuck on '{error_type}', will force variation")
                    # Don't break yet - let variation forcing handle it
                    # Save this mistake to memory
                    if hasattr(self, 'review_callback') and self.review_callback and not self.review_already_shown:
                        self.review_already_shown = True
                        self.review_callback(self.original_task, error_type, code, output)


            # ===== STEP 4: Evaluate Solution =====
            self.log(f"[STEP 3] Evaluating solution...")
            is_good_enough, score, reason = self._solution_is_good_enough(output, self.original_task)
            self._report_progress(score)

            metadata["attempts"].append({
                "attempt": self.attempt_count,
                "error": error,
                "error_type": error_type,
                "score": score,
                "good_enough": is_good_enough,
                "code_length": len(code)
            })
            metadata["scores"].append(score)

            if score > self.best_score:
                self.best_score = score
                self.best_solution = output
                self.consecutive_no_improvement = 0
                self.log(f"[STEP 3] 🏆 New best: {score}")
            else:
                self.consecutive_no_improvement += 1

            # ===== STEP 5: Check Stop Conditions =====
            if is_good_enough:
                self.log(f"[STEP 4] ✅ Solution looks good!")
                metadata["final_score"] = score
                metadata["stopping_reason"] = reason
                return True, self.best_solution or output, self.attempt_count, metadata

            if self.attempt_count >= self.max_attempts:
                self.log(f"[STOP] ⏰ Max attempts")
                metadata["final_score"] = self.best_score
                metadata["stopping_reason"] = "Max attempts"
                if self.best_solution:
                    return True, self.best_solution, self.attempt_count, metadata
                else:
                    return False, output, self.attempt_count, metadata

            # Check for hard stuck condition
            if (self.consecutive_same_error >= 4 or
                    len(self.repeated_errors) >= 3 or
                    self.consecutive_no_improvement >= self.max_no_improvement * 2):
                ################
                self.log(f"[STOP] 🌀 Stuck in loop - giving up")
                if hasattr(self, 'review_callback') and self.review_callback and not self.review_already_shown:
                    self.review_already_shown = True
                    self.review_callback(self.original_task, self.last_error_type or "unknown",
                                         code, output)

                metadata["final_score"] = self.best_score
                metadata["stopping_reason"] = f"Stuck in loop (errors: {list(self.repeated_errors)})"
                if self.best_solution:
                    return True, self.best_solution, self.attempt_count, metadata
                else:
                    return False, output, self.attempt_count, metadata

            # ===== STEP 6: Prepare Next Attempt =====
            self.log(f"[STEP 5] Preparing next attempt...")

            if error:
                # Enhanced error handling with cache
                search_results = ""
                error_type = self._extract_error_type(output)
                normalized_error = self._normalize_error_type(error_type)

                # Try to get cached solution
                cache_query = f"Fix {error_type}: {output[:300]}"
                cached_result = self.get_smart_cached_solution(error_type, cache_query, self.original_task)

                if cached_result:
                    self.log(f"[CACHE] ✅ Found cached solution for {error_type}")
                    # Use cached solution as context for next attempt
                    user_request = f"""
PREVIOUS ERROR: {error_type}
CACHED SOLUTION: {cached_result[:500]}...

TASK: {self.original_task}

Generate NEW code that avoids the previous error:
"""
            else:
                    self.log(f"[CACHE] ❌ No cached solution for {error_type}")
                    # Update request with error context for next attempt
                    user_request = f"""
            PREVIOUS ERROR: {error_type}
            ERROR OUTPUT: {output[:400]}
            
            TASK: {self.original_task}
            
            The previous attempt failed with the above error.
            Generate NEW code that specifically avoids this error.
            Try a different approach if needed.
            """
        # ===== MAX ATTEMPTS EXHAUSTED =====
        self.log(f"\n[FAILED] Max attempts exhausted")
        metadata["final_score"] = self.best_score
        metadata["stopping_reason"] = "Max attempts exceeded"

        if self.best_solution:
            return True, self.best_solution, self.attempt_count, metadata
        else:
            return False, output if 'output' in locals() else "No solution", self.attempt_count, metadata

    def _report_progress(self, score: float):
        """Send progress updates to UI or console"""
        progress = self.attempt_count / self.max_attempts
        percent = int(progress * 100)

        bar_len = 10
        filled = int(progress * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)

        message = (
            f"[SMART LOOP] Attempt {self.attempt_count}/{self.max_attempts} | "
            f"Score: {int(score)} | "
            f"Best: {int(self.best_score)} | "
            f"{bar} {percent}%"
        )

        self.log(message)

        if self.progress_callback:
            try:
                self.progress_callback(message, percent)
            except Exception:
                pass

    def _clear_old_plots(self):
        """Delete old plot files before running new code"""
        plot_patterns = ["plot.png", "*.png", "figure*.png", "*.jpg"]

        for pattern in plot_patterns:
            for old_file in glob.glob(pattern):
                try:
                    os.remove(old_file)
                    self.log(f"[SANDBOX] 🗑️ Cleared old plot: {old_file}")
                except Exception as e:
                    self.log(f"[SANDBOX] ⚠️ Could not delete {old_file}: {e}")

    def _solution_is_good_enough(self, output: str, task: str) -> Tuple[bool, float, str]:
        """Smart solution checking with scoring"""
        score = 0.0
        task_lower = task.lower()
        output_lower = output.lower()

        self.log(f"\n[GOOD_ENOUGH] ===== Checking attempt {self.attempt_count} =====")

        # CRITICAL: Check if there are ANY errors first
        if getattr(self.sandbox, '_last_had_error', False):
            self.log(f"[GOOD_ENOUGH] ❌ Has errors - immediately not good enough")
            return False, 0, "Has errors"

        # ===== NEW: CHECK FOR RUNTIME ERRORS IN OUTPUT =====
        runtime_error_patterns = [
            'error:',
            'exception:',
            'failed',
            'failure',
            'traceback',
            'attributeerror',
            'typeerror',
            'valueerror',
            'importerror',
            'modulenotfounderror',
            'nameerror',
            'keyerror',
            'indexerror',
            'runtimeerror',
            'could not',
            'unable to',
            'not found',
            'does not exist',
            'no attribute',
            'playback error',
            'audio error',
            'connection error'
        ]

        for pattern in runtime_error_patterns:
            if pattern in output_lower:
                self.log(f"[GOOD_ENOUGH] ❌ Runtime error detected: '{pattern}'")
                return False, 0, f"Runtime error: {pattern}"
        # ===== END NEW CODE =====

        # CHECK FOR TIMEOUT (treated as error for our purposes)
        if "[TIMEOUT]" in output or "timeout" in output_lower:
            self.log(f"[GOOD_ENOUGH] ⏱️ TIMEOUT - not good enough")
            return False, 0, "Timeout"

        self.log(f"[GOOD_ENOUGH] Task: {task[:50]}...")

        # end runtime errors detect


        # CHECK FOR TIMEOUT (treated as error for our purposes)
        if "[TIMEOUT]" in output or "timeout" in output_lower:
            self.log(f"[GOOD_ENOUGH] ⏱️ TIMEOUT - not good enough")
            return False, 0, "Timeout"

        self.log(f"[GOOD_ENOUGH] Task: {task[:50]}...")

        # 1. NO ERRORS - ESSENTIAL (40 points)
        score += 40
        self.log(f"[GOOD_ENOUGH] ✅ +40 points: No errors")

        # 2. PLOTTING TASKS - SPECIAL HANDLING (STRICTER!)
        plot_keywords = ['plot', 'graph', 'chart', 'figure', 'visualize', 'matplotlib', 'fourier', 'series']
        is_plotting_task = any(keyword in task_lower for keyword in plot_keywords)

        if is_plotting_task:
            self.log(f"[GOOD_ENOUGH] 📊 This is a PLOTTING task (stricter requirements!)")

            # ===== NEW: FILE-BASED PLOT DETECTION =====
            plot_file = "plot.png"

            # Check if plot file exists
            if os.path.exists(plot_file):
                # Verify plot is FRESH (created in last 10 seconds)
                file_mod_time = os.path.getmtime(plot_file)
                current_time = time.time()
                is_fresh = (current_time - file_mod_time) < 10

                if is_fresh:
                    score += 50  # MAJOR points for actual plot
                    self.log("[GOOD_ENOUGH] 📈 Plot detected")

                else:
                    file_age = current_time - file_mod_time
                    self.log(f"[GOOD_ENOUGH] ❌ Plot file exists but is STALE (age: {file_age:.1f}s)")
                    return False, 0, "Plot file is old - code failed"
                # ── NEW: sandbox saves to a temp path, detect that too ──────────
            elif "Plot auto-saved to:" in output or "sandbox_plot_" in output:
                score += 50
                self.log("[GOOD_ENOUGH] 📈 Plot detected (sandbox temp path)")
            # ────────────────────────────────────────────────────────────────

            else:
                self.log(f"[GOOD_ENOUGH] ❌ PLOTTING TASK but no plot.png file found!")
                self.log(f"[GOOD_ENOUGH] Output preview: {output[:100]}")
                return False, 0, "Missing plot file"
            # ===== END NEW CODE =====


        # 3. CODE COMPLETENESS CHECK (non-plotting)
        lines = [l.strip() for l in output.split('\n') if l.strip()]
        code_indicators = ['import ', 'def ', 'result', 'output']
        code_lines = [l for l in lines if any(indicator in l for indicator in code_indicators)]

        if len(code_lines) >= 2:
            score += 20
            self.log(f"[GOOD_ENOUGH] 📝 +20 points: Code structure found")

        # 4. OUTPUT SUBSTANTIALITY
        if len(output) > 50 or "plot" in output_lower or "figure" in output_lower:
            score += 20
            self.log(f"[GOOD_ENOUGH] 📄 +20 points: Substantial output ({len(output)} chars)")

        # 5. SIMPLE TASK BONUS - short output is fine for simple tasks
        elif len(output.strip()) > 0 and not is_plotting_task:
            score += 20
            self.log(f"[GOOD_ENOUGH] 📄 +20 points: Output produced for simple task")

        # 6. SIMPLE TASK - if no plotting required and no errors, good enough at 60+
        if not is_plotting_task and score >= 60:
            self.log(f"[GOOD_ENOUGH] ✅ Non-plotting task with output - accepting at {score}")
            return True, score, "Simple task completed"


        # DECISION LOGIC
        if score >= 70:
            self.log(f"[GOOD_ENOUGH] ✅ EXCELLENT!")
            return True, score, "Excellent solution"
        elif score >= 50:
            self.log(f"[GOOD_ENOUGH] ✅ GOOD!")
            return True, score, "Good solution"
        else:
            self.log(f"[GOOD_ENOUGH] 🔄 Needs improvement")
            return False, score, "Needs improvement"

    def detect_loop(self) -> bool:
        """Check if we're in an error loop"""
        if len(self.error_history) < 2:
            return False

        recent_errors = self.error_history[-2:]

        for i in range(len(recent_errors) - 1):
            err1 = recent_errors[i].lower()
            err2 = recent_errors[i + 1].lower()

            if ("error" in err1 and "error" in err2):
                return True

        return False

    def _extract_error_type(self, error_text: str) -> str:
        """Extract the actual Python error type from traceback"""
        if not error_text:
            return "NoError"

        self.log(f"[ERROR_EXTRACT] Input text (first 200 chars): {error_text[:200]}")

        # Check for timeout
        if '[TIMEOUT]' in error_text or 'Execution exceeded' in error_text:
            return "TimeoutError"

        # ── ADD THIS GUARD ──────────────────────────────────────────
        # Only look for errors if there's an actual Python traceback or error line.
        # Without this, pygame's startup banner gets false-matched.
        has_traceback = 'Traceback (most recent call last)' in error_text
        has_error_line = re.search(r'^\w+Error:', error_text, re.MULTILINE)
        has_exception = re.search(r'^\w+Exception:', error_text, re.MULTILINE)

        if not has_traceback and not has_error_line and not has_exception:
            self.log(f"[ERROR_EXTRACT] ✅ No traceback found - treating as clean output")
            return "NoError"
        # ────────────────────────────────────
        # Try to find Python exception names with MORE patterns
        patterns = [
            r'(\w+Error):',  # AttributeError:
            r'(\w+Exception):',  # ValueError Exception:
            r'File ".*", line \d+, in .*?\n(\w+Error):',  # Multi-line
            r'pygame\.error:\s*(.*)',  # pygame.error: message
            r'(\w+):\s*(?:invalid|wrong|bad|missing)',  # Generic error messages
            r'raise\s+(\w+Error)',  # raise statements
            r'(\w+):\s*[\w\s]+(?:argument|parameter)',  # Argument errors
        ]

        for pattern in patterns:
            match = re.search(pattern, error_text, re.IGNORECASE | re.DOTALL)
            if match:
                error_type = match.group(1).lower()
                self.log(f"[ERROR_EXTRACT] ✅ MATCHED: {error_type}")

                # Special handling for pygame errors
                if 'pygame' in error_text.lower():
                    if 'argument' in error_text.lower():
                        return 'argumenterror'
                    if 'display' in error_text.lower():
                        return 'displayerror'

                return self._normalize_error_type(error_type)

        # LAST RESORT: Look for any word ending in "error" or "exception"
        fallback = re.search(r'\b(\w*(?:error|exception))\b', error_text, re.IGNORECASE)
        if fallback:
            error_type = fallback.group(1).lower()
            self.log(f"[ERROR_EXTRACT] ⚠️ FALLBACK MATCH: {error_type}")
            return self._normalize_error_type(error_type)

        self.log(f"[ERROR_EXTRACT] ❌ NO MATCH - returning UnknownError")
        return self._normalize_error_type("UnknownError")


    def _build_cache_key(self, error_type: str, query: str) -> str:
        """Build a cache key matching the seed format: error_type::library"""

        # Clean error type (same as seeding script)
        error_type_clean = self._normalize_error_type(error_type)

        # Extract library name from query
        # Use the same libraries list as seeding script
        libraries = [
            'control', 'matplotlib', 'numpy', 'scipy', 'pandas', 'sympy',
            'tensorflow', 'torch', 'sklearn', 'keras', 'transformers', 'opencv-python',
            'flask', 'django', 'fastapi', 'requests', 'beautifulsoup4', 'selenium',
            'polars', 'dask', 'seaborn', 'plotly', 'statsmodels',
            'slycot', 'scipy.signal',
            'tkinter', 'pygame', 'pyqt5', 'kivy', 'pyside6',
            'cv2', 'pillow', 'scikit-image', 'albumentations',
            'pydub', 'librosa', 'soundfile', 'pyaudio', 'wave',
            'pyopengl', 'moderngl', 'vispy', 'pyvista', 'trimesh'
        ]

        # Try to find library in query
        query_lower = query.lower()
        found_library = None

        for lib in libraries:
            if lib in query_lower:
                found_library = lib
                break

        # If no library found, try to extract from ImportError message
        if not found_library:
            # Pattern: "cannot import name 'xxx' from 'library_name'"
            import_pattern = r"from ['\"]([a-zA-Z0-9_-]+)['\"]"
            matches = re.findall(import_pattern, query_lower)
            if matches:
                found_library = matches[-1]  # Take the last one (usually the library)

        # Fallback to first word after "import" or "ModuleNotFoundError"
        if not found_library:
            words = query_lower.split()
            for i, word in enumerate(words):
                if word in ['import', 'module', 'package', 'library'] and i + 1 < len(words):
                    candidate = words[i + 1]
                    if len(candidate) > 2:  # Avoid very short words
                        found_library = candidate
                        break

        # Final fallback
        if not found_library:
            found_library = "unknown"

        # Build key EXACTLY like seeding script
        cache_key = f"{error_type_clean}::{found_library}"

        self.log(f"[CACHE KEY] Built: '{cache_key}' (format matches seeding script)")
        return cache_key

    def _normalize_error_type(self, error_type: str) -> str:
        """Return canonical error type for cache keys"""
        if not error_type:
            return "unknownerror"

        error_type = error_type.lower().strip()

        # Remove punctuation or trailing colon
        error_type = error_type.replace(":", "")

        # Ensure it ends with 'error' when appropriate
        if not error_type.endswith("error") and not error_type.endswith("exception"):
            error_type += "error"

        return error_type

    def _build_search_query(self, task: str, error: str = None) -> str:
        """Build a specific, effective search query for fixing code errors"""
        if error:
            self.log(f"[BUILD_QUERY] Error text received (first 300 chars): {error[:300]}")
            error_type = self._extract_error_type(error)
            self.log(f"[BUILD_QUERY] Extracted error type: {error_type}")

            if error_type == "UnknownError":
                return None
            # Handle TimeoutError specially
            if error_type.lower() == "timeouterror":
                task_lower = task.lower()
                if 'tkinter' in task_lower or 'mainloop' in task_lower or 'tk.' in task_lower:
                    query = "Python Tkinter non-blocking execution without mainloop sandbox"
                elif 'matplotlib' in task_lower or 'plot' in task_lower:
                    query = "Python matplotlib animation without blocking event loop"
                else:
                    query = "Python code timeout infinite loop fix optimization non-blocking"
                self.log(f"[SEARCH_QUERY] Built timeout query: '{query}'")
                return query

            # Extract library/module names from the error
            libraries = []
            lib_patterns = [
                r'import (\w+)',  # import statements
                r'from (\w+)',  # from imports
                r'(\w+)\.(\w+)\(',  # module.function() calls
                r'(\w+)\.(\w+)\.(\w+)',  # module.submodule.function
            ]

            for pattern in lib_patterns:
                matches = re.findall(pattern, error)
                for match in matches:
                    if isinstance(match, tuple):
                        libraries.extend(
                            [m for m in match if m and m not in ['C', 'Users', 'AppData', 'Local', 'Temp']])
                    else:
                        if match not in ['C', 'Users', 'AppData', 'Local', 'Temp']:
                            libraries.append(match)

            # Get unique libraries
            libraries = list(set(libraries))[:2]  # Take top 2

            # Build specific query
            if libraries:
                lib_str = ' '.join(libraries)
                query = f"{lib_str} {error_type} fix python example"
            else:
                # Extract key words from task
                task_words = re.findall(r'\b\w{4,}\b', task)[:3]
                task_str = ' '.join(task_words) if task_words else task[:30]
                query = f"Python {error_type} {task_str} fix example"

            self.log(f"[SEARCH_QUERY] Built query: '{query}'")
            return query

        # No error - general task query
        words = re.findall(r'\b\w{4,}\b', task)
        task_words = ' '.join(words[:3]) if words else task[:30]
        query = f"Python {task_words} example code"
        self.log(f"[SEARCH_QUERY] Built query: '{query}'")
        return query

    def _get_documentation_context(self, task: str) -> Optional[str]:
        """
        Get documentation context BEFORE code generation.

        TWO MODES:
        1. PROACTIVE (Attempt 1): Predict libraries from task keywords
        2. REACTIVE (Attempt 2+): Identify libraries from error traceback

        Both use the same seeded cache of 369 solutions + documentation.
        """
        if not self.ai:
            return None

        if not hasattr(self.ai, "_get_cached_error_search"):
            return None

        # Strip INTERNET DATA block - take only text before it
        if "INTERNET DATA" in task:
            task_clean = task.split("=" * 20)[0]  # Everything before first ===
        else:
            task_clean = task
        task_lower = task_clean.lower()

        libraries_to_try = []

        # ================================================================
        # MODE 1: PROACTIVE (Attempt 1) - Predict from task keywords
        # ================================================================
        if self.attempt_count == 1 or not self.last_error_type:
            self.log("[DOC CACHE] 📋 PROACTIVE mode - predicting libraries from task")


            # ===== PRIORITY 1: Check for EXPLICIT library mentions first =====
            if 'pygame' in task_lower:
                libraries_to_try = ['pygame', 'numpy']
                self.log("[DOC CACHE] 🎮 Task explicitly mentions pygame")

            elif 'matplotlib' in task_lower:
                libraries_to_try = ['matplotlib', 'numpy']
                self.log("[DOC CACHE] 📊 Task explicitly mentions matplotlib")

            elif any(kw in task_lower for kw in
                     ['speaker', 'audio', 'hear', 'frequency hz', 'tone',
                      'sounddevice', 'pyaudio', 'waveform', 'oscillator']):
                libraries_to_try = ['sounddevice', 'pygame', 'numpy']
                self.log("[DOC CACHE] 🔊 Task suggests audio generation")

            # ===== ADD HERE =====
            elif any(kw in task_lower for kw in
                     ['picture', 'photo', 'image', 'gallery', 'slideshow', 'portrait', 'photograph']):
                libraries_to_try = ['matplotlib', 'pillow']
                self.log("[DOC CACHE] 🖼 Task suggests image display")
            # ===== END ADD =====

            elif 'pandas' in task_lower:
                libraries_to_try = ['pandas', 'numpy']
                self.log("[DOC CACHE] 📊 Task explicitly mentions pandas")

            elif 'control' in task_lower and 'library' in task_lower:
                libraries_to_try = ['control', 'scipy', 'numpy']
                self.log("[DOC CACHE] 🎛️ Task explicitly mentions control library")


            # ===== PRIORITY 2: Check for specific 3D/animation keywords =====
            elif any(kw in task_lower for kw in
                     ['cube', '3d', 'tumble', 'tumbling', 'rotate', 'rotating', 'animation', 'animate']):
                libraries_to_try = ['pygame', 'matplotlib']
                self.log("[DOC CACHE] 🎮 Task suggests 3D graphics (pygame)")

            # ===== PRIORITY 3: Check for plotting keywords =====
            elif any(kw in task_lower for kw in ['plot', 'chart', 'graph', 'sin', 'cos', 'visualiz',
                                                 'aesthetic', 'beautiful', 'infographic',
                                                 'map', 'heatmap', 'dashboard']):
                libraries_to_try = ['matplotlib', 'numpy']
                self.log("[DOC CACHE] 📊 Task suggests plotting (matplotlib)")

            # ===== PRIORITY 4: Check for control systems =====
            elif any(kw in task_lower for kw in ['system', 'transfer', 'locus', 'bode', 'rlocus', 'nyquist']):
                libraries_to_try = ['control', 'scipy', 'numpy']
                self.log("[DOC CACHE] 🎛️ Task suggests control systems")

            # ===== PRIORITY 5: Check for data science =====
            elif any(kw in task_lower for kw in ['data', 'dataframe', 'csv', 'analysis', 'excel']):
                libraries_to_try = ['pandas', 'numpy', 'matplotlib']
                self.log("[DOC CACHE] 📊 Task suggests data science (pandas)")

            # ===== PRIORITY 6: Check for web/API =====
            elif any(kw in task_lower for kw in ['web', 'api', 'http', 'request', 'scrape', 'download']):
                libraries_to_try = ['requests', 'beautifulsoup4']
                self.log("[DOC CACHE] 🌐 Task suggests web libraries")


            # ===== DEFAULT: no confident match - skip injection =====
            else:
                self.log("[DOC CACHE] ❌ No confident library match - skipping injection")
                return None

        # ================================================================
        # MODE 2: REACTIVE (Attempt 2+) - Identify from error traceback
        # ================================================================
        else:
            self.log("[DOC CACHE] 🔧 REACTIVE mode - identifying from error traceback")
            error_output = getattr(self, '_last_output', '') if hasattr(self, '_last_output') else ''

            # Check what library is mentioned in the error traceback
            if 'matplotlib' in error_output or 'pyplot' in error_output:
                libraries_to_try = ['matplotlib', 'numpy']
                self.log("[DOC CACHE] 📊 Error involves matplotlib")

            elif 'pygame' in error_output:
                libraries_to_try = ['pygame', 'numpy']
                self.log("[DOC CACHE] 🎮 Error involves pygame")

            elif 'control' in error_output or 'scipy.signal' in error_output:
                libraries_to_try = ['control', 'scipy', 'numpy']
                self.log("[DOC CACHE] 🎛️ Error involves control systems")

            elif 'pandas' in error_output:
                libraries_to_try = ['pandas', 'numpy']
                self.log("[DOC CACHE] 📊 Error involves pandas")

            elif 'numpy' in error_output:
                libraries_to_try = ['numpy', 'matplotlib']
                self.log("[DOC CACHE] 🔢 Error involves numpy")
            ##################
            elif 'requests' in error_output or 'urllib' in error_output:
                libraries_to_try = ['requests']
                self.log("[DOC CACHE] 🌐 Error involves web requests")

            elif 'tclerror' in error_output.lower() or 'tkinter' in error_output or 'tk.' in error_output:
                libraries_to_try = ['tkinter']
                self.log("[DOC CACHE] 🖼 Error involves tkinter/TclError")
                ####
            else:
                # No library detected in error - don't guess, return nothing
                self.log("[DOC CACHE] ❌ No library detected in error traceback - skipping injection")
                return None

        # ================================================================
        # RETRIEVE DOCUMENTATION from seeded cache
        # ================================================================
        if not libraries_to_try:
            self.log(f"[DOC CACHE] ❌ No libraries identified")
            return None

        # Try to get documentation for each relevant library
        for library in libraries_to_try[:3]:  # Limit to top 3
            query_for_docs = f"{library} python library API reference"

            # Try common error types that might have documentation cached
            for error_type in ["modulenotfounderror", "attributeerror", "documentation"]:
                try:
                    cached = self.ai._get_cached_error_search(error_type, query_for_docs)
                    if cached:
                        self.log(f"[DOC CACHE] ✅ Found {library} documentation ({len(cached)} chars)")
                        # Add context about what this library is for
                        library_context = self._get_library_context(library)
                        return f"{library_context}\n\nDOCUMENTATION:\n{cached[:2500]}"
                except:
                    continue

        self.log(f"[DOC CACHE] ❌ No documentation found in cache")
        return None


    def _get_library_context(self, library: str) -> str:
        """Provide context about what a library is used for"""
        contexts = {
            'control': """
    CONTROL LIBRARY - USE FOR:
    • Control systems analysis
    • Transfer functions
    • Root locus plots
    • Bode/Nyquist plots
    • System simulations
    • PID controllers

    DO NOT USE for: 3D graphics, animations, games
    """,
            'pygame': """
    PYGAME - USE FOR:
    • 2D/3D game development
    • Real-time animations
    • Interactive graphics
    • Physics simulations
    • Visual demonstrations

    PERFECT FOR: Tumbling cubes, animations, visual effects
    """,
            'matplotlib': """
    MATPLOTLIB - USE FOR:
    • 2D/3D plotting and charts
    • Data visualization
    • Static or animated plots
    • Scientific visualizations
    • 3D surfaces and objects

    GOOD FOR: 3D cube visualizations with Axes3D
    """,
            'numpy': """
    NUMPY - USE FOR:
    • Numerical computations
    • Array mathematics
    • Linear algebra
    • Mathematical operations
    • Coordinate calculations

    ALMOST ALWAYS NEEDED: For any numerical Python code
    """,
            'opengl': """
    OPENGL - USE FOR:
    • Advanced 3D graphics
    • High-performance rendering
    • Complex 3D visualizations
    • Professional graphics applications

    ADVANCED: For complex 3D graphics needs
    """,
            'vpython': """
    VPYTHON - USE FOR:
    • Simple 3D visualizations
    • Educational demonstrations
    • Physics simulations
    • Interactive 3D objects

    EASY OPTION: For quick 3D visualizations
    """
        }
        return contexts.get(library, f"{library.upper()} LIBRARY: General purpose library.")

    def _extract_code_from_ai_response(self, prompt: str) -> Optional[str]:
        """Extract Python code from AI response with SMART context"""
        try:
            # Get contextual documentation
            doc_context = self._get_documentation_context(prompt)
            # Get mistake warnings
            mistake_warnings = ""
            if self.mistake_memory:
                mistake_warnings = self.mistake_memory.get_relevant_warnings(prompt)
                if mistake_warnings:
                    self.log(
                        f"[MISTAKES] Found {mistake_warnings.count('⚠️') + mistake_warnings.count('🔴')} relevant warnings")
                    self.log(f"[MISTAKES DEBUG] First 1500 chars:\n{mistake_warnings[:1500]}")

            # Inject goof web search context if available
            extra = getattr(self, 'extra_context', None)
            if extra:
                mistake_warnings += f"\n\nWEB SEARCH RESULTS FOR FIX:\n{extra}\n"
                self.extra_context = None
                self.log("[GOOF] ✅ Web fix context included in prompt")

            if doc_context or mistake_warnings:
                self.log(f"[CONTEXT] ✅ Injected context into prompt")

                enhanced_prompt = f"""
                                        {mistake_warnings}

                            TASK CONTEXT ANALYSIS:
                            First, read the task and the library documentation below.
                            Determine what type of code is actually needed.

                            LIBRARY CONTEXT:
                            {doc_context}

                            ORIGINAL TASK:
                            {prompt}

                    THINKING PROCESS REQUIRED:
                    1. Based on the task, what is the user REALLY asking for?
                    2. What is the appropriate library for this task type?
                    3. How should the code be structured?

                    GENERATION REQUIREMENTS:
                    1. Return ONLY Python code in ```python ... ``` block
                    2. Code must be COMPLETE and RUNNABLE
                    3. Include ALL necessary imports
                    4. Add print statements to verify execution
                    5. Use the library shown in LIBRARY CONTEXT above
                    6. For audio generation: use sounddevice or pygame for continuous playback
                    7. For 3D graphics: use pygame, matplotlib 3D, or OpenGL

                    Generate the COMPLETE, APPROPRIATE code:
                    """
            else:
                enhanced_prompt = f"""
    TASK: {prompt}

    GENERATION REQUIREMENTS:
    1. Return ONLY Python code in ```python ... ``` block
    2. Code must be COMPLETE and RUNNABLE
    3. Include ALL necessary imports
    4. Add print statements to verify execution
    5. Think about what type of code is actually needed

    Generate the COMPLETE Python code:
    """

            response = self.ai.generate_code(enhanced_prompt)

            # =====================================================
            # Extract python code block
            # =====================================================
            pattern = r'```python\s*(.*?)\s*```'
            matches = re.findall(pattern, response, re.DOTALL)

            if matches:
                code = matches[0].strip()

                # ========== ADD HEADER COMMENT WITH DATE AND MODEL ==========
                import datetime
                current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                model_name = self.ai.model if hasattr(self.ai, 'model') else "Unknown Model"

                source = "Cloud" if hasattr(self.ai, '_is_cloud_model') and self.ai._is_cloud_model(
                    model_name) else "Ollama"

                header_lines = [
                    f"# Generated by: {model_name} ({source})",
                    f"# Date: {current_date}",
                    "# AutoCoder System - Automated Code Generation",
                    ""  # Blank line separator
                ]

                code = code.strip()
                code = "\n".join(header_lines) + "\n" + code

                self.log(f"[HEADER] Added generation info: {model_name} at {current_date}")

                # =============================================================

                # =============================================
                # HELPER: Insert imports after header comments
                # =============================================
                def _insert_after_header(code: str, new_imports: str) -> str:
                    lines = code.split('\n')
                    insert_at = 0
                    for i, line in enumerate(lines):
                        if line.startswith('#') or line.strip() == '':
                            insert_at = i + 1
                        else:
                            break
                    lines.insert(insert_at, new_imports)
                    return '\n'.join(lines)

                # =============================================
                # SMARTER IMPORT CHECKING
                # =============================================
                lines = code.split('\n')

                task_lower = prompt.lower()
                is_github_task = "INSTRUCTION: Do NOT rewrite" in prompt

                is_3d_graphics = any(keyword in task_lower for keyword in [
                    'cube', '3d', 'animation', 'rotate', 'tumble', 'visualize',
                    'pygame', 'opengl', 'vpython'
                ])

                control_indicators = [
                    'transfer function', 'bode plot', 'root locus', 'nyquist',
                    'state space', 'pid controller', 'control system', 'feedback',
                    'step response', 'impulse response', 'pole', 'zero'
                ]
                control_count = sum(1 for indicator in control_indicators if indicator in task_lower)
                has_isolated_control = re.search(r'\bcontrol\s+(system|theory|design|analysis)\b', task_lower)
                is_control_systems = (control_count >= 2 or has_isolated_control)

                if is_3d_graphics and not is_github_task:
                    has_pygame = any('import pygame' in line or 'import pg' in line for line in lines)
                    has_matplotlib = any('import matplotlib' in line for line in lines)

                    if not has_pygame and 'cube' in task_lower:
                        self.log("[IMPORT] Adding PyGame for 3D cube animation")
                        code = _insert_after_header(code, "import pygame\nimport numpy as np")
                    elif not has_matplotlib and ('plot' in task_lower or '3d' in task_lower):
                        self.log("[IMPORT] Adding matplotlib for 3D plotting")
                        code = _insert_after_header(code,
                                                    "import matplotlib.pyplot as plt\nfrom mpl_toolkits.mplot3d import Axes3D")

                elif is_control_systems and not is_github_task:
                    has_control = any('import control' in line for line in lines)
                    has_numpy = any('import numpy' in line for line in lines)

                    if not has_control:
                        self.log("[IMPORT] Adding control library for control systems task")
                        code = _insert_after_header(code, "import control as ctrl")
                    if not has_numpy:
                        self.log("[IMPORT] Adding numpy for numerical operations")
                        code = _insert_after_header(code, "import numpy as np")

                elif not is_github_task:
                    has_any_import = any(line.startswith('import ') or line.startswith('from ') for line in lines)
                    if not has_any_import:
                        self.log("[IMPORT] Adding basic Python imports")
                        code = _insert_after_header(code, "import numpy as np\nimport matplotlib.pyplot as plt")

                # ====== COMPLETENESS CHECKS ======
                lines = code.split('\n')

                # 1. Check for unmatched brackets
                bracket_stack = []
                for line in lines:
                    for char in line:
                        if char == '[':
                            bracket_stack.append('[')
                        elif char == ']':
                            if bracket_stack:
                                bracket_stack.pop()

                if bracket_stack:
                    self.log(f"[ERROR] Unmatched brackets - code is incomplete")
                    return None

                # 2. Check for truncated imports
                if 'from ' in code and 'import ' not in code:
                    self.log(f"[ERROR] Incomplete import statement")
                    return None


                # 3. Minimum length check - relax for simple tasks
                min_length = 50 if len(self.original_task.split()) < 6 else 200
                if len(code) < min_length:
                    self.log(f"[ERROR] Code too short ({len(code)} chars) - likely incomplete")
                    return None

                # 4. Check for incomplete ending
                last_line = lines[-1].strip()
                if last_line.endswith(',') or last_line.endswith('[') or last_line.endswith('('):
                    self.log(f"[ERROR] Code ends with incomplete line")
                    return None

                return code

            self.log(f"[WARN] No ```python code block found in response")
            return None

        except Exception as e:
            self.log(f"[AI Error] {e}")
            return None


    def _create_improvement_prompt(self, current_output: str, score: float, reason: str) -> str:
        """Create improvement prompt"""
        return f"""ORIGINAL TASK: {self.original_task}

Current solution: Score {score:.1f}/100 - {reason}

CRITICAL REQUIREMENTS:
1. Generate COMPLETE, STANDALONE Python code
2. Code must be wrapped in ```python ... ``` code block
3. Include ALL imports, functions, and logic needed
4. Do NOT generate snippets or partial code

Generate the improved COMPLETE code:"""

    def _should_stop_early(self, is_good_enough: bool, score: float) -> bool:
        """Determine if we should stop early"""
        if is_good_enough:
            self.log(f"[STOP_EARLY] Solution is good enough")
            return True

        if score >= 70 and self.attempt_count >= 2:
            self.log(f"[STOP_EARLY] Good score ({score}) after {self.attempt_count} attempts")
            return True

        if score >= 55 and self.attempt_count >= 3:
            self.log(f"[STOP_EARLY] Acceptable score ({score}) after {self.attempt_count} attempts")
            return True

        if self.consecutive_no_improvement >= self.max_no_improvement:
            self.log(f"[STOP_EARLY] No improvement for {self.max_no_improvement} attempts")
            return True

        return False

    def get_smart_cached_solution(self, error_type: str, query: str, original_task: str) -> Optional[str]:
        """Get cached solution - tries seeded cache format FIRST"""
        if not self.ai or not hasattr(self.ai, '_get_cached_error_search'):
            return None

        self.log(f"[SMART CACHE] Looking for {error_type}")

        # ====== STRATEGY 1: Try seeded cache format FIRST ======
        # This matches your pre-seeded cache keys!
        normalized_error = self._normalize_error_type(error_type)

        # Extract library from query
        query_lower = query.lower()
        libraries = [
            'control', 'matplotlib', 'numpy', 'scipy', 'pandas', 'sympy',
            'tensorflow', 'torch', 'sklearn', 'keras', 'transformers', 'opencv-python',
            'flask', 'django', 'fastapi', 'requests', 'beautifulsoup4', 'selenium',
            'polars', 'dask', 'seaborn', 'plotly', 'statsmodels',
            'slycot', 'scipy.signal',
            'tkinter', 'pygame', 'pyqt5', 'kivy', 'pyside6',
            'cv2', 'pillow', 'scikit-image', 'albumentations',
            'pydub', 'librosa', 'soundfile', 'pyaudio', 'wave',
            'pyopengl', 'moderngl', 'vispy', 'pyvista', 'trimesh'
        ]

        detected_lib = None
        for lib in libraries:
            if lib in query_lower:
                detected_lib = lib
                break

        if detected_lib:
            # Try with library-based query (matches seeded cache)
            lib_query = f"{detected_lib} python library API reference import documentation"
            self.log(f"[SMART CACHE] Trying library-based query: {lib_query}")

            cached = self.ai._get_cached_error_search(normalized_error, lib_query)
            if cached:
                self.log(f"[SMART CACHE] ✅ Found in SEEDED cache! ({len(cached)} chars)")
                return cached

        # ====== STRATEGY 2: Try full query (runtime cache) ======
        self.log(f"[SMART CACHE] Trying full query")
        cached = self.ai._get_cached_error_search(normalized_error, query)

        if cached:
            self.log(f"[SMART CACHE] ✅ Found in runtime cache")
            return cached

        self.log(f"[SMART CACHE] ❌ No cached solution found")
        return None


    def run(self, user_request: str):
        """Backwards compatibility wrapper"""
        return self.run_with_loop_detection(user_request)