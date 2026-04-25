#!/usr/bin/env python3
"""
nova_evolve_loop.py  —  Nova Self-Evolution Controller
=======================================================
Runs overnight, autonomously proposing, testing, and committing
improvements to Nova's codebase. Full git-backed with auto-revert
on any regression.

Architecture per cycle:
  1.  Git-snapshot current state
  2.  Run fixed eval suite  →  baseline score
  3.  Meta-AI reads Nova source  →  proposes ONE targeted change
  4.  Apply change to allowed file
  5.  Python syntax check
  6.  Re-run eval suite  →  new score
  7.  New score > baseline  →  git commit + log SUCCESS
      New score ≤ baseline  →  git revert  + log FAILURE
  8.  Sleep CYCLE_DELAY seconds, repeat up to MAX_CYCLES

Usage:
  python nova_evolve_loop.py              # Run the loop
  python nova_evolve_loop.py --dry-run    # Propose changes only, don't write
  python nova_evolve_loop.py --report     # Generate HTML morning report and exit
  python nova_evolve_loop.py --eval-only  # Run eval suite once and exit
"""

import os, sys, json, time, subprocess, ast, shutil, textwrap, hashlib
import datetime, argparse, re, traceback
from pathlib import Path

# Force UTF-8 output on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ═══════════════════════════════════════════════════════════
#  CONFIGURATION  —  edit before first run
# ═══════════════════════════════════════════════════════════

NOVA_DIR = Path(os.environ.get("NOVA_DIR", r"C:\Users\OEM\nova"))   # Nova source root
NOVA_WEB_URL  = os.environ.get("NOVA_URL", "https://192.168.178.58:8080")
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY", os.environ.get("OPENROUTER_API_KEY", ""))
META_MODEL    = "anthropic/claude-sonnet-4-5"   # model that proposes changes
EVAL_MODEL    = "anthropic/claude-sonnet-4-5"   # model that scores outputs

LOG_FILE      = Path("nova_evolve_log.json")
EVAL_SUITE    = Path("nova_eval_suite.json")    # NEVER modified by loop
REPORT_FILE   = Path("nova_evolve_report.html")

MAX_CYCLES    = 60          # hard ceiling (60 × ~2 min ≈ 2 hours; adjust freely)
CYCLE_DELAY   = 90          # seconds to rest between cycles
NOVA_TIMEOUT  = 120          # seconds to wait for Nova to respond to a test prompt
SCORE_IMPROVE_THRESHOLD = 0.05   # new score must beat baseline by this fraction

# Files the meta-AI may propose changes to (paths relative to NOVA_DIR)
ALLOWED_FILES = [
    "nova_assistant_v1.py",
    "nova_router.py",
    "nova_selfimprove_ui.py",
    "nova_web.py",
    "tools/diagram_tool.py",
    "tools/file_explorer.py",
    "tools/sympy_exec.py",
    "nova_state.py",
    "nova_planner.py",
]

# Files the loop will NEVER touch regardless of what the meta-AI says
PROTECTED = {
    "nova_evolve_loop.py",
    "nova_eval_suite.json",
    "nova_evolve_log.json",
    ".git",
}

# ═══════════════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════════════

class Log:
    def __init__(self):
        self.entries = []
        if LOG_FILE.exists():
            try:
                self.entries = json.loads(LOG_FILE.read_text(encoding="utf-8"))
            except Exception:
                self.entries = []

    def record(self, entry: dict):
        entry["ts"] = datetime.datetime.now().isoformat(timespec="seconds")
        self.entries.append(entry)
        LOG_FILE.write_text(json.dumps(self.entries, indent=2), encoding="utf-8")
        tag = entry.get("event", "?")
        msg = entry.get("message", "")
        print(f"  [{tag}] {msg}")

log = Log()

def banner(text: str):
    bar = "-" * 60
    print(f"\n{bar}\n  {text}\n{bar}")

# ═══════════════════════════════════════════════════════════
#  GIT HELPERS
# ═══════════════════════════════════════════════════════════

def git(args: list, cwd=NOVA_DIR) -> tuple[int, str]:
    r = subprocess.run(
        ["git"] + args, cwd=cwd, capture_output=True, text=True
    )
    return r.returncode, (r.stdout + r.stderr).strip()

def ensure_git_repo():
    code, _ = git(["rev-parse", "--is-inside-work-tree"])
    if code != 0:
        git(["init"])
        git(["add", "-A"])
        git(["commit", "-m", "nova_evolve: initial snapshot"])
        print("  [git] Initialised new repo and committed baseline.")
    else:
        # Make sure we have at least one commit (clean working tree to revert to)
        code2, out = git(["status", "--porcelain"])
        if out.strip():
            git(["add", "-A"])
            git(["commit", "-m", "nova_evolve: pre-run snapshot"])
            print("  [git] Committed dirty working tree as baseline.")

def commit_change(filepath: str, cycle: int, description: str):
    rel = Path(filepath).relative_to(NOVA_DIR) if Path(filepath).is_absolute() else filepath
    git(["add", str(rel)])
    msg = f"nova_evolve cycle {cycle}: {description[:72]}"
    git(["commit", "-m", msg])

def revert_file(filepath: str):
    rel = Path(filepath).relative_to(NOVA_DIR) if Path(filepath).is_absolute() else filepath
    git(["checkout", "HEAD", "--", str(rel)])

# ═══════════════════════════════════════════════════════════
#  EVAL SUITE  —  run fixed prompts against Nova, score outputs
# ═══════════════════════════════════════════════════════════

def load_eval_suite() -> list[dict]:
    if not EVAL_SUITE.exists():
        raise FileNotFoundError(f"Eval suite not found: {EVAL_SUITE}")
    data = json.loads(EVAL_SUITE.read_text(encoding="utf-8"))
    return data["tests"]

def call_nova(prompt: str) -> str | None:
    """Send a prompt to Nova via /api/send, poll /api/history for the response."""
    base = NOVA_WEB_URL.rstrip("/")
    send_url    = f"{base}/api/send"
    history_url = f"{base}/api/history"
    state_url   = f"{base}/api/state"

    try:
        def get_history():
            r = requests.get(history_url, timeout=10, verify=False)
            if not r.ok:
                return []
            raw = r.json()
            if isinstance(raw, dict):
                return raw.get("history", [])
            return raw if isinstance(raw, list) else []

        def is_thinking():
            try:
                r = requests.get(state_url, timeout=5, verify=False)
                return r.json().get("thinking", False) if r.ok else False
            except Exception:
                return False

        def count_assistant(hist):
            return sum(1 for e in hist
                       if e.get("role") == "assistant" or e.get("result"))

        # Baseline assistant count before sending
        before_count = count_assistant(get_history())

        # Send the prompt
        requests.post(
            send_url,
            json={"message": prompt},
            timeout=10,
            verify=False,
        )

        # Wait for Nova to start thinking
        time.sleep(2)

        # Poll until Nova finishes thinking AND a new reply appears
        deadline = time.time() + NOVA_TIMEOUT
        while time.time() < deadline:
            time.sleep(4)
            try:
                # Skip if Nova is still thinking
                if is_thinking():
                    continue
                hist = get_history()
                if count_assistant(hist) > before_count:
                    for entry in reversed(hist):
                        if entry.get("result"):
                            return entry["result"]
                        if entry.get("role") == "assistant":
                            return entry.get("content", "")
            except Exception:
                continue
        return None   # timed out
    except Exception:
        return None

def score_response(prompt: str, response: str | None, criteria: str) -> float:
    """Ask the eval model to score Nova's response 0.0–1.0."""
    if response is None:
        return 0.0
    system = textwrap.dedent("""\
        You are an objective evaluator. Score the AI response 0.0 to 1.0 based
        on the provided criteria. Reply with ONLY a JSON object:
        {"score": <float 0-1>, "reason": "<one sentence>"}
        No markdown, no preamble, no backticks.
    """)
    user = f"""PROMPT:\n{prompt}\n\nRESPONSE:\n{response[:3000]}\n\nCRITERIA:\n{criteria}"""
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}",
                     "Content-Type": "application/json"},
            json={"model": EVAL_MODEL, "max_tokens": 150,
                  "messages": [{"role": "system", "content": system},
                                {"role": "user",   "content": user}]},
            timeout=30,
        )
        text = r.json()["choices"][0]["message"]["content"].strip()
        # Strip markdown fences if present
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"\s*```$",     "", text)
        text = text.strip()
        parsed = json.loads(text)
        score = float(parsed["score"])
        return max(0.0, min(1.0, score))  # clamp to valid range
    except Exception as e:
        # Try regex fallback to extract score from malformed response
        try:
            m = re.search(r'"score"\s*:\s*([0-9.]+)', text)
            if m:
                return max(0.0, min(1.0, float(m.group(1))))
        except Exception:
            pass
        return 0.5   # neutral fallback

def run_eval_suite(verbose=False) -> tuple[float, list[dict]]:
    """Run every test in the suite. Returns (mean_score, detailed_results)."""
    tests = load_eval_suite()
    results = []
    for t in tests:
        response = call_nova(t["prompt"])
        score    = score_response(t["prompt"], response, t["criteria"])
        entry    = {"id": t["id"], "prompt": t["prompt"],
                    "response": response, "score": score}
        results.append(entry)
        if verbose:
            print(f"    [{t['id']}] score={score:.2f}  {t['prompt'][:60]}")
        time.sleep(5)  # let Nova settle before next prompt
    mean = sum(r["score"] for r in results) / len(results) if results else 0.0
    return mean, results

# ═══════════════════════════════════════════════════════════
#  SOURCE READER  —  feed Nova's source to the meta-AI
# ═══════════════════════════════════════════════════════════

MAX_SOURCE_CHARS = 60_000   # stay inside context budget

def read_nova_sources() -> dict[str, str]:
    """Read allowed source files that exist. Truncate to budget."""
    sources = {}
    total = 0
    for rel in ALLOWED_FILES:
        p = NOVA_DIR / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if total + len(text) > MAX_SOURCE_CHARS:
            remaining = MAX_SOURCE_CHARS - total
            if remaining < 200:
                break
            text = text[:remaining] + "\n... [TRUNCATED]"
        sources[rel] = text
        total += len(text)
        if total >= MAX_SOURCE_CHARS:
            break
    return sources

# ═══════════════════════════════════════════════════════════
#  META-AI  —  proposes a single, targeted code change
# ═══════════════════════════════════════════════════════════

SYSTEM_PROPOSE = textwrap.dedent("""\
    You are a senior Python engineer reviewing an AI assistant codebase called Nova.
    Your job: propose ONE specific, self-contained improvement to ONE file.

    Rules:
    - Only modify files from the ALLOWED list.
    - The change must be safe: no removing tools, no breaking imports.
    - Prefer bug fixes and reliability improvements over new features.
    - Focus on whichever file has the lowest test scores.
    - Output ONLY valid JSON — no markdown, no preamble:

    {
      "file": "<relative path from ALLOWED list>",
      "description": "<one sentence: what and why>",
      "search": "<exact existing code block to replace (≥3 lines)>",
      "replace": "<new code block that replaces search>"
    }

    The "search" string must appear verbatim in the file. The "replace" must be
    syntactically valid Python. If you cannot propose a safe, confident improvement,
    reply: {"skip": true, "reason": "<why>"}
""")

def propose_change(eval_results: list[dict], cycle: int) -> dict | None:
    """Ask the meta-AI for one improvement. Returns parsed JSON or None."""
    sources = read_nova_sources()
    if not sources:
        print("  [meta] No source files found — check NOVA_DIR config.")
        return None

    # Summarise which tests scored poorly
    weak = sorted(eval_results, key=lambda r: r["score"])[:5]
    weak_text = "\n".join(
        f"  [{r['id']}] score={r['score']:.2f}: {r['prompt'][:80]}"
        for r in weak
    )

    source_block = "\n\n".join(
        f"### {path} ###\n{code}" for path, code in sources.items()
    )

    user = textwrap.dedent(f"""\
        CYCLE: {cycle}
        ALLOWED FILES: {', '.join(ALLOWED_FILES)}

        WEAKEST TEST RESULTS (focus here):
        {weak_text}

        NOVA SOURCE CODE:
        {source_block}

        Propose one improvement.
    """)

    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}",
                     "Content-Type": "application/json"},
            json={"model": META_MODEL, "max_tokens": 1500,
                  "messages": [{"role": "system", "content": SYSTEM_PROPOSE},
                                {"role": "user",   "content": user}]},
            timeout=60,
        )
        raw = r.json()["choices"][0]["message"]["content"].strip()
        # Strip markdown fences if the model was naughty
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$",     "", raw)
        return json.loads(raw)
    except Exception as e:
        print(f"  [meta] Proposal failed: {e}")
        return None

# ═══════════════════════════════════════════════════════════
#  APPLY CHANGE
# ═══════════════════════════════════════════════════════════

def apply_change(proposal: dict, dry_run=False) -> tuple[bool, str]:
    """
    Apply search→replace patch to the specified file.
    Returns (success, message).
    """
    rel_path = proposal.get("file", "")
    # Safety: must be in allowed list and not protected
    if rel_path not in ALLOWED_FILES:
        return False, f"File '{rel_path}' not in ALLOWED_FILES."
    if any(p in rel_path for p in PROTECTED):
        return False, f"File '{rel_path}' is protected."

    full_path = NOVA_DIR / rel_path
    if not full_path.exists():
        return False, f"File does not exist: {full_path}"

    original = full_path.read_text(encoding="utf-8")
    search  = proposal.get("search", "")
    replace = proposal.get("replace", "")

    if not search or not replace:
        return False, "Proposal missing 'search' or 'replace' fields."

    if search not in original:
        return False, "Search string not found verbatim in file."

    if original.count(search) > 1:
        return False, "Search string is ambiguous (appears more than once)."

    patched = original.replace(search, replace, 1)

    # Syntax check
    try:
        ast.parse(patched)
    except SyntaxError as e:
        return False, f"Syntax error in replacement: {e}"

    if dry_run:
        print(f"\n  [dry-run] Would patch {rel_path}:")
        print(f"    REMOVE: {search[:120].strip()}")
        print(f"    INSERT: {replace[:120].strip()}")
        return True, "dry-run OK"

    full_path.write_text(patched, encoding="utf-8")
    return True, f"Patched {rel_path}"

# ═══════════════════════════════════════════════════════════
#  REPORT GENERATOR
# ═══════════════════════════════════════════════════════════

def generate_report():
    if not LOG_FILE.exists():
        print("No log file found.")
        return
    entries = json.loads(LOG_FILE.read_text(encoding="utf-8"))
    cycles  = [e for e in entries if e.get("event") == "CYCLE_COMPLETE"]
    n_ok    = sum(1 for c in cycles if c.get("committed"))
    n_fail  = len(cycles) - n_ok
    scores  = [c.get("new_score", 0) for c in cycles]

    rows = ""
    for c in cycles:
        committed = c.get("committed", False)
        colour = "#2ecc71" if committed else "#e74c3c"
        status = "✓ COMMITTED" if committed else "✗ REVERTED"
        rows += (
            f"<tr>"
            f"<td>{c.get('cycle','?')}</td>"
            f"<td>{c.get('ts','')}</td>"
            f"<td>{c.get('file','')}</td>"
            f"<td title='{c.get('description','')}'>"
            f"  {c.get('description','')[:80]}</td>"
            f"<td>{c.get('baseline_score', 0):.3f}</td>"
            f"<td>{c.get('new_score', 0):.3f}</td>"
            f"<td style='color:{colour};font-weight:bold'>{status}</td>"
            f"</tr>\n"
        )

    score_trend = ", ".join(f"{s:.3f}" for s in scores[-30:])
    html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
<title>Nova Evolution Report — {datetime.date.today()}</title>
<style>
  body {{font-family: 'Segoe UI', sans-serif; background:#1a1a2e; color:#e0e0e0; padding:2em}}
  h1   {{color:#00d4ff; font-size:2em}}
  h2   {{color:#7ec8e3; border-bottom:1px solid #333; padding-bottom:.3em}}
  table{{width:100%; border-collapse:collapse; font-size:.9em}}
  th   {{background:#0f3460; padding:.6em; text-align:left}}
  td   {{padding:.5em; border-bottom:1px solid #2a2a4a}}
  tr:hover td {{background:#1e1e3e}}
  .stat{{display:inline-block; background:#0f3460; padding:1em 2em;
         border-radius:8px; margin:.5em; text-align:center}}
  .stat .val {{font-size:2em; font-weight:bold; color:#00d4ff}}
  .stat .lbl {{font-size:.85em; color:#888}}
  canvas{{max-width:100%; background:#0f3460; border-radius:8px; margin-top:1em}}
</style></head><body>
<h1>🧬 Nova Self-Evolution Report</h1>
<p>Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

<h2>Summary</h2>
<div class='stat'><div class='val'>{len(cycles)}</div><div class='lbl'>Cycles Run</div></div>
<div class='stat'><div class='val' style='color:#2ecc71'>{n_ok}</div><div class='lbl'>Improvements Committed</div></div>
<div class='stat'><div class='val' style='color:#e74c3c'>{n_fail}</div><div class='lbl'>Reverted</div></div>
<div class='stat'><div class='val'>{max(scores):.3f if scores else 0}</div><div class='lbl'>Peak Score</div></div>

<h2>Score Trend</h2>
<canvas id='chart' height='80'></canvas>
<script>
const scores=[{score_trend}];
const canvas=document.getElementById('chart');
const ctx=canvas.getContext('2d');
canvas.width=canvas.offsetWidth||900; canvas.height=200;
const w=canvas.width, h=canvas.height, n=scores.length;
const mn=Math.min(...scores)*.95, mx=Math.max(...scores)*1.02;
ctx.strokeStyle='#00d4ff'; ctx.lineWidth=2; ctx.beginPath();
scores.forEach((s,i)=>{{
  const x=i/(n-1)*w, y=h-(s-mn)/(mx-mn)*h;
  i===0?ctx.moveTo(x,y):ctx.lineTo(x,y);
}});
ctx.stroke();
</script>

<h2>Cycle Log</h2>
<table>
<tr><th>#</th><th>Time</th><th>File</th><th>Change</th>
    <th>Baseline</th><th>New Score</th><th>Result</th></tr>
{rows}
</table>
</body></html>"""

    REPORT_FILE.write_text(html, encoding="utf-8")
    print(f"Report written to: {REPORT_FILE.resolve()}")

# ═══════════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run",   action="store_true",
                        help="Propose changes but don't write or commit")
    parser.add_argument("--report",    action="store_true",
                        help="Generate HTML report from log and exit")
    parser.add_argument("--eval-only", action="store_true",
                        help="Run eval suite once, print scores, exit")
    parser.add_argument("--cycles",    type=int, default=MAX_CYCLES,
                        help=f"Override max cycles (default {MAX_CYCLES})")
    args = parser.parse_args()

    if args.report:
        generate_report()
        return

    if not OPENROUTER_KEY:
        print("ERROR: OPENROUTER_API_KEY environment variable not set.")
        sys.exit(1)

    if args.eval_only:
        banner("Eval Suite — single run")
        mean, results = run_eval_suite(verbose=True)
        print(f"\n  Mean score: {mean:.4f}")
        return

    banner(f"Nova Evolution Loop  |  max_cycles={args.cycles}  dry_run={args.dry_run}")
    log.record({"event": "START", "message": f"Loop started. max_cycles={args.cycles}, dry_run={args.dry_run}"})

    if not args.dry_run:
        ensure_git_repo()

    for cycle in range(1, args.cycles + 1):
        banner(f"Cycle {cycle}/{args.cycles}")

        # ── 1. Baseline eval ──────────────────────────────────
        print("  Running baseline eval suite...")
        baseline_score, baseline_results = run_eval_suite()
        print(f"  Baseline score: {baseline_score:.4f}")

        # ── 2. Propose change ─────────────────────────────────
        print("  Asking meta-AI for improvement proposal...")
        proposal = propose_change(baseline_results, cycle)

        if proposal is None:
            log.record({"event": "SKIP", "cycle": cycle,
                        "message": "Meta-AI returned no proposal."})
            time.sleep(CYCLE_DELAY)
            continue

        if proposal.get("skip"):
            reason = proposal.get("reason", "No reason given.")
            log.record({"event": "SKIP", "cycle": cycle, "message": reason})
            print(f"  Meta-AI chose to skip: {reason}")
            time.sleep(CYCLE_DELAY)
            continue

        desc = proposal.get("description", "")
        file = proposal.get("file", "")
        print(f"  Proposal: [{file}] {desc}")

        # ── 3. Apply change ───────────────────────────────────
        ok, msg = apply_change(proposal, dry_run=args.dry_run)
        if not ok:
            log.record({"event": "PATCH_FAIL", "cycle": cycle,
                        "file": file, "message": msg})
            print(f"  Patch failed: {msg}")
            time.sleep(CYCLE_DELAY)
            continue

        if args.dry_run:
            log.record({"event": "DRY_RUN", "cycle": cycle,
                        "file": file, "description": desc, "message": msg})
            time.sleep(CYCLE_DELAY)
            continue

        # ── 4. Re-evaluate ────────────────────────────────────
        print("  Re-running eval suite after patch...")
        new_score, new_results = run_eval_suite(verbose=False)
        print(f"  New score:      {new_score:.4f}  (Δ {new_score - baseline_score:+.4f})")

        committed = False
        if new_score >= baseline_score + SCORE_IMPROVE_THRESHOLD:
            commit_change(NOVA_DIR / file, cycle, desc)
            committed = True
            print(f"  ✓ COMMITTED — improvement confirmed.")
        else:
            revert_file(NOVA_DIR / file)
            print(f"  ✗ REVERTED  — score did not improve by threshold.")

        log.record({
            "event":          "CYCLE_COMPLETE",
            "cycle":          cycle,
            "file":           file,
            "description":    desc,
            "baseline_score": round(baseline_score, 4),
            "new_score":      round(new_score, 4),
            "delta":          round(new_score - baseline_score, 4),
            "committed":      committed,
            "message":        ("COMMITTED" if committed else "REVERTED") + f": {desc}",
        })

        # ── 5. Rest ───────────────────────────────────────────
        time.sleep(CYCLE_DELAY)

    banner("Loop complete")
    log.record({"event": "DONE", "message": f"Completed {args.cycles} cycles."})
    generate_report()
    print(f"Report: {REPORT_FILE.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Generating report...")
        generate_report()
