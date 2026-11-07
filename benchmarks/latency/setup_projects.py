"""Register one Simple Chat project per benchmark condition and set its OpenAI backend.

Usage:
    python setup_projects.py --config conditions.toml
"""

# This command-line script reports project setup on stdout.
# ruff: noqa: T201

from __future__ import annotations

import argparse

import httpx
from common import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default="conditions.toml")
    args = parser.parse_args()

    config = load_config(args.config)
    with httpx.Client(base_url=config.backend_url, timeout=30) as client:
        for cond in config.conditions:
            r = client.post(
                "/project/register",
                json={
                    "project_id": cond.pid,
                    "requested_by": config.requested_by,
                    "system_message": config.system_message,
                },
            )
            if r.status_code == 200:
                print(f"{cond.pid}: registered")
            elif "already a project" in r.text:
                print(f"{cond.pid}: already exists (system message left unchanged)")
            else:
                raise SystemExit(
                    f"{cond.pid}: register failed: {r.status_code} {r.text}"
                )

            # OpenAI and Azure share model names; the project's backend picks the provider.
            if cond.provider in ("openai", "azure"):
                r = client.get(
                    f"/dashboard/toggle_openai_backend/{cond.pid}/{cond.provider}"
                )
                r.raise_for_status()
                print(f"{cond.pid}: openai_backend = {cond.provider}")


if __name__ == "__main__":
    main()
