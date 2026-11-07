# Latency Benchmark

Measures how quickly Simple Chat answers: the time to the first token and the time
to the full reply, with streaming on and off, for several LLM providers and 1, 5
or 20 concurrent chat sessions. The raw data and results in this folder are the
ones cited in the Simple Chat paper.

The committed CSVs cover OpenAI GPT-5.1, Azure GPT-5.1, and Together AI DeepSeek
V4.1 Flash in backend and direct modes (6 November 2026), and the same three
conditions end to end in desktop Chrome and an emulated iPhone Safari (7 November
2026, `e2e-*.csv`), with a direct-to-provider baseline from the same day. The
end-to-end runs used the production Docker stack (`docker compose --profile prod`)
on the benchmark machine. The example
configuration names these same conditions.

## What Is Measured

| Script                         | Path measured                                   | Main metrics                                   |
| ------------------------------ | ----------------------------------------------- | ---------------------------------------------- |
| `run_backend.py`               | Client → Simple Chat backend (Socket.IO) → LLM  | `ttft_s`, `total_s` under 1 / 5 / 20 sessions  |
| `run_backend.py --mode direct` | Client → LLM provider API, no Simple Chat       | Same, as a baseline for Simple Chat's overhead |
| `run_e2e.py`                   | Browser → frontend in an iframe → backend → LLM | On-screen times under 1 / 5 / 20 sessions      |

- `ttfe_s`: time to the first assistant event (OpenAI's first chunk carries only the role)
- `ttft_s`: time to the first chunk with text (time to first token)
- `total_s`: time until the reply is complete (`message_end` event)
- `setup_s`: time from connecting (or loading the page) until the chat is ready
- `ttft_render_s` / `total_render_s` (end-to-end only): first and last character on screen.
  The frontend types replies out at 20 ms per character, so on-screen completion
  is mostly the length of the reply times 20 ms, whatever the network does.

With streaming off, the first token arrives with the full reply, so `ttft_s`
equals `total_s` in the backend and direct modes.

Each measured request uses a fresh chat session with a single prompt, so history
and the token limit stay the same. Each block (condition × streaming ×
concurrency) starts with one warm-up request per session. Warm-ups are stored but
left out of the analysis. Blocks run in a shuffled (seeded) order so that changes
in provider load over time do not line up with one condition.

## Setup

Requires Python 3.11 or later and a running Simple Chat deployment. Results depend
on where the backend runs, so use the deployment you report.

```bash
cd benchmarks/latency
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium webkit   # for run_e2e.py; desktop Chrome uses your installed Chrome
cp conditions.example.toml conditions.toml   # then edit
python setup_projects.py --config conditions.toml
```

For GPT-5 models (such as `gpt-5.1-2025-11-13`), set `AZURE_OPENAI_API_VERSION=v1`
in the backend `.env`, and optionally `OPENAI_REASONING_EFFORT`. Reasoning effort
strongly affects time to first token, so report the value used. Simple Chat and
the direct baseline read the same variables, so both send the same request.

`setup_projects.py` registers one project per condition and sets its OpenAI
backend (`openai` or `azure`), because OpenAI and Azure use the same model names.
The backend selects the provider per project.

## Running

```bash
# Through Simple Chat: all conditions, streaming on/off, 1/5/20 sessions, 3 repetitions
python run_backend.py --config conditions.toml

# Direct-to-provider baseline (reads the same keys as the backend)
python run_backend.py --config conditions.toml --mode direct --env-file ../../backend/.env

# End to end in browsers: desktop Chrome and emulated iPhone Safari,
# 1/5/20 sessions open at once, 30 measured trials per block
python run_e2e.py --config conditions.toml --trials 30

# Direct baseline for the end-to-end run, on the same day with the same 30 requests
python run_backend.py --config conditions.toml --mode direct --env-file ../../backend/.env --requests-per-block 30

# p50/p95 table, overhead table and figures
python analyze.py
```

Every run writes one CSV to `data/raw/`, with one row per request. `analyze.py`
combines all of them into:

- `results/summary.csv`: n, error rate, and p50/p95 of every metric per mode,
  condition, streaming, concurrency and device
- `results/overhead.csv`: Simple Chat backend minus direct p50/p95, per condition
- `results/overhead-e2e.csv`: first character on screen minus direct time to first
  token, and full reply on screen minus direct full completion, per condition and
  device
- `results/latency.png` and `.pdf`: backend time to first token and full completion
  against concurrent sessions
- `results/latency-e2e.png` and `.pdf`: first and last character on screen in the
  browser against concurrent sessions, per device, next to the direct baseline
- `results/latency-paper.pdf` and `.png`: the figure in the paper, the time until the
  first text is visible (median and interquartile range, Simple Chat on screen vs
  direct API), drawn at print size and cropped to its content

`analyze.py` compares Simple Chat runs only with direct runs from the same day
(`date` column), so provider load is similar on both sides.

The summary CSV and figures for the committed raw data are also versioned here.
`overhead.csv` subtracts the two groups' p50 or p95 values. Those differences
describe the measured groups; they are not per-request overhead measurements.

Benchmark conversations are stored like any other conversation, with
`experiment_id = latency-benchmark`, so they can be filtered out or deleted later.

## Notes for Reporting

- Report the deployment (host, region, instance size), the client machine and
  network, the date, and the model versions. `client_host` and `started_at` are in
  every row.
- The mobile devices in `run_e2e.py` are emulated: Playwright reproduces the
  viewport, user agent and touch input of a Pixel 7 (Chromium) and an iPhone 14
  (WebKit), not the phone hardware or a mobile network. For real devices, run the
  same page on a phone or a device cloud and note it.
- `run_e2e.py` opens every browser session on the client machine. At 20 sessions,
  the client's CPU can delay rendering, so watch its load and report the machine.
- `--reps 3` with 12 prompts gives 36 measured requests per block. Increase it
  if the p95 values are unstable between runs.
