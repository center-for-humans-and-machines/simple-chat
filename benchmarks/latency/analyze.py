"""Summarise the latency benchmark: p50/p95 per condition (CSV) plus one figure.

Reads every CSV in data/raw/ (or the files given), drops warm-up requests and writes:

- results/summary.csv   p50/p95 of each latency metric per condition, plus error rate
- results/overhead.csv  Simple Chat minus direct-to-provider p50/p95 (where both exist)
- results/latency.png / .pdf  TTFT and full completion vs concurrent sessions

Usage:
    python analyze.py
    python analyze.py data/raw/backend-*.csv data/raw/direct-*.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl
from common import RAW_DIR, RESULTS_DIR

GROUP = ["mode", "condition", "provider", "model", "stream", "concurrency", "device"]
METRICS = ["setup_s", "ttft_s", "total_s", "ttft_render_s", "total_render_s"]

# Reference palette slots 1 and 2 (a validated adjacent pair); text stays in ink colors.
STREAM_COLORS = {True: "#2a78d6", False: "#eb6834"}
INK, INK_MUTED, GRID = "#1f1f1e", "#6b6a64", "#e4e3dd"


def load(paths: list[Path]) -> pl.DataFrame:
    frames = [pl.read_csv(p, infer_schema_length=None) for p in paths]
    df = pl.concat(frames, how="diagonal_relaxed")
    for col in ["device", *METRICS]:
        if col not in df.columns:
            df = df.with_columns(pl.lit(None).alias(col))
    return df.with_columns(
        pl.col("device").fill_null("none"),
        pl.col("stream").cast(pl.Utf8).str.to_lowercase().eq("true"),
        pl.col("warmup").cast(pl.Utf8).str.to_lowercase().eq("true"),
        *[pl.col(m).cast(pl.Float64) for m in METRICS],
    )


def summarise(df: pl.DataFrame) -> pl.DataFrame:
    measured = df.filter(~pl.col("warmup"))
    aggs = [
        pl.len().alias("n_requests"),
        (pl.col("status") != "ok").mean().round(4).alias("error_rate"),
    ]
    ok = pl.col("status") == "ok"
    for m in METRICS:
        aggs += [
            pl.col(m).filter(ok).quantile(0.5, "linear").round(3).alias(f"{m}_p50"),
            pl.col(m).filter(ok).quantile(0.95, "linear").round(3).alias(f"{m}_p95"),
        ]
    summary = measured.group_by(GROUP).agg(aggs).sort(GROUP)
    # Drop metric columns that no mode produced.
    empty = [c for c in summary.columns if summary[c].null_count() == summary.height]
    return summary.drop(empty)


def overhead(summary: pl.DataFrame) -> pl.DataFrame:
    keys = ["condition", "provider", "stream", "concurrency"]
    cols = [c for c in ("ttft_s_p50", "ttft_s_p95", "total_s_p50", "total_s_p95") if c in summary.columns]
    backend = summary.filter(pl.col("mode") == "backend").select(keys + cols)
    direct = summary.filter(pl.col("mode") == "direct").select(keys + cols)
    if backend.is_empty() or direct.is_empty():
        return pl.DataFrame()
    joined = backend.join(direct, on=keys, suffix="_direct")
    return joined.select(
        keys + [(pl.col(c) - pl.col(f"{c}_direct")).round(3).alias(f"overhead_{c}") for c in cols]
    ).sort(keys)


def plot(summary: pl.DataFrame, out_stem: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    data = summary.filter(pl.col("mode").is_in(["backend", "direct"]))
    if data.is_empty():
        print("no backend/direct rows to plot")
        return
    conditions = data["condition"].unique(maintain_order=True).sort().to_list()
    levels = sorted(data["concurrency"].unique().to_list())
    rows = [("ttft_s", "Time to first token (s)"), ("total_s", "Full completion (s)")]

    plt.rcParams.update({
        "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": INK_MUTED, "ytick.color": INK_MUTED, "axes.titlesize": 10,
    })
    fig, axes = plt.subplots(len(rows), len(conditions), figsize=(3.0 * len(conditions), 5.2),
                             sharex=True, sharey="row", squeeze=False)
    x_of = {lvl: i for i, lvl in enumerate(levels)}

    for col, cond in enumerate(conditions):
        for row, (metric, label) in enumerate(rows):
            ax = axes[row][col]
            for (mode, stream), part in data.filter(pl.col("condition") == cond).group_by(
                    ["mode", "stream"], maintain_order=True):
                part = part.sort("concurrency")
                xs = [x_of[c] for c in part["concurrency"]]
                p50, p95 = part[f"{metric}_p50"].to_list(), part[f"{metric}_p95"].to_list()
                if all(v is None for v in p50):
                    continue
                color = STREAM_COLORS[stream]
                if mode == "backend":
                    # p50 line; the whisker reaches up to p95.
                    ax.errorbar(xs, p50, yerr=[[0] * len(p50), [b - a for a, b in zip(p50, p95)]],
                                color=color, lw=2, marker="o", ms=6, capsize=3, elinewidth=1.2,
                                markeredgecolor="white", markeredgewidth=1.5, zorder=3)
                else:
                    ax.plot(xs, p50, color=color, lw=1.5, ls="--", marker="o", ms=4,
                            mfc="white", zorder=2)
            ax.set_xticks(range(len(levels)), [str(lvl) for lvl in levels])
            ax.set_ylim(bottom=0)
            ax.grid(axis="y", color=GRID, lw=0.8)
            ax.set_axisbelow(True)
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
            if row == 0:
                ax.set_title(cond)
            if col == 0:
                ax.set_ylabel(label)
            if row == len(rows) - 1:
                ax.set_xlabel("Concurrent sessions")

    handles = [
        Line2D([], [], color=STREAM_COLORS[True], lw=2, marker="o", label="Simple Chat, streaming"),
        Line2D([], [], color=STREAM_COLORS[False], lw=2, marker="o", label="Simple Chat, non-streaming"),
        Line2D([], [], color=INK_MUTED, lw=1.5, ls="--", marker="o", mfc="white",
               label="Direct to provider (p50)"),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, 1.0))
    fig.text(0.5, -0.01, "Points: median (p50). Whiskers: up to p95.", ha="center",
             color=INK_MUTED, fontsize=8)
    fig.tight_layout(rect=(0, 0.01, 1, 0.94))
    for ext in ("png", "pdf"):
        fig.savefig(out_stem.with_suffix(f".{ext}"), dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="*", type=Path, help="raw CSVs (default: data/raw/*.csv)")
    parser.add_argument("--out-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()

    paths = args.files or sorted(RAW_DIR.glob("*.csv"))
    if not paths:
        raise SystemExit(f"no CSV files found in {RAW_DIR}")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    df = load(paths)
    summary = summarise(df)
    summary.write_csv(args.out_dir / "summary.csv")
    print(f"summary: {summary.height} conditions -> {args.out_dir / 'summary.csv'}")

    over = overhead(summary)
    if not over.is_empty():
        over.write_csv(args.out_dir / "overhead.csv")
        print(f"overhead -> {args.out_dir / 'overhead.csv'}")

    plot(summary, args.out_dir / "latency")
    print(f"figure -> {args.out_dir / 'latency.png'}")


if __name__ == "__main__":
    main()
