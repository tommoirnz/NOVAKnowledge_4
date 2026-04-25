# mistake_memory.py - Persistent Mistake Learning System
import json
import os
import time
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
NEVER_WARN_ABOUT = {
    'os', 'sys', 're', 'json', 'time', 'datetime', 'threading',
    'subprocess', 'pathlib', 'math', 'random', 'collections',
    'itertools', 'functools', 'abc', 'io', 'copy', 'struct',
    'types', 'warnings', 'traceback', 'inspect', 'typing'
}


class MistakeMemory:
    """
    Persistent memory system that learns from coding mistakes across sessions.
    Prevents the AI from repeating the same failed approaches.
    """

    def __init__(self, cache_dir="cache", logger=None):
            """Initialize the mistake memory cache, loading any previously stored mistakes from disk."""
            self.cache_dir = cache_dir
            self.log = logger or print
            self.mistake_file = os.path.join(cache_dir, "mistake_memory.json")
            self.mistakes = []
            self.error_patterns = {}
            self.library_incompatibilities = {}
            os.makedirs(cache_dir, exist_ok=True)
            self._load_mistakes()
            self.log(f"[MISTAKE MEMORY] Initialized with {len(self.mistakes)} past mistakes")

    def _load_mistakes(self):
        """Load mistakes, error patterns, and library incompatibilities from the JSON cache file."""
        if not os.path.exists(self.mistake_file):
            self.log(f"[MISTAKE MEMORY] No existing mistake file - starting fresh")
            self._save_mistakes()
            return
        try:
            with open(self.mistake_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.mistakes = data.get("mistakes", [])
            self.error_patterns = data.get("error_patterns", {})
            self.library_incompatibilities = data.get("library_incompatibilities", {})
            self.log(f"[MISTAKE MEMORY] Loaded {len(self.mistakes)} mistakes from disk")
        except Exception as e:
            self.log(f"[MISTAKE MEMORY] Error loading: {e}")
            self.mistakes = []
            self.error_patterns = {}
            self.library_incompatibilities = {}

    def _save_mistakes(self):
        """Persist the current mistakes, error patterns, and incompatibilities to the JSON cache file."""
        try:
            data = {
                "mistakes": self.mistakes,
                "error_patterns": self.error_patterns,
                "library_incompatibilities": self.library_incompatibilities,
                "last_updated": datetime.now().isoformat()
            }
            with open(self.mistake_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            self.log(f"[MISTAKE MEMORY] Saved {len(self.mistakes)} mistakes to disk")
        except Exception as e:
            self.log(f"[MISTAKE MEMORY] Error saving: {e}")

    def classify_task(self, task: str) -> str:
        """Classify a task description into a category by scoring keyword matches."""
        task_lower = task.lower()
        classifications = {
            "audio_processing": ["audio", "sound", "speaker", "oscillator", "sinewave", "sounddevice", "frequency hz", "khz"],
            "3d_visualization": ["cube", "3d", "rotate", "tumble", "animation", "sphere", "mesh"],
            "control_systems": ["transfer function", "bode plot", "nyquist", "root locus", "pid controller", "control system", "state space"],
            "plotting": ["plot", "graph", "chart", "visualize", "matplotlib", "figure"],
            "data_analysis": ["data", "pandas", "dataframe", "csv", "analyze", "statistics"],
            "web_scraping": ["scrape", "web", "requests", "beautifulsoup", "html", "parse"],
            "machine_learning": ["train", "model", "neural", "tensorflow", "pytorch", "sklearn"],
            "image_processing": ["image", "opencv", "cv2", "pillow", "filter", "detection"],
            "simulation": ["simulate", "simulation", "physics", "dynamics"]
        }
        scores = {}
        for task_type, keywords in classifications.items():
            score = sum(1 for keyword in keywords if keyword in task_lower)
            if score > 0:
                scores[task_type] = score
        if scores:
            best_match = max(scores.items(), key=lambda x: x[1])
            return best_match[0]
        return "general"

    def extract_libraries(self, code_or_error: str) -> List[str]:
        """Extract library names from import statements and error messages in the given text."""
        libraries = set()
        import_pattern = r'import\s+(\w+)'
        matches = re.findall(import_pattern, code_or_error)
        libraries.update(matches)
        from_pattern = r'from\s+(\w+)'
        matches = re.findall(from_pattern, code_or_error)
        libraries.update(matches)
        module_pattern = r"No module named ['\"](\w+)['\"]"
        matches = re.findall(module_pattern, code_or_error)
        libraries.update(matches)
        attr_pattern = r"module ['\"](\w+)['\"]"
        matches = re.findall(attr_pattern, code_or_error)
        libraries.update(matches)
        return list(libraries)

    def save_mistake(self, task: str, error_type: str, failed_code: str,
                     error_output: str, lesson: str = None) -> bool:
        """Record a mistake for future reference."""
        try:
            task_type = self.classify_task(task)
            libraries = self.extract_libraries(failed_code + " " + error_output)
            if not lesson:
                lesson = self._generate_lesson(task_type, error_type, libraries, error_output)
            if self._is_bad_lesson(lesson, libraries):
                self.log(f"[MISTAKE MEMORY] Rejected bad lesson: {lesson[:60]}")
                return False
            mistake = {
                "timestamp": datetime.now().isoformat(),
                "task": task[:200],
                "task_type": task_type,
                "error_type": error_type.lower(),
                "libraries": libraries,
                "lesson": lesson,
                "error_snippet": error_output[:300]
            }
            if self._is_duplicate_mistake(mistake):
                self.log(f"[MISTAKE MEMORY] Duplicate mistake - updating count instead")
                self._increment_pattern_count(error_type, task_type)
                return False
            self.mistakes.append(mistake)
            pattern_key = f"{error_type}::{task_type}"
            if pattern_key not in self.error_patterns:
                self.error_patterns[pattern_key] = {"count": 1, "lesson": lesson, "libraries": libraries}
            else:
                self.error_patterns[pattern_key]["count"] += 1
            if len(libraries) > 0:
                for lib in libraries:
                    lib_key = f"{lib}::{task_type}"
                    if lib_key not in self.library_incompatibilities:
                        self.library_incompatibilities[lib_key] = {"error_count": 1, "common_error": error_type}
                    else:
                        self.library_incompatibilities[lib_key]["error_count"] += 1
            if len(self.mistakes) > 200:
                self.mistakes = self.mistakes[-200:]
            self._save_mistakes()
            self.log(f"[MISTAKE MEMORY] Saved mistake: {task_type} / {error_type}")
            return True
        except Exception as e:
            self.log(f"[MISTAKE MEMORY] Error saving mistake: {e}")
            return False

    def _is_bad_lesson(self, lesson: str, libraries: list) -> bool:
            """Returns True if the lesson is vague or incorrectly warns about approved modules."""
            lesson_lower = lesson.lower()
            for mod in NEVER_WARN_ABOUT:
                if f"don't use {mod}" in lesson_lower or f"not use {mod}" in lesson_lower:
                    return True
            vague = ["approach failed", "doesn't have the expected attributes"]
            return any(v in lesson_lower for v in vague)

    def _generate_lesson(self, task_type: str, error_type: str,
                         libraries: List[str], error_output: str) -> str:
        """Generate a human-readable lesson string from a task type, error type, and libraries."""
        if error_type == "modulenotfounderror" and libraries:
            real_libs = [l for l in libraries if l not in NEVER_WARN_ABOUT]
            if real_libs:
                return f"Don't use {real_libs[0]} for {task_type} tasks - it's not available or not appropriate"
            else:
                return f"Approach failed for {task_type} task with {error_type}"
        if error_type == "attributeerror" and libraries:
            if task_type == "3d_visualization" and "control" in libraries:
                return "Don't use control library for 3D graphics - use pygame, matplotlib, or opengl instead"
            return f"{libraries[0]} doesn't have the expected attributes for {task_type} tasks"
        if error_type == "timeouterror":
            return f"Code for {task_type} tasks took too long - simplify or use non-blocking approach"
        return f"Approach failed for {task_type} task with {error_type}"

    def _is_duplicate_mistake(self, new_mistake: Dict) -> bool:
        """Return True if a very similar mistake already exists in the last 10 recorded entries."""
        if len(self.mistakes) == 0:
            return False
        recent = self.mistakes[-10:]
        for old_mistake in recent:
            if (old_mistake["error_type"] == new_mistake["error_type"] and
                    old_mistake["task_type"] == new_mistake["task_type"]):
                old_libs = set(old_mistake.get("libraries", []))
                new_libs = set(new_mistake.get("libraries", []))
                if old_libs == new_libs:
                    return True
        return False

    def _increment_pattern_count(self, error_type: str, task_type: str):
        """Increment the occurrence count for an existing error pattern key."""
        pattern_key = f"{error_type}::{task_type}"
        if pattern_key in self.error_patterns:
            self.error_patterns[pattern_key]["count"] += 1
            self._save_mistakes()

    def get_relevant_warnings(self, task: str, max_warnings: int = 5) -> str:
        """Get warnings about past mistakes relevant to this task."""
        task_type = self.classify_task(task)
        task_lower = task.lower()
        potential_libs = self.extract_libraries(task)
        warnings = []
        for pattern_key, pattern_data in self.error_patterns.items():
            error_type, pattern_task_type = pattern_key.split("::")
            if pattern_task_type == task_type and pattern_data["count"] >= 2:
                warnings.append({"priority": 3, "text": f"COMMON MISTAKE for {task_type}: {pattern_data['lesson']}"})
        for lib in potential_libs:
            lib_key = f"{lib}::{task_type}"
            if lib_key in self.library_incompatibilities:
                incomp = self.library_incompatibilities[lib_key]
                if incomp["error_count"] >= 2:
                    warnings.append({"priority": 2, "text": f"{lib} has failed {incomp['error_count']}x for {task_type} tasks"})
        recent_mistakes = [
            m for m in self.mistakes[-20:]
            if (m["task_type"] == task_type and not m['lesson'].startswith("Approach failed"))
            or (m.get("error_type") == "best_practice" and
                any(kw in task_lower for kw in m.get("libraries", [])))
        ]
        for mistake in recent_mistakes[-3:]:
            warnings.append({"priority": 1, "text": f"Past mistake: {mistake['lesson']}"})
        warnings.sort(key=lambda x: x["priority"], reverse=True)
        warnings = warnings[:max_warnings]
        if not warnings:
            return ""
        warning_text = "\n" + "=" * 60 + "\n"
        warning_text += "WARNINGS - PAST MISTAKES ON SIMILAR TASKS:\n"
        warning_text += "=" * 60 + "\n"
        for w in warnings:
            warning_text += f"{w['text']}\n"
        warning_text += "=" * 60 + "\n"
        return warning_text

    def get_statistics(self) -> Dict[str, Any]:
        """Return a summary dict of total mistakes, error types, task types, and problem libraries."""
        stats = {
            "total_mistakes": len(self.mistakes),
            "error_types": {},
            "task_types": {},
            "most_common_pattern": None,
            "problem_libraries": []
        }
        for mistake in self.mistakes:
            error_type = mistake["error_type"]
            stats["error_types"][error_type] = stats["error_types"].get(error_type, 0) + 1
            task_type = mistake["task_type"]
            stats["task_types"][task_type] = stats["task_types"].get(task_type, 0) + 1
        if self.error_patterns:
            most_common = max(self.error_patterns.items(), key=lambda x: x[1]["count"])
            stats["most_common_pattern"] = {
                "pattern": most_common[0],
                "count": most_common[1]["count"],
                "lesson": most_common[1]["lesson"]
            }
        if self.library_incompatibilities:
            problem_libs = sorted(
                self.library_incompatibilities.items(),
                key=lambda x: x[1]["error_count"],
                reverse=True
            )[:5]
            stats["problem_libraries"] = [
                {"lib_task": lib, "errors": data["error_count"]}
                for lib, data in problem_libs
            ]
        return stats

    def clear_old_mistakes(self, days: int = 30):
        """Remove mistakes older than the given number of days and return the count removed."""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        original_count = len(self.mistakes)
        self.mistakes = [
            m for m in self.mistakes
            if datetime.fromisoformat(m["timestamp"]).timestamp() > cutoff_time
        ]
        removed = original_count - len(self.mistakes)
        if removed > 0:
            self._save_mistakes()
            self.log(f"[MISTAKE MEMORY] Cleared {removed} old mistakes")
        return removed

    def export_lessons(self) -> str:
        """Format all recorded lessons grouped by task type into a readable string."""
        if not self.mistakes:
            return "No mistakes recorded yet."
        output = "=" * 60 + "\n"
        output += "LESSONS LEARNED FROM PAST MISTAKES\n"
        output += "=" * 60 + "\n\n"
        by_task_type = {}
        for mistake in self.mistakes:
            task_type = mistake["task_type"]
            if task_type not in by_task_type:
                by_task_type[task_type] = []
            by_task_type[task_type].append(mistake)
        for task_type, mistakes in sorted(by_task_type.items()):
            output += f"\n{task_type.upper()} TASKS:\n"
            output += "-" * 60 + "\n"
            lessons = set(m["lesson"] for m in mistakes)
            for lesson in lessons:
                count = sum(1 for m in mistakes if m["lesson"] == lesson)
                output += f"  - {lesson} (occurred {count}x)\n"
        return output