import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as pe

# ─────────────────────────────────────────────
#  FIGURE SETUP
# ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(22, 15))
ax.set_xlim(0, 22)
ax.set_ylim(0, 15)
ax.axis("off")
fig.patch.set_facecolor("#0D1117")
ax.set_facecolor("#0D1117")

# ─────────────────────────────────────────────
#  COLOR PALETTE
# ─────────────────────────────────────────────
C = {
    "input":    "#1F6FEB",
    "parse":    "#388BFD",
    "plan":     "#A371F7",
    "reason":   "#F78166",
    "retrieve": "#3FB950",
    "generate": "#D29922",
    "safety":   "#EC6547",
    "output":   "#58A6FF",
    "arrow":    "#8B949E",
    "text":     "#E6EDF3",
    "muted":    "#8B949E",
    "border":   "#30363D",
    "accent":   "#F0883E",
    "panel":    "#161B22",
    "bg":       "#0D1117",
    "feedback": "#3FB950",
}

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def draw_block(ax, x, y, w, h, label, sublabel, color, icon="", radius=0.32):
    # Drop shadow
    ax.add_patch(FancyBboxPatch(
        (x + 0.07, y - 0.07), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        linewidth=0, facecolor="#000000", alpha=0.45, zorder=2
    ))
    # Main body
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        linewidth=1.4, edgecolor=color,
        facecolor=C["panel"], alpha=0.93, zorder=3
    ))
    # Left accent bar
    ax.add_patch(FancyBboxPatch(
        (x, y), 0.17, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        linewidth=0, facecolor=color, alpha=0.88, zorder=4
    ))
    # Label
    ax.text(x + 0.42, y + h * 0.63,
            f"{icon}  {label}",
            fontsize=10, fontweight="bold",
            color=C["text"], va="center", ha="left",
            fontfamily="monospace", zorder=5)
    # Sublabel
    ax.text(x + 0.42, y + h * 0.27,
            sublabel,
            fontsize=7.2, color=C["muted"],
            va="center", ha="left",
            fontfamily="monospace", zorder=5)


def draw_arrow(ax, x1, y1, x2, y2, color=None, lw=2.0,
               label="", curved=False):
    color = color or C["arrow"]
    cs = "arc3,rad=0.28" if curved else "arc3,rad=0.0"
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(
                    arrowstyle="-|>", color=color, lw=lw,
                    connectionstyle=cs, mutation_scale=17
                ), zorder=6)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.12, my, label, fontsize=6.8,
                color=color, va="center",
                fontfamily="monospace", zorder=7)


def draw_badge(ax, x, y, text, color):
    ax.add_patch(FancyBboxPatch(
        (x, y), 2.2, 0.36,
        boxstyle="round,pad=0,rounding_size=0.18",
        linewidth=1, edgecolor=color,
        facecolor=color, alpha=0.16, zorder=5
    ))
    ax.text(x + 1.1, y + 0.18, text,
            fontsize=6.8, color=color,
            ha="center", va="center",
            fontfamily="monospace", fontweight="bold", zorder=6)


def draw_lane(ax, x, y, w, h, title):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0,rounding_size=0.5",
        linewidth=1, edgecolor=C["border"],
        facecolor=C["panel"], alpha=0.5, zorder=1
    ))
    ax.text(x + w / 2, y + h - 0.22, title,
            fontsize=7, color=C["muted"],
            ha="center", va="center",
            fontfamily="monospace", fontweight="bold", zorder=2)


# ─────────────────────────────────────────────
#  TITLE
# ─────────────────────────────────────────────
ax.text(11, 14.45,
        "AI Assistant  ·  Python Pipeline Architecture",
        fontsize=18, fontweight="bold", color=C["text"],
        ha="center", va="center", fontfamily="monospace", zorder=10,
        path_effects=[pe.withStroke(linewidth=5, foreground=C["bg"])])

ax.text(11, 14.02,
        "user_input → tokenize → intent → plan → reason → retrieve → format → safety → output",
        fontsize=8.5, color=C["muted"],
        ha="center", va="center", fontfamily="monospace", zorder=10)

ax.plot([1.2, 20.8], [13.75, 13.75],
        color=C["border"], lw=0.9, zorder=5)

# ─────────────────────────────────────────────
#  SWIM LANES
# ─────────────────────────────────────────────
draw_lane(ax, 0.3,  0.4, 5.6, 13.2, "INPUT  &  PRE-PROCESSING")
draw_lane(ax, 6.2,  0.4, 7.8, 13.2, "CORE REASONING LAYER")
draw_lane(ax, 14.3, 0.4, 7.2, 13.2, "OUTPUT  &  OBSERVABILITY")

# ─────────────────────────────────────────────
#  BLOCKS
# ─────────────────────────────────────────────
BW, BH = 5.1, 0.92

# ── INPUT / PRE-PROCESSING ───────────────────
input_blocks = [
    (0.55, 12.35, BW, BH, "user_input()",
     "stdin · API endpoint · WebSocket frame",
     C["input"], "📥"),

    (0.55, 11.05, BW, BH, "tokenize_and_clean()",
     "regex strip · unicode normalize · BOM remove",
     C["parse"], "🔤"),

    (0.55,  9.75, BW, BH, "intent_classifier()",
     "rule-based + heuristic intent tagging",
     C["parse"], "🏷️"),

    (0.55,  8.45, BW, BH, "context_manager()",
     "session dict · sliding window · token budget",
     C["parse"], "🗂️"),

    (0.55,  7.15, BW, BH, "plan_builder()",
     "PLAN: parse → reason → retrieve → respond",
     C["plan"], "📋"),

    (0.55,  5.85, BW, BH, "constraint_checker()",
     "length · scope · forbidden topics · format rules",
     C["plan"], "🔒"),

    (0.55,  4.55, BW, BH, "prompt_assembler()",
     "system_prompt + context + plan + user_msg",
     C["plan"], "🧩"),

    (0.55,  3.25, BW, BH, "token_budget_guard()",
     "tiktoken count · truncate · summarise overflow",
     C["plan"], "💰"),
]

# ── CORE REASONING ───────────────────────────
BW2 = 7.4
reason_blocks = [
    (6.45, 12.35, BW2, BH, "reasoning_engine.run()",
     "chain-of-thought · step decomposition · self-critique loop",
     C["reason"], "🧠"),

    (6.45, 11.05, BW2, BH, "knowledge_retriever()",
     "vector similarity search · BM25 fallback · source ranking",
     C["retrieve"], "🔍"),

    (6.45,  9.75, BW2, BH, "tool_dispatcher()",
     "code_exec() · web_search() · calculator() · file_reader()",
     C["retrieve"], "🛠️"),

    (6.45,  8.45, BW2, BH, "multi_step_planner()",
     "DAG task graph · dependency resolution · parallel subtasks",
     C["reason"], "🗺️"),

    (6.45,  7.15, BW2, BH, "self_consistency_check()",
     "N-sample voting · contradiction detector · confidence score",
     C["reason"], "✅"),

    (6.45,  5.85, BW2, BH, "response_formatter()",
     "markdown render · code highlight · table builder · LaTeX",
     C["generate"], "📝"),

    (6.45,  4.55, BW2, BH, "citation_linker()",
     "source attribution · footnote injection · URL validation",
     C["generate"], "🔗"),

    (6.45,  3.25, BW2, BH, "safety_filter()",
     "PII redact · harm classifier · policy gate · refusal handler",
     C["safety"], "🛡️"),
]

# ── OUTPUT / OBSERVABILITY ───────────────────
BW3 = 6.8
output_blocks = [
    (14.55, 12.35, BW3, BH, "stream_writer()",
     "SSE · chunked HTTP · WebSocket push",
     C["output"], "📡"),

    (14.55, 11.05, BW3, BH, "cache_store()",
     "Redis TTL · semantic dedup · embedding index",
     C["output"], "💾"),

    (14.55,  9.75, BW3, BH, "logger()",
     "structured JSON · latency · token usage · trace_id",
     C["output"], "📊"),

    (14.55,  8.45, BW3, BH, "feedback_collector()",
     "thumbs · RLHF signal · correction capture",
     C["output"], "👍"),

    (14.55,  7.15, BW3, BH, "metrics_emitter()",
     "Prometheus counters · p50/p95 latency · error rate",
     C["output"], "📈"),

    (14.55,  5.85, BW3, BH, "session_updater()",
     "append turn · compress history · persist to DB",
     C["output"], "🔄"),

    (14.55,  4.55, BW3, BH, "rate_limiter()",
     "token bucket · per-user quota · backpressure",
     C["output"], "⏱️"),

    (14.55,  3.25, BW3, BH, "final_response()",
     "JSON envelope · HTTP 200 · EOS token · done flag",
     C["input"], "📤"),
]

for b in input_blocks + reason_blocks + output_blocks:
    draw_block(ax, *b)

# ─────────────────────────────────────────────
#  ARROWS — INPUT LANE (vertical)
# ─────────────────────────────────────────────
in_cx = 3.1
in_ys = [b[1] for b in input_blocks]
in_colors = [C["input"], C["parse"], C["parse"], C["parse"],
             C["plan"],  C["plan"],  C["plan"],  C["plan"]]

for i in range(len(in_ys) - 1):
    draw_arrow(ax, in_cx, in_ys[i],
                   in_cx, in_ys[i + 1] + BH,
               color=in_colors[i + 1], lw=2.1)

# ─────────────────────────────────────────────
#  ARROWS — REASONING LANE (vertical)
# ─────────────────────────────────────────────
re_cx = 10.15
re_ys = [b[1] for b in reason_blocks]
re_colors = [C["reason"], C["retrieve"], C["retrieve"],
             C["reason"], C["reason"],   C["generate"],
             C["generate"], C["safety"]]

for i in range(len(re_ys) - 1):
    draw_arrow(ax, re_cx, re_ys[i],
                   re_cx, re_ys[i + 1] + BH,
               color=re_colors[i + 1], lw=2.1)

# ─────────────────────────────────────────────
#  ARROWS — OUTPUT LANE (vertical)
# ─────────────────────────────────────────────
out_cx = 17.95
out_ys = [b[1] for b in output_blocks]

for i in range(len(out_ys) - 1):
    draw_arrow(ax, out_cx, out_ys[i],
                   out_cx, out_ys[i + 1] + BH,
               color=C["output"], lw=2.1)

# ─────────────────────────────────────────────
#  HANDOFF ARROWS
# ─────────────────────────────────────────────
# token_budget_guard → reasoning_engine  (curved cross-lane)
draw_arrow(ax,
           in_cx,  in_ys[-1],          # bottom of input lane
           re_cx,  re_ys[0] + BH,      # top of reasoning lane
           color=C["accent"], lw=2.6,
           label="assembled prompt", curved=True)

# safety_filter → stream_writer  (curved cross-lane)
draw_arrow(ax,
           re_cx,  re_ys[-1],          # bottom of reasoning lane
           out_cx, out_ys[0] + BH,     # top of output lane
           color=C["accent"], lw=2.6,
           label="safe payload", curved=True)

# ─────────────────────────────────────────────
#  FEEDBACK LOOP
# ─────────────────────────────────────────────
ax.annotate("", xy=(0.55, 8.91), xytext=(14.55, 3.71),
            arrowprops=dict(
                arrowstyle="-|>",
                color=C["feedback"], lw=1.8,
                connectionstyle="arc3,rad=-0.32",
                mutation_scale=15, linestyle="dashed"
            ), zorder=6)
ax.text(7.5, 0.72, "⟳  feedback / session loop  →  context_manager()",
        fontsize=7.8, color=C["feedback"],
        ha="center", va="center",
        fontfamily="monospace", style="italic", zorder=7)

# ─────────────────────────────────────────────
#  DATA-TYPE BADGES
# ─────────────────────────────────────────────
badges = [
    # Input lane
    (0.6, 13.45, "str | bytes",       C["input"]),
    (0.6, 12.12, "List[Token]",       C["parse"]),
    (0.6, 10.82, "IntentTag",         C["parse"]),
    (0.6,  9.52, "ContextWindow",     C["parse"]),
    (0.6,  8.22, "ReasoningPlan",     C["plan"]),
    (0.6,  6.92, "ConstrainedPlan",   C["plan"]),
    (0.6,  5.62, "PromptBundle",      C["plan"]),
    (0.6,  4.32, "TruncatedPrompt",   C["plan"]),
    # Reasoning lane
    (6.5, 13.45, "ChainOfThought",    C["reason"]),
    (6.5, 12.12, "RetrievedChunks",   C["retrieve"]),
    (6.5, 10.82, "ToolResult",        C["retrieve"]),
    (6.5,  9.52, "TaskDAG",           C["reason"]),
    (6.5,  8.22, "ScoredResponse",    C["reason"]),
    (6.5,  6.92, "FormattedText",     C["generate"]),
    (6.5,  5.62, "CitedResponse",     C["generate"]),
    (6.5,  4.32, "SafePayload",       C["safety"]),
    # Output lane
    (14.6, 13.45, "SSE Stream",       C["output"]),
    (14.6, 12.12, "CacheEntry",       C["output"]),
    (14.6, 10.82, "LogRecord",        C["output"]),
    (14.6,  9.52, "FeedbackEvent",    C["output"]),
    (14.6,  8.22, "MetricPoint",      C["output"]),
    (14.6,  6.92, "SessionRecord",    C["output"]),
    (14.6,  5.62, "QuotaCheck",       C["output"]),
    (14.6,  4.32, "HTTPResponse",     C["input"]),
]
for bx, by, bt, bc in badges:
    draw_badge(ax, bx, by, bt, bc)

# ─────────────────────────────────────────────
#  LEGEND
# ─────────────────────────────────────────────
legend_items = [
    (C["input"],    "I/O Interface"),
    (C["parse"],    "NLP Pre-processing"),
    (C["plan"],     "Planning & Assembly"),
    (C["reason"],   "Reasoning Engine"),
    (C["retrieve"], "Retrieval & Tools"),
    (C["generate"], "Generation & Format"),
    (C["safety"],   "Safety & Policy"),
    (C["output"],   "Output & Observability"),
]

lx, ly = 0.6, 2.05
ax.text(lx, ly + 0.22, "LEGEND",
        fontsize=7, color=C["muted"],
        fontfamily="monospace", fontweight="bold", zorder=10)

for i, (lc, lt) in enumerate(legend_items):
    ix = lx + i * 2.62
    ax.add_patch(FancyBboxPatch(
        (ix, ly - 0.26), 0.26, 0.26,
        boxstyle="round,pad=0,rounding_size=0.08",
        linewidth=0, facecolor=lc, alpha=0.88, zorder=10
    ))
    ax.text(ix + 0.36, ly - 0.13, lt,
            fontsize=6.6, color=C["text"],
            va="center", fontfamily="monospace", zorder=10)

# ─────────────────────────────────────────────
#  WATERMARK
# ─────────────────────────────────────────────
ax.text(21.6, 0.18,
        "pipeline_diagram.py  ·  v2.0  ·  2026-03-21",
        fontsize=6.2, color=C["border"],
        ha="right", va="center",
        fontfamily="monospace", zorder=10)

# ─────────────────────────────────────────────
#  RENDER
# ─────────────────────────────────────────────
plt.tight_layout(pad=0.2)
plt.savefig(
    "ai_pipeline_diagram.png",
    dpi=180,
    bbox_inches="tight",
    facecolor=fig.get_facecolor()
)
print("✅  Saved → ai_pipeline_diagram.png")
plt.show()
