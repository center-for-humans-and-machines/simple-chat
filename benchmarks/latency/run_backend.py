"""Backend latency benchmark for Simple Chat.

Drives the Simple Chat backend over Socket.IO (exactly like the frontend does) with
N concurrent sessions and records, per request, the time to first token and the time
to the full completion. With `--mode direct` the same prompts go straight to the
provider API instead, as a baseline for Simple Chat's own overhead.

Every measured request uses a fresh chat session with a single user prompt, so the
conversation history and token limit do not change between requests.

Usage:
    python run_backend.py --config conditions.toml
    python run_backend.py --config conditions.toml --mode direct --env-file ../../.env
"""

# CLI output, deterministic shuffling, and recording individual request failures
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
import os
import random
import time
import traceback
from dataclasses import dataclass
from pathlib import Path

import common
import socketio
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI, AsyncOpenAI

FIELDS = [
    "run_id",
    "mode",
    "block",
    "condition",
    "provider",
    "model",
    "stream",
    "concurrency",
    "rep",
    "prompt_id",
    "worker",
    "warmup",
    "started_at",
    "setup_s",
    "ttfe_s",
    "ttft_s",
    "total_s",
    "n_chunks",
    "response_chars",
    "status",
    "error",
    "target",
    "client_host",
]


class RequestError(Exception):
    pass


@dataclass
class Job:
    rep: int
    prompt: dict
    warmup: bool


# --------------------------------------------------------------------------------------
# One request through Simple Chat (Socket.IO)
# --------------------------------------------------------------------------------------


async def simple_chat_request(
    config: common.Config,
    cond: common.Condition,
    prompt: str,
    stream: bool,
    participant_id: str,
    timeout: float,
) -> dict:
    """Open a session, send one prompt, and time the assistant reply."""
    events: asyncio.Queue = asyncio.Queue()
    sio = socketio.AsyncClient(reconnection=False)

    @sio.on("*")
    async def _any(event, data=None):
        events.put_nowait((time.perf_counter(), event, data))

    deadline = time.perf_counter() + timeout

    async def next_event():
        remaining = deadline - time.perf_counter()
        if remaining <= 0:
            raise RequestError("timeout")
        try:
            return await asyncio.wait_for(events.get(), remaining)
        except TimeoutError as e:
            raise RequestError("timeout") from e

    t_setup0 = time.perf_counter()
    try:
        await sio.connect(
            config.backend_url,
            socketio_path="/ws",
            transports=["websocket"],
            wait_timeout=timeout,
        )

        # 1. The server assigns a session ID on connect.
        while True:
            _, event, data = await next_event()
            if event == "session_id":
                session_id = data["session_id"]
                break

        # 2. Start the conversation, as the frontend does with the iframe's query parameters.
        await sio.emit(
            "initial_message_to_server",
            {
                "session_id": session_id,
                "data": {
                    "pid": cond.pid,
                    "model": cond.model,
                    "participant_id": participant_id,
                    "experiment_id": "latency-benchmark",
                    "stream": "true" if stream else "false",
                },
            },
        )
        while True:
            _, event, data = await next_event()
            if event == "pid_not_found":
                raise RequestError(f"pid_not_found: {data.get('message')}")
            # The system message comes back as a bare message dict.
            if event == "message_to_client" and data.get("role") == "system":
                break
        setup_s = time.perf_counter() - t_setup0

        # 3. Send the prompt and time the reply.
        t0 = time.perf_counter()
        await sio.emit(
            "text_message",
            {
                "session_id": session_id,
                "participant_id": participant_id,
                "data": {"content": prompt, "role": "user"},
            },
        )

        t_first_event = t_first_token = None
        n_chunks = response_chars = 0
        while True:
            t, event, data = await next_event()
            if event == "message_to_client" and data.get("type") in (
                "message",
                "stream",
            ):
                if data["data"].get("role") != "assistant":
                    continue
                t_first_event = t_first_event or t
                content = data["data"].get("content") or ""
                if content and t_first_token is None:
                    t_first_token = t
                n_chunks += 1
                response_chars += len(content)
            elif event == "message_end":
                t_end = t
                status = data.get("status", "ok")
                break

        return {
            "setup_s": setup_s,
            "ttfe_s": t_first_event - t0 if t_first_event else None,
            "ttft_s": t_first_token - t0 if t_first_token else None,
            "total_s": t_end - t0,
            "n_chunks": n_chunks,
            "response_chars": response_chars,
            "status": status,
            "error": "" if status == "ok" else "backend reported an error",
        }
    finally:
        if sio.connected:
            await sio.disconnect()


# --------------------------------------------------------------------------------------
# One request straight to the provider (baseline)
# --------------------------------------------------------------------------------------


def deployment_name(cond: common.Condition) -> str:
    """On Azure, map the model name to its deployment like the backend does
    (AZURE_OPENAI_DEPLOYMENTS)."""
    if cond.provider != "azure":
        return cond.direct_model
    mapping = json.loads(os.environ.get("AZURE_OPENAI_DEPLOYMENTS") or "{}")
    return mapping.get(cond.direct_model, cond.direct_model)


def make_direct_client(cond: common.Condition):
    if cond.provider == "openai":
        return AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    if cond.provider == "azure":
        # Same choice of endpoint as the backend (AZURE_OPENAI_API_VERSION).
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01")
        if api_version == "v1":
            return AsyncOpenAI(
                api_key=os.environ["AZURE_OPENAI_API_KEY"],
                base_url=os.environ["AZURE_OPENAI_BASE_URL"].rstrip("/") + "/openai/v1/",
            )
        return AsyncAzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_endpoint=os.environ["AZURE_OPENAI_BASE_URL"],
            api_version=api_version,
        )
    return AsyncOpenAI(
        api_key=os.environ["TOGETHER_AI_KEY"], base_url=os.environ["TOGETHER_AI_URL"]
    )


def is_reasoning_model(model: str) -> bool:
    """Mirror of backend/src/utils/configs.py: GPT-5 family and o-series reject temperature."""
    name = model.lower().split("/")[-1]
    return name.startswith(("gpt-5", "o1", "o3", "o4")) and "chat" not in name


def request_params(cond: common.Condition) -> dict:
    """Same sampling settings as the backend (backend/src/utils/llm_model.py)."""
    if cond.provider == "together_ai":
        effort = os.environ.get("TOGETHER_AI_REASONING_EFFORT")
        params = {"temperature": 0.7}
        return {**params, "extra_body": {"reasoning_effort": effort}} if effort else params
    if not is_reasoning_model(cond.direct_model):
        return {"temperature": 0.7}
    effort = os.environ.get("OPENAI_REASONING_EFFORT")
    return {"extra_body": {"reasoning_effort": effort}} if effort else {}


async def direct_request(
    client,
    config: common.Config,
    cond: common.Condition,
    prompt: str,
    stream: bool,
    timeout: float,
) -> dict:
    messages = [
        {"role": "system", "content": config.system_message},
        {"role": "user", "content": prompt},
    ]

    async def run():
        t0 = time.perf_counter()
        response = await client.chat.completions.create(
            model=deployment_name(cond),
            messages=messages,
            stream=stream,
            **request_params(cond),
        )
        if not stream:
            t_end = time.perf_counter()
            content = response.choices[0].message.content or ""
            return {
                "ttfe_s": t_end - t0,
                "ttft_s": t_end - t0,
                "total_s": t_end - t0,
                "n_chunks": 1,
                "response_chars": len(content),
            }

        t_first_event = t_first_token = None
        n_chunks = response_chars = 0
        async for chunk in response:
            if not chunk.choices:
                continue
            t = time.perf_counter()
            t_first_event = t_first_event or t
            content = chunk.choices[0].delta.content or ""
            if content and t_first_token is None:
                t_first_token = t
            n_chunks += 1
            response_chars += len(content)
        t_end = time.perf_counter()
        return {
            "ttfe_s": t_first_event - t0 if t_first_event else None,
            "ttft_s": t_first_token - t0 if t_first_token else None,
            "total_s": t_end - t0,
            "n_chunks": n_chunks,
            "response_chars": response_chars,
        }

    try:
        result = await asyncio.wait_for(run(), timeout)
    except TimeoutError as e:
        raise RequestError("timeout") from e
    return {"setup_s": None, "status": "ok", "error": "", **result}


# --------------------------------------------------------------------------------------
# Blocks: one condition x stream mode x concurrency level
# --------------------------------------------------------------------------------------


async def run_block(args, config, cond, stream, concurrency, prompts, writer, run_id, block):
    jobs: asyncio.Queue[Job] = asyncio.Queue()
    # One warm-up request per worker (flagged, excluded from the analysis), then the
    # measured requests in a shuffled order.
    for i in range(concurrency):
        jobs.put_nowait(Job(rep=-1, prompt=prompts[i % len(prompts)], warmup=True))
    measured = [
        Job(rep, p, False)
        for rep, p in common.prompt_schedule(prompts, args.reps, args.requests_per_block)
    ]
    random.Random(f"{args.seed}-{block}").shuffle(measured)
    for job in measured:
        jobs.put_nowait(job)

    client = make_direct_client(cond) if args.mode == "direct" else None
    target = config.backend_url if args.mode == "backend" else f"{cond.provider} API"
    done = 0
    total_jobs = jobs.qsize()

    async def worker(worker_id: int):
        nonlocal done
        while True:
            try:
                job = jobs.get_nowait()
            except asyncio.QueueEmpty:
                return
            row = {
                "run_id": run_id,
                "mode": args.mode,
                "block": block,
                "condition": cond.name,
                "provider": cond.provider,
                "model": cond.model if args.mode == "backend" else cond.direct_model,
                "stream": stream,
                "concurrency": concurrency,
                "rep": job.rep,
                "prompt_id": job.prompt["id"],
                "worker": worker_id,
                "warmup": job.warmup,
                "started_at": common.utc_now(),
                "target": target,
                "client_host": common.client_host(),
            }
            try:
                if args.mode == "backend":
                    participant_id = f"{run_id}-b{block}-w{worker_id}-{job.prompt['id']}-r{job.rep}"
                    result = await simple_chat_request(
                        config,
                        cond,
                        job.prompt["content"],
                        stream,
                        participant_id,
                        args.timeout,
                    )
                else:
                    result = await direct_request(
                        client,
                        config,
                        cond,
                        job.prompt["content"],
                        stream,
                        args.timeout,
                    )
            # Keep going; failures are part of the data.
            # pylint: disable-next=broad-exception-caught
            except Exception as e:
                if args.verbose:
                    traceback.print_exc()
                result = {"status": "error", "error": f"{type(e).__name__}: {e}"[:300]}
            writer.write({**row, **result})
            done += 1
            if result["status"] != "ok" or args.verbose:
                print(
                    f"    [{done}/{total_jobs}] {job.prompt['id']} {result['status']} "
                    f"{result.get('error', '')}"
                )

    await asyncio.gather(*(worker(i) for i in range(concurrency)))
    if client is not None:
        await client.close()


async def main_async(args) -> None:
    config = common.load_config(args.config)
    conditions = common.select_conditions(config, args.conditions)
    prompts = common.load_prompts(args.prompts)
    streams = common.parse_stream_modes(args.stream)

    blocks = [(c, s, n) for c in conditions for s in streams for n in args.concurrency]
    # Shuffle the block order so time-of-day effects at the provider do not line up
    # with one condition.
    random.Random(args.seed).shuffle(blocks)

    run_id = common.new_run_id(args.mode)
    out = Path(args.out) if args.out else common.RAW_DIR / f"{run_id}.csv"
    writer = common.RowWriter(out, FIELDS)
    per_block = len(common.prompt_schedule(prompts, args.reps, args.requests_per_block))
    n_requests = sum(n + per_block for _, _, n in blocks)
    print(f"run {run_id}: {len(blocks)} blocks, {n_requests} requests -> {out}")

    try:
        for i, (cond, stream, concurrency) in enumerate(blocks):
            print(
                f"  block {i + 1}/{len(blocks)}: {cond.name} stream={'on' if stream else 'off'} "
                f"concurrency={concurrency}"
            )
            await run_block(args, config, cond, stream, concurrency, prompts, writer, run_id, i)
            if args.pause and i < len(blocks) - 1:
                await asyncio.sleep(args.pause)
    finally:
        writer.close()
    print(f"done -> {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default="conditions.toml")
    parser.add_argument("--prompts", default="prompts.jsonl")
    parser.add_argument(
        "--mode",
        choices=["backend", "direct"],
        default="backend",
        help="backend: through Simple Chat; direct: straight to the provider",
    )
    parser.add_argument("--conditions", nargs="*", help="subset of condition names (default: all)")
    parser.add_argument("--stream", nargs="+", default=["on", "off"], help="on and/or off")
    parser.add_argument("--concurrency", nargs="+", type=int, default=[1, 5, 20])
    parser.add_argument(
        "--reps", type=int, default=3, help="repetitions of the prompt set per block"
    )
    parser.add_argument(
        "--requests-per-block",
        type=int,
        help="exact number of measured requests per block, cycling through the "
        "prompts (overrides --reps)",
    )
    parser.add_argument("--timeout", type=float, default=120, help="seconds per request")
    parser.add_argument("--pause", type=float, default=5, help="seconds between blocks")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--env-file", help="dotenv file with provider keys (for --mode direct)")
    parser.add_argument("--out", help="output CSV (default: data/raw/<run_id>.csv)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.env_file:
        load_dotenv(args.env_file)
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
