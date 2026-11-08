"""Summarise the latency benchmark: p50/p95 per condition (CSV) plus figures.

Reads every CSV in data/raw/ (or the files given), drops warm-up requests and writes:

- results/summary.csv   p50/p95 of each latency metric per condition, plus error rate
- results/overhead.csv  Simple Chat backend minus direct-to-provider p50/p95
- results/overhead-e2e.csv  on-screen times in the browser minus direct-to-provider p50/p95
- results/latency.png / .pdf  backend TTFT and full completion vs concurrent sessions
- results/latency-e2e.png / .pdf  first and last character on screen in the browser,
  next to the direct-to-provider baseline
- results/latency-paper.pdf / .png  figure for the paper (journal style)

Simple Chat runs are compared only with direct-to-provider runs from the same day
(`date`), so that provider load is similar.

Usage:
    python analyze.py
    python analyze.py data/raw/backend-*.csv data/raw/direct-*.csv
"""

# This command-line script reports generated paths on stdout.
# ruff: noqa: T201

# _grid() lays out one figure step by step and takes its drawing callbacks.
# pylint: disable=too-many-locals,too-many-arguments,too-many-positional-arguments

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import transforms
import polars as pl
from common import RAW_DIR, RESULTS_DIR
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator

GROUP = ["mode", "date", "condition", "provider", "model", "stream", "concurrency", "device"]
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
        pl.col("started_at").cast(pl.Utf8).str.slice(0, 10).alias("date"),
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
    keys = ["date", "condition", "provider", "stream", "concurrency"]
    cols = [
        c
        for c in ("ttft_s_p50", "ttft_s_p95", "total_s_p50", "total_s_p95")
        if c in summary.columns
    ]
    backend = summary.filter(pl.col("mode") == "backend").select(keys + cols)
    direct = summary.filter(pl.col("mode") == "direct").select(keys + cols)
    if backend.is_empty() or direct.is_empty():
        return pl.DataFrame()
    joined = backend.join(direct, on=keys, suffix="_direct")
    return joined.select(
        keys + [(pl.col(c) - pl.col(f"{c}_direct")).round(3).alias(f"overhead_{c}") for c in cols]
    ).sort(keys)


def overhead_e2e(summary: pl.DataFrame) -> pl.DataFrame:
    """On-screen times minus the same-day direct-to-provider times.

    First character on screen is compared with the direct time to first token, and the
    full reply on screen with the direct full completion.
    """
    keys = ["date", "condition", "provider", "stream", "concurrency"]
    pairs = {
        "first_char": ("ttft_render_s", "ttft_s"),
        "full_reply": ("total_render_s", "total_s"),
    }
    if "total_render_s_p50" not in summary.columns:
        return pl.DataFrame()
    e2e = summary.filter(pl.col("mode") == "e2e")
    direct = summary.filter(pl.col("mode") == "direct").select(
        keys + [f"{d}_{q}" for _, d in pairs.values() for q in ("p50", "p95")]
    )
    if e2e.is_empty() or direct.is_empty():
        return pl.DataFrame()
    joined = e2e.join(direct, on=keys, suffix="_direct")
    return joined.select(
        keys
        + ["device"]
        + [
            (pl.col(f"{screen}_{q}") - pl.col(f"{d}_{q}_direct"))
            .round(3)
            .alias(f"overhead_{n}_{q}")
            for n, (screen, d) in pairs.items()
            for q in ("p50", "p95")
        ]
    ).sort(keys + ["device"])


def _same_day_direct(summary: pl.DataFrame, mode: str) -> pl.DataFrame:
    """Rows of `mode` plus the direct-to-provider rows from the same days."""
    rows = summary.filter(pl.col("mode") == mode)
    days = rows["date"].unique().to_list()
    direct = summary.filter((pl.col("mode") == "direct") & pl.col("date").is_in(days))
    return pl.concat([rows, direct], how="diagonal_relaxed")


# Line style per device in the end-to-end figure; color still encodes streaming.
DEVICE_STYLES = {
    "desktop-chrome": ("-", "o", "Desktop Chrome"),
    "android-chrome": ("--", "s", "Android Chrome (emulated)"),
    "iphone-safari": (":", "^", "iPhone Safari (emulated)"),
}


def _style_rc() -> None:
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.edgecolor": GRID,
            "axes.labelcolor": INK,
            "text.color": INK,
            "xtick.color": INK_MUTED,
            "ytick.color": INK_MUTED,
            "axes.titlesize": 10,
        }
    )


def _p50_with_p95(ax, xs, p50, p95, **style) -> None:
    """Median line; the whisker reaches up to p95."""
    ax.errorbar(
        xs,
        p50,
        yerr=[[0] * len(p50), [b - a for a, b in zip(p50, p95, strict=True)]],
        capsize=3,
        elinewidth=1.2,
        markeredgecolor="white",
        markeredgewidth=1.2,
        zorder=3,
        **style,
    )


def _grid(data, rows, series, draw, handles, out_stem: Path, note: str = "") -> None:
    """One column per condition, one row per metric, one line per series."""
    matplotlib.use("Agg")
    _style_rc()
    conditions = sorted(set(data["condition"].to_list()))
    levels = sorted(set(data["concurrency"].to_list()))
    x_of = {lvl: i for i, lvl in enumerate(levels)}
    fig, axes = plt.subplots(
        len(rows),
        len(conditions),
        figsize=(3.0 * len(conditions), 5.2),
        sharex=True,
        sharey="row",
        squeeze=False,
    )
    for col, cond in enumerate(conditions):
        for row, (metric, label) in enumerate(rows):
            ax = axes[row][col]
            for key, part in data.filter(pl.col("condition") == cond).group_by(
                series, maintain_order=True
            ):
                part = part.sort("concurrency")
                p50 = part[f"{metric}_p50"].to_list()
                if all(v is None for v in p50):
                    continue
                xs = [x_of[c] for c in part["concurrency"]]
                draw(ax, key, xs, p50, part[f"{metric}_p95"].to_list())
            ax.set_xticks(range(len(levels)), [str(lvl) for lvl in levels])
            # Shared y-axis per row: fit the largest p95 in the row so no whisker is cut.
            row_cols = [c for c in (f"{metric}_p95", f"{metric}_p50") if c in data.columns]
            row_max = max(data.select(pl.max_horizontal(row_cols).max()).item() or 0, 0.1)
            ax.set_ylim(0, row_max * 1.08)
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
    fig.legend(
        handles=handles,
        loc="upper center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.5, 1.0),
    )
    fig.text(
        0.5,
        -0.01,
        "Points: median (p50). Whiskers: up to p95." + (f" {note}" if note else ""),
        ha="center",
        color=INK_MUTED,
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.01, 1, 0.92))
    for ext in ("png", "pdf"):
        fig.savefig(out_stem.with_suffix(f".{ext}"), dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot(summary: pl.DataFrame, out_stem: Path) -> None:
    """Backend and direct-to-provider times (what the Simple Chat server sees)."""
    data = _same_day_direct(summary, "backend")
    if data.filter(pl.col("mode") == "backend").is_empty():
        print("no backend rows to plot")
        return

    def draw(ax, key, xs, p50, p95):
        mode, stream = key
        color = STREAM_COLORS[stream]
        if mode == "backend":
            _p50_with_p95(ax, xs, p50, p95, color=color, lw=2, marker="o", ms=6)
        else:
            ax.plot(
                xs,
                p50,
                color=color,
                lw=1.5,
                ls="--",
                marker="o",
                ms=4,
                mfc="white",
                zorder=2,
            )

    handles = [
        Line2D(
            [],
            [],
            color=STREAM_COLORS[True],
            lw=2,
            marker="o",
            label="Simple Chat, streaming",
        ),
        Line2D(
            [],
            [],
            color=STREAM_COLORS[False],
            lw=2,
            marker="o",
            label="Simple Chat, non-streaming",
        ),
        Line2D(
            [],
            [],
            color=INK_MUTED,
            lw=1.5,
            ls="--",
            marker="o",
            mfc="white",
            label="Direct to provider (p50)",
        ),
    ]
    rows = [("ttft_s", "Time to first token (s)"), ("total_s", "Full completion (s)")]
    _grid(data, rows, ["mode", "stream"], draw, handles, out_stem)


def plot_e2e(summary: pl.DataFrame, out_stem: Path) -> None:
    """On-screen times in the browser (what participants see)."""
    if "total_render_s_p50" not in summary.columns:
        print("no e2e rows to plot")
        return
    # The direct baseline has no screen: plot its time to first token and full
    # completion in the first-character and full-reply rows.
    data = _same_day_direct(summary, "e2e").with_columns(
        *[
            pl.when(pl.col("mode") == "direct")
            .then(pl.col(f"{d}_{q}"))
            .otherwise(pl.col(f"{screen}_{q}"))
            .alias(f"{screen}_{q}")
            for screen, d in (("ttft_render_s", "ttft_s"), ("total_render_s", "total_s"))
            for q in ("p50", "p95")
        ]
    )
    if data.filter(pl.col("mode") == "e2e").is_empty():
        print("no e2e rows to plot")
        return
    devices = [d for d in DEVICE_STYLES if d in set(data["device"].to_list())]
    # Nudge devices apart on the x-axis so their whiskers do not overlap.
    nudge = {d: (i - (len(devices) - 1) / 2) * 0.08 for i, d in enumerate(devices)}

    def draw(ax, key, xs, p50, p95):
        mode, device, stream = key
        if mode == "direct":
            ax.plot(
                xs,
                p50,
                color=STREAM_COLORS[stream],
                lw=1.5,
                ls="--",
                marker="o",
                ms=4,
                mfc="white",
                zorder=2,
            )
            return
        ls, marker, _ = DEVICE_STYLES.get(device, ("-", "o", device))
        xs = [x + nudge.get(device, 0) for x in xs]
        _p50_with_p95(
            ax,
            xs,
            p50,
            p95,
            color=STREAM_COLORS[stream],
            lw=1.6,
            ls=ls,
            marker=marker,
            ms=5,
        )

    handles = [
        Line2D([], [], color=STREAM_COLORS[True], lw=2, label="Streaming"),
        Line2D([], [], color=STREAM_COLORS[False], lw=2, label="Non-streaming"),
    ] + [
        Line2D(
            [],
            [],
            color=INK_MUTED,
            lw=1.6,
            ls=DEVICE_STYLES[d][0],
            marker=DEVICE_STYLES[d][1],
            label=DEVICE_STYLES[d][2],
        )
        for d in devices
    ]
    if not data.filter(pl.col("mode") == "direct").is_empty():
        handles.append(
            Line2D(
                [],
                [],
                color=INK_MUTED,
                lw=1.5,
                ls="--",
                marker="o",
                mfc="white",
                label="Direct to provider (p50)",
            )
        )
    rows = [
        ("ttft_render_s", "First character on screen (s)"),
        ("total_render_s", "Full reply on screen (s)"),
    ]
    note = "Direct to provider: time to first token and full completion, no display."
    _grid(data, rows, ["mode", "device", "stream"], draw, handles, out_stem, note)


# Okabe-Ito blue, from the colorblind-safe set common in journals.
PAPER_BLUE = "#0072B2"
PAPER_GREY = "#999999"
PAPER_MODELS = [
    ("openai-gpt-5.1", "GPT-5.1, OpenAI"),
    ("azure-gpt-5.1", "GPT-5.1, Azure"),
    ("together-deepseek-v4.1-flash", "DeepSeek-V4.1-Flash, Together AI"),
]
# Drawn at print size so the manuscript includes it unscaled; saved cropped to its content.
PAPER_WIDTH_MM, PAPER_HEIGHT_MM = 140, 72
PAPER_FONT_PT = 9


def _paper_rows(df: pl.DataFrame) -> tuple[list[dict], str] | None:
    """Per model and streaming mode: quartiles of the time to first visible text,
    on screen and direct, from the latest day that has both an end-to-end run and a
    direct baseline."""
    ok = df.filter(~pl.col("warmup") & (pl.col("status") == "ok"))
    days = set(ok.filter(pl.col("mode") == "e2e")["date"].to_list()) & set(
        ok.filter(pl.col("mode") == "direct")["date"].to_list()
    )
    if not days:
        return None
    day = max(days)
    ok = ok.filter(pl.col("date") == day)

    def quartiles(s: pl.Series) -> tuple[float, float, float]:
        return (s.quantile(0.25, "linear"), s.median(), s.quantile(0.75, "linear"))

    rows = []
    for cond, label in PAPER_MODELS:
        for stream in (True, False):
            sel = (pl.col("condition") == cond) & (pl.col("stream") == stream)
            e2e = ok.filter(sel & (pl.col("mode") == "e2e"))
            direct = ok.filter(sel & (pl.col("mode") == "direct"))
            if e2e.is_empty() or direct.is_empty():
                continue
            rows.append(
                {
                    "model": label,
                    "stream": stream,
                    # Without streaming the first token arrives with the full response.
                    "direct": quartiles(direct["ttft_s"]),
                    "screen": quartiles(e2e["ttft_render_s"]),
                }
            )
    return rows, day


def plot_paper(df: pl.DataFrame, out_stem: Path) -> None:
    """Figure for the paper, in journal style (Arial 9 pt, 0.5 pt lines): time until
    the first text is visible, Simple Chat on screen vs direct API, median and
    interquartile range, pooled over devices and concurrency."""
    found = _paper_rows(df)
    if not found or not found[0]:
        print("no same-day e2e and direct rows for the paper figure")
        return
    rows, day = found
    matplotlib.use("Agg")
    style = {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": PAPER_FONT_PT,
        "legend.fontsize": PAPER_FONT_PT,
        "text.color": "black",
        "axes.labelcolor": "black",
        "axes.edgecolor": "black",
        "xtick.color": "black",
        "ytick.color": "black",
        "axes.linewidth": 0.5,
        "xtick.major.width": 0.5,
        "xtick.major.size": 2,
        "ytick.major.size": 0,
        "xtick.direction": "out",
        "pdf.fonttype": 42,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
    }
    with plt.rc_context(style):
        mm = 1 / 25.4
        fig, ax = plt.subplots(figsize=(PAPER_WIDTH_MM * mm, PAPER_HEIGHT_MM * mm))
        pos, labels, groups = [], [], []
        y = 0.0
        for _, label in PAPER_MODELS:
            groups.append((y - 0.6, label))
            for stream in (True, False):
                pos.append(y)
                labels.append("Streaming" if stream else "Non-streaming")
                y += 1.0
            y += 0.7

        series = (
            ("direct", PAPER_GREY, -0.16, "white", "Direct API"),
            ("screen", PAPER_BLUE, 0.16, PAPER_BLUE, "Simple Chat, on screen"),
        )
        for r, yy in zip(rows, pos):
            for key, color, dy, face, _ in series:
                lo, med, hi = r[key]
                ax.plot([lo, hi], [yy + dy] * 2, color=color, lw=0.8, solid_capstyle="butt")
                ax.plot(med, yy + dy, marker="o", ms=3.5, mfc=face, mec=color, mew=0.7)

        ax.set_xlim(0, max(r[k][2] for r in rows for k in ("direct", "screen")) * 1.05)
        ax.set_xlabel("Time until first text is visible (s)")
        ax.set_yticks(pos, labels)
        ax.xaxis.set_major_locator(MultipleLocator(1))
        ax.set_ylim(y - 0.95, -1.1)
        ax.tick_params(axis="y", length=0)
        # Model names right-aligned with the tick labels, above their two rows.
        name_transform = transforms.offset_copy(
            ax.get_yaxis_transform(), fig=fig, x=-plt.rcParams["ytick.major.pad"], units="points"
        )
        for gy, label in groups:
            ax.text(0, gy, label, transform=name_transform, ha="right", va="center", weight="bold")
        ax.legend(
            handles=[
                Line2D([], [], color=c, lw=0.8, marker="o", ms=3.5, mfc=f, mew=0.7, label=lab)
                for _, c, _, f, lab in series
            ],
            loc="lower right",
            bbox_to_anchor=(1.0, 1.0),
            ncol=2,
            frameon=False,
            handlelength=1.6,
            columnspacing=1.2,
            borderaxespad=0.2,
        )
        for ext in ("pdf", "png"):
            fig.savefig(
                out_stem.with_suffix(f".{ext}"), dpi=600, bbox_inches="tight", pad_inches=0.01
            )
        plt.close(fig)
    print(f"paper figure ({day}) -> {out_stem.with_suffix('.pdf')}")


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

    over_e2e = overhead_e2e(summary)
    if not over_e2e.is_empty():
        over_e2e.write_csv(args.out_dir / "overhead-e2e.csv")
        print(f"overhead -> {args.out_dir / 'overhead-e2e.csv'}")

    plot(summary, args.out_dir / "latency")
    print(f"figure -> {args.out_dir / 'latency.png'}")
    plot_e2e(summary, args.out_dir / "latency-e2e")
    print(f"figure -> {args.out_dir / 'latency-e2e.png'}")
    plot_paper(df, args.out_dir / "latency-paper")


if __name__ == "__main__":
    main()
