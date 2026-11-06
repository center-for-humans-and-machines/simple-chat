"""Shared helpers for the Simple Chat latency benchmark scripts."""

from __future__ import annotations

import csv
import json
import platform
import socket
import tomllib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW_DIR = HERE / "data" / "raw"
RESULTS_DIR = HERE / "results"

PROVIDERS = ("openai", "azure", "together_ai")


@dataclass
class Condition:
    """One model/provider combination to benchmark."""

    name: str
    provider: str  # openai | azure | together_ai
    model: str  # value of the `model` query parameter sent to Simple Chat
    pid: str  # Simple Chat project ID (its openai_backend selects OpenAI vs Azure)
    direct_model: str = ""  # model/deployment name for the direct-to-provider baseline

    def __post_init__(self):
        if self.provider not in PROVIDERS:
            raise ValueError(f"{self.name}: provider must be one of {PROVIDERS}")
        self.direct_model = self.direct_model or self.model


@dataclass
class Config:
    backend_url: str
    frontend_url: str
    requested_by: str
    system_message: str
    conditions: list[Condition] = field(default_factory=list)


def load_config(path: str | Path) -> Config:
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    conditions = [Condition(**c) for c in raw.pop("conditions", [])]
    if not conditions:
        raise ValueError(f"{path}: no [[conditions]] defined")
    return Config(conditions=conditions, **raw)


def select_conditions(config: Config, names: list[str] | None) -> list[Condition]:
    if not names:
        return config.conditions
    known = {c.name: c for c in config.conditions}
    missing = [n for n in names if n not in known]
    if missing:
        raise SystemExit(f"Unknown condition(s): {missing}. Known: {list(known)}")
    return [known[n] for n in names]


def load_prompts(path: str | Path) -> list[dict]:
    """Read the fixed prompt set: one JSON object per line with `id` and `content`."""
    prompts = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                prompts.append(json.loads(line))
    return prompts


def prompt_schedule(prompts: list[dict], reps: int, n_requests: int | None) -> list[tuple[int, dict]]:
    """(rep, prompt) pairs for one condition: the prompt set `reps` times, or exactly
    `n_requests` requests cycling through the prompts in order."""
    n = n_requests if n_requests else reps * len(prompts)
    return [(i // len(prompts), prompts[i % len(prompts)]) for i in range(n)]


def parse_stream_modes(values: list[str]) -> list[bool]:
    mapping = {"on": True, "off": False}
    try:
        return [mapping[v] for v in values]
    except KeyError as e:
        raise SystemExit(f"--stream accepts 'on' and/or 'off', got {e}") from e


def new_run_id(mode: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{mode}-{stamp}-{uuid.uuid4().hex[:6]}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def client_host() -> str:
    """Describe the machine that ran the benchmark (stored with every row)."""
    return f"{socket.gethostname()} ({platform.system()} {platform.machine()})"


class RowWriter:
    """Append rows to a CSV file and flush after each one, so a crash keeps the data."""

    def __init__(self, path: Path, fieldnames: list[str]):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._file = open(path, "w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=fieldnames, extrasaction="ignore")
        self._writer.writeheader()

    def write(self, row: dict) -> None:
        self._writer.writerow(row)
        self._file.flush()

    def close(self) -> None:
        self._file.close()
