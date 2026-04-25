import ast
import os
import sys
import re


# Files to always include
CORE_FILES = [
    "nova_assistant_v1.py",
    "nova_ai.py",
    "nova_router.py",
    "nova_manager.py",
    "nova_tts.py",
    "nova_whisper.py",
    "nova_widgets.py",
    "nova_selfimprove_ui.py",
    "agent_executor.py",
    "planner.py",
    "code_execution_loop.py",
    "mistake_memory.py",
    "Internet_Tools.py",
    "latex_window.py",
    "code_window.py",
    "code_display.py",
    "theme_manager.py",
    "self_improver.py",
    "paper_tools_window.py",
    "asr_whisper.py",
    "nova_web.py",
    "nova_memory.py",
    "nova_council.py",
    "nova_affect.py",

]

# Subdirectories to scan
SCAN_DIRS = [
    "tools",
]

# Files to skip
SKIP_FILES = {
    "tool_registry.py",
    "__init__.py",
}


def _get_project_root():
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def _read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"# ERROR reading {path}: {e}"


def _collect_sources(root):
    """Collect all relevant source files with labelled headers."""
    sections = []

    found   = [f for f in CORE_FILES if os.path.exists(os.path.join(root, f))]
    missing = [f for f in CORE_FILES if not os.path.exists(os.path.join(root, f))]
    print(f"[SELF_INSPECT] Root: {root}")
    print(f"[SELF_INSPECT] Found: {found}")
    print(f"[SELF_INSPECT] Missing: {missing}")

    for fname in CORE_FILES:
        path = os.path.join(root, fname)
        if os.path.exists(path):
            source = _read_file(path)
            sections.append(f"{'='*60}\nFILE: {fname}\n{'='*60}\n{source}")

    for subdir in SCAN_DIRS:
        dirpath = os.path.join(root, subdir)
        if not os.path.isdir(dirpath):
            continue
        for fname in sorted(os.listdir(dirpath)):
            if not fname.endswith(".py"):
                continue
            if fname in SKIP_FILES or fname.startswith("_"):
                continue
            path = os.path.join(dirpath, fname)
            source = _read_file(path)
            sections.append(f"{'='*60}\nFILE: {subdir}/{fname}\n{'='*60}\n{source}")

    return "\n\n".join(sections)


def _extract_sigs(source: str) -> list:
    """
    Extract def/class/async def lines using AST parsing.
    Immune to docstrings containing 'def' or 'class' keywords.
    Falls back to a multiline-string-aware scanner for unparseable fragments.
    """
    try:
        tree = ast.parse(source)
        definition_linenos = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                definition_linenos.add(node.lineno)
        source_lines = source.splitlines()
        return [source_lines[i - 1] for i in sorted(definition_linenos)]

    except SyntaxError:
        result = []
        in_multiline = False
        delim = None
        for line in source.splitlines():
            stripped = line.strip()
            for d in ('"""', "'''"):
                if stripped.count(d) % 2 == 1:
                    if not in_multiline:
                        in_multiline, delim = True, d
                    elif delim == d:
                        in_multiline, delim = False, None
                    break
            if not in_multiline and stripped.startswith(("def ", "class ", "async def ")):
                result.append(line)
        return result


def _build_method_index(full_source: str) -> dict:
    """
    Parse all file sections once and build a name → (body, filename) index.
    Single pass — O(1) lookups thereafter. Replaces per-word per-section parsing.
    """
    index = {}

    for section in full_source.split("=" * 60):
        if not section.strip():
            continue
        file_match = re.match(r'\nFILE: (.+?)\n', section)
        fname = file_match.group(1).strip() if file_match else "unknown"

        try:
            tree = ast.parse(section)
            section_lines = section.splitlines()

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    start = node.lineno - 1
                    end   = node.end_lineno
                    body  = "\n".join(section_lines[start:end])
                    name  = node.name

                    # Keep longest definition if name appears in multiple files
                    if name not in index or len(body) > len(index[name][0]):
                        index[name] = (body, fname)

        except SyntaxError:
            pass

    return index


def self_inspect(query=None):
    """
    Read Nova's entire source tree to answer questions about how it works.
    Covers nova_assistant.py, agent_executor.py, planner.py, and all tools/.
    """
    try:
        root = _get_project_root()
        full_source = _collect_sources(root)
        lines = full_source.splitlines()

        # Single parse pass over all files — used for all lookups below
        method_index = _build_method_index(full_source)

        if not query:
            sigs = _extract_sigs(full_source)
            return "SELF_INSPECT_SIGS:" + "\n".join(s.strip() for s in sigs)

        words = re.findall(r'[\w_]+', query)
        words_sorted = sorted(set(words), key=len, reverse=True)

        # O(1) dict lookup per word — no repeated parsing
        for word in words_sorted:
            if len(word) < 2:
                continue
            if word in method_index:
                body, fname = method_index[word]
                return (
                    f"SELF_INSPECT:{query}||METHOD:{word} (from {fname})\n"
                    f"{body[:8000]}"
                )

        # No method match — keyword search across all lines
        significant_words = [w for w in words_sorted if len(w) > 3]
        if significant_words:
            hits = []
            seen = set()
            for i, line in enumerate(lines):
                if any(w.lower() in line.lower() for w in significant_words):
                    block = range(max(0, i - 2), min(len(lines), i + 6))
                    for j in block:
                        if j not in seen:
                            hits.append(lines[j])
                            seen.add(j)
                    hits.append("---")
                if len(hits) > 300:
                    hits.append("... [truncated]")
                    break
            if hits:
                return f"SELF_INSPECT:{query}||KEYWORD_HITS:\n" + "\n".join(hits)

        # Nothing found — signatures only, with hallucination warning
        sigs = _extract_sigs(full_source)
        sigs_text = "\n".join(sigs)

        return (
            f"SELF_INSPECT:{query}||NOT_FOUND: No method or keyword match found for '{query}' in Nova source.\n"
            f"IMPORTANT: The following are ONLY function signatures — you do NOT have the method bodies. "
            f"Do NOT invent or guess what these functions contain.\n"
            f"Available signatures:\n{sigs_text}"
        )

    except Exception as e:
        return f"Could not read source: {e}"