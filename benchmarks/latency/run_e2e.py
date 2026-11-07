"""End-to-end latency benchmark for Simple Chat in a browser.

Loads the Simple Chat frontend inside an iframe (as in Qualtrics or oTree), types one
prompt and records:

- setup_s: from loading the host page until the chat is ready for input
- ttft_s / total_s: first token / end of reply as received over the WebSocket
- ttft_render_s / total_render_s: first assistant character / last character on
  screen. The frontend types replies out at 20 ms per character, so on-screen
  completion is mostly set by that animation, not by the network.

Devices: desktop Chrome (installed Google Chrome) and an emulated iPhone Safari
(WebKit) by default; an emulated Android Chrome (Chromium) is available with
--device. Emulation reproduces the viewport, user agent and touch input, not real
phone hardware or networks.

Like run_backend.py, it runs blocks of one condition x streaming mode x number of
concurrent sessions (1, 5, 20 by default): that many browser sessions, each a
simulated participant, chat at the same time.

Usage:
    python run_e2e.py --config conditions.toml --trials 30
"""

# CLI output, deterministic shuffling, and recording individual trial failures
# are intentional for this benchmark.
# ruff: noqa: T201, S311, BLE001

# Flat benchmark scripts: each measurement step keeps its parameters and
# intermediate timings together, and both runners share the same CSV schema.
# pylint: disable=too-many-arguments,too-many-positional-arguments
# pylint: disable=too-many-locals,duplicate-code

from __future__ import annotations

import argparse
import asyncio
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode

import common
from playwright.async_api import async_playwright

FIELDS = [
    "run_id",
    "mode",
    "block",
    "condition",
    "provider",
    "model",
    "stream",
    "concurrency",
    "device",
    "browser",
    "rep",
    "prompt_id",
    "worker",
    "warmup",
    "started_at",
    "setup_s",
    "ttfe_s",
    "ttft_s",
    "total_s",
    "ttft_render_s",
    "total_render_s",
    "response_chars",
    "status",
    "error",
    "target",
    "client_host",
]

# name -> (browser engine, Playwright device descriptor or None, launch channel)
DEVICES = {
    "desktop-chrome": ("chromium", None, "chrome"),
    "android-chrome": ("chromium", "Pixel 7", None),
    "iphone-safari": ("webkit", "iPhone 14", None),
}

# Runs inside the chat iframe: notes when the prompt is submitted and when the newest
# assistant bubble gets its first and its last character.
OBSERVER_JS = """
() => {
  const labels = () => [...document.querySelectorAll('span')]
    .filter(s => s.textContent === 'Assistant:');
  const b = window.__bench = {base: labels().length, t0: null, first: null, last: null, len: 0};
  document.addEventListener('submit', () => { b.t0 = performance.now(); }, true);
  new MutationObserver(() => {
    const ls = labels();
    if (ls.length <= b.base) return;
    const label = ls[ls.length - 1];
    const len = label.parentElement.textContent.slice(label.textContent.length).trim().length;
    if (len > 0 && b.first === null) b.first = performance.now();
    if (len !== b.len) { b.len = len; b.last = performance.now(); }
  }).observe(document.body, {subtree: true, childList: true, characterData: true});
}
"""


def parse_socketio_frame(payload) -> tuple[str, dict] | None:
    """Socket.IO event frames look like 42["event", {...}]."""
    if not isinstance(payload, str) or not payload.startswith("42"):
        return None
    try:
        event, *rest = json.loads(payload[2:])
    except (ValueError, TypeError):
        return None
    return event, (rest[0] if rest else {})


async def one_trial(
    browser,
    device_descriptor,
    config,
    cond,
    prompt,
    stream,
    participant_id,
    timeout,
    render_idle,
):
    context = await browser.new_context(
        **(device_descriptor or {"viewport": {"width": 1280, "height": 800}})
    )
    page = await context.new_page()
    frames: list[tuple[float, str, dict]] = []

    def on_websocket(ws):
        def on_frame(payload):
            parsed = parse_socketio_frame(payload)
            if parsed:
                frames.append((time.perf_counter(), *parsed))

        ws.on("framereceived", on_frame)

    page.on("websocket", on_websocket)

    async def wait_for(predicate, what, deadline):
        while time.perf_counter() < deadline:
            for item in frames:
                if predicate(item):
                    return item
            await asyncio.sleep(0.005)
        raise TimeoutError(f"timed out waiting for {what}")

    try:
        query = urlencode(
            {
                "pid": cond.pid,
                "model": cond.model,
                "participant_id": participant_id,
                "experiment_id": "latency-benchmark",
                "stream": "true" if stream else "false",
            }
        )
        src = f"{config.frontend_url.rstrip('/')}/?{query}"
        deadline = time.perf_counter() + timeout

        t_setup0 = time.perf_counter()
        await page.set_content(
            f'<iframe id="chat" src="{src}" style="width:100%;height:95vh;border:0"></iframe>'
        )
        frame = await (await page.wait_for_selector("#chat")).content_frame()
        await frame.wait_for_load_state("load")
        # Ready once the backend has returned the system message for this session.
        await wait_for(
            lambda f: f[1] == "message_to_client" and f[2].get("role") == "system",
            "session setup",
            deadline,
        )
        send = frame.get_by_role("button", name="Send")
        await send.wait_for(state="visible")
        setup_s = time.perf_counter() - t_setup0

        await frame.evaluate(OBSERVER_JS)
        await frame.get_by_role("textbox").fill(prompt)
        n_before = len(frames)
        t0 = time.perf_counter()
        await send.click()

        def assistant_chunk(f):
            return (
                f[1] == "message_to_client"
                and f[2].get("type") in ("message", "stream")
                and f[2].get("data", {}).get("role") == "assistant"
            )

        end = await wait_for(lambda f: f[1] == "message_end", "message_end", deadline)
        chunks = [f for f in frames[n_before:] if assistant_chunk(f)]
        first_event = chunks[0][0] if chunks else None
        first_token = next((f[0] for f in chunks if f[2]["data"].get("content")), None)

        # Wait until the typewriter animation has finished (no change for render_idle s).
        while time.perf_counter() < deadline:
            b = await frame.evaluate("window.__bench")
            if (
                b["last"] is not None
                and (await frame.evaluate("performance.now()") - b["last"]) > render_idle * 1000
            ):
                break
            await asyncio.sleep(0.1)
        b = await frame.evaluate("window.__bench")

        status = end[2].get("status", "ok")
        return {
            "setup_s": setup_s,
            "ttfe_s": first_event - t0 if first_event else None,
            "ttft_s": first_token - t0 if first_token else None,
            "total_s": end[0] - t0,
            "ttft_render_s": ((b["first"] - b["t0"]) / 1000 if b["first"] and b["t0"] else None),
            "total_render_s": ((b["last"] - b["t0"]) / 1000 if b["last"] and b["t0"] else None),
            "response_chars": sum(len(f[2]["data"].get("content") or "") for f in chunks),
            "status": status,
            "error": "" if status == "ok" else "backend reported an error",
        }
    finally:
        await context.close()


@dataclass
class Job:
    rep: int
    prompt: dict
    warmup: bool


# --------------------------------------------------------------------------------------
# Blocks: one condition x stream mode x concurrency level, on one device
# --------------------------------------------------------------------------------------


async def run_block(
    args,
    config,
    browser,
    device,
    descriptor,
    cond,
    stream,
    concurrency,
    prompts,
    writer,
    run_id,
    block,
):
    """Run one block with `concurrency` browser sessions open at the same time.

    Each worker is one simulated participant: it opens the chat in a fresh browser
    context, sends one prompt and waits until the reply has been typed out on screen,
    then starts the next trial. As in run_backend.py, every worker begins with one
    warm-up trial (flagged, excluded from the analysis), then the workers share the
    measured trials in a shuffled order.
    """
    jobs: asyncio.Queue[Job] = asyncio.Queue()
    for i in range(concurrency):
        jobs.put_nowait(Job(rep=-1, prompt=prompts[i % len(prompts)], warmup=True))
    measured = [
        Job(rep, p, False) for rep, p in common.prompt_schedule(prompts, args.reps, args.trials)
    ]
    random.Random(f"{args.seed}-{device}-{block}").shuffle(measured)
    for job in measured:
        jobs.put_nowait(job)
    done = 0
    total_jobs = jobs.qsize()
    engine = DEVICES[device][0]

    async def worker(worker_id: int):
        nonlocal done
        while True:
            try:
                job = jobs.get_nowait()
            except asyncio.QueueEmpty:
                return
            row = {
                "run_id": run_id,
                "mode": "e2e",
                "block": block,
                "condition": cond.name,
                "provider": cond.provider,
                "model": cond.model,
                "stream": stream,
                "concurrency": concurrency,
                "device": device,
                "browser": f"{engine} {browser.version}",
                "rep": job.rep,
                "prompt_id": job.prompt["id"],
                "worker": worker_id,
                "warmup": job.warmup,
                "started_at": common.utc_now(),
                "target": config.frontend_url,
                "client_host": common.client_host(),
            }
            participant_id = (
                f"{run_id}-{device}-b{block}-w{worker_id}-{job.prompt['id']}-r{job.rep}"
            )
            try:
                result = await one_trial(
                    browser,
                    descriptor,
                    config,
                    cond,
                    job.prompt["content"],
                    stream,
                    participant_id,
                    args.timeout,
                    args.render_idle,
                )
            # Keep going; failures are part of the data.
            # pylint: disable-next=broad-exception-caught
            except Exception as e:
                result = {
                    "status": "error",
                    "error": f"{type(e).__name__}: {e}"[:300],
                }
            writer.write({**row, **result})
            done += 1
            if result["status"] != "ok" or args.verbose:
                print(
                    f"    [{done}/{total_jobs}] {job.prompt['id']}: "
                    f"{result['status']} {result.get('error', '')}"
                )

    await asyncio.gather(*(worker(i) for i in range(concurrency)))


async def main_async(args) -> None:
    config = common.load_config(args.config)
    conditions = common.select_conditions(config, args.conditions)
    prompts = common.load_prompts(args.prompts)
    if args.prompt_ids:
        prompts = [p for p in prompts if p["id"] in args.prompt_ids]
    streams = common.parse_stream_modes(args.stream)

    run_id = common.new_run_id("e2e")
    out = Path(args.out) if args.out else common.RAW_DIR / f"{run_id}.csv"
    writer = common.RowWriter(out, FIELDS)
    blocks = [(c, s, n) for c in conditions for s in streams for n in args.concurrency]
    per_block = len(common.prompt_schedule(prompts, args.reps, args.trials))
    n_trials = len(args.device) * sum(n + per_block for _, _, n in blocks)
    print(
        f"run {run_id}: {len(args.device)} devices x {len(blocks)} blocks, "
        f"{n_trials} trials -> {out}"
    )

    async with async_playwright() as pw:
        try:
            for device in args.device:
                engine, descriptor_name, channel = DEVICES[device]
                launch: dict[str, bool | str] = {"headless": not args.headed}
                if channel:
                    launch["channel"] = channel
                browser = await getattr(pw, engine).launch(**launch)
                descriptor = pw.devices[descriptor_name] if descriptor_name else None
                print(f"  device {device} ({engine} {browser.version})")

                # Shuffle the block order per device so time-of-day effects at the
                # provider do not line up with one condition.
                order = list(blocks)
                random.Random(f"{args.seed}-{device}").shuffle(order)
                for i, (cond, stream, concurrency) in enumerate(order):
                    print(
                        f"  {device} block {i + 1}/{len(order)}: {cond.name} "
                        f"stream={'on' if stream else 'off'} concurrency={concurrency}"
                    )
                    await run_block(
                        args,
                        config,
                        browser,
                        device,
                        descriptor,
                        cond,
                        stream,
                        concurrency,
                        prompts,
                        writer,
                        run_id,
                        i,
                    )
                    if args.pause and i < len(order) - 1:
                        await asyncio.sleep(args.pause)
                await browser.close()
        finally:
            writer.close()
    print(f"done -> {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default="conditions.toml")
    parser.add_argument("--prompts", default="prompts.jsonl")
    parser.add_argument("--prompt-ids", nargs="*", help="subset of prompt IDs (default: all)")
    parser.add_argument("--conditions", nargs="*", help="subset of condition names (default: all)")
    parser.add_argument(
        "--device",
        nargs="+",
        default=["desktop-chrome", "iphone-safari"],
        choices=sorted(DEVICES),
        help="browsers to run (default: desktop Chrome and emulated iPhone Safari)",
    )
    parser.add_argument("--stream", nargs="+", default=["on", "off"], help="on and/or off")
    parser.add_argument(
        "--concurrency",
        nargs="+",
        type=int,
        default=[1, 5, 20],
        help="browser sessions open at the same time",
    )
    parser.add_argument(
        "--reps", type=int, default=2, help="repetitions of the prompt set per block"
    )
    parser.add_argument(
        "--trials",
        type=int,
        help="exact number of measured trials per block, cycling through the "
        "prompts (overrides --reps)",
    )
    parser.add_argument("--timeout", type=float, default=180, help="seconds per trial")
    parser.add_argument(
        "--render-idle",
        type=float,
        default=1.0,
        help="seconds without on-screen change that count as finished",
    )
    parser.add_argument("--pause", type=float, default=5, help="seconds between blocks")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--headed", action="store_true", help="show the browser window")
    parser.add_argument("--out", help="output CSV (default: data/raw/<run_id>.csv)")
    parser.add_argument("--verbose", action="store_true")
    asyncio.run(main_async(parser.parse_args()))


if __name__ == "__main__":
    main()
