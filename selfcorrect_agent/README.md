# selfcorrect_agent

A drop-in **self-correcting code agent**. Copy this folder into any Python
project, call one function, and it opens a local **one-page review website**.
Point it at a file (or upload one in the UI); it generates a test suite, runs
it, diagnoses failures, corrects itself (the dreaming cycle), then shows exactly
what changed and asks you to approve before anything is written to disk.

The dashboard also reports the generated-test pass rate for the original file
and the final candidate, for example `0% before -> 100% after (+100% lift)`.

It implements the loop from the PRD:

```
Generate -> Run -> Diagnose -> Correct / Escalate / Quarantine -> Verify -> Stop
```

## Install

```bash
pip install -r selfcorrect_agent/requirements.txt
```

Drop the `selfcorrect_agent/` folder anywhere on your `PYTHONPATH` (e.g. the
root of your repo).

## Use it (the website)

```python
from selfcorrect_agent import improve_file
improve_file("path/to/your_module.py")   # opens http://127.0.0.1:8765
```

or from the command line:

```bash
python -m selfcorrect_agent path/to/your_module.py
```

The page is a single productivity dashboard with:

- path entry for files already on the machine,
- drag-and-drop / picker upload for `.py` files,
- the full Generate -> Run -> Diagnose -> Correct -> Verify -> Score cycle,
- before/after improvement percentage,
- tabs for original code, proposed diff, improved code, and generated tests,
- **Apply to file** / **Reject** controls.

Apply writes the file (after saving `your_module.py.bak.<timestamp>`) and,
optionally, the test file as `test_your_module.py`.

## Plug it into a host project

The simplest integration is still:

```python
from selfcorrect_agent import improve_file

improve_file("app/services/pricing.py")
```

If your project already has an agent/model abstraction, pass a provider object
with `propose(filename, code)`, `diagnose(code, tests_code, failure_output)`,
and `revise(code, tests_code, failure_output, classification)` methods:

```python
from selfcorrect_agent import Config, improve_file

improve_file(
    "app/services/pricing.py",
    config=Config(port=9000),
    provider=my_provider,
)
```

The same `provider=` hook is available on `run_headless(...)` and
`server.create_app(...)`.

## Use it headless (CI / scripts)

```python
from selfcorrect_agent import run_headless
s = run_headless("path/to/your_module.py")
print(s.status, s.attempts_used, s.final_summary)
print(f"{s.before_score}% -> {s.after_score}% ({s.improvement_percent:+.1f}% lift)")
print(s.unified_diff)
if s.status == "ready" and s.changed:
    s.apply()          # writes file + backup; only call after your own check
```

```bash
python -m selfcorrect_agent path/to/file.py --headless          # print the proposal
python -m selfcorrect_agent path/to/file.py --headless --apply  # and apply it
```

## Real model vs offline demo

- Set `ANTHROPIC_API_KEY` to use the real Claude model (default
  `claude-sonnet-4-6`, override with `SELFCORRECT_MODEL`).
- With no key, or `SELFCORRECT_MOCK=1`, it uses a deterministic **offline
  provider** so you can see the whole loop and UI without any API calls. Try:

```bash
python -m selfcorrect_agent selfcorrect_agent/example_target.py --mock
```

## Verify the install

```bash
python -m selfcorrect_agent.selftest      # runs the loop + website end-to-end (offline)
```

The self-test verifies the path workflow, upload workflow, self-correction
iteration, apply/backup behavior, and the before/after score.

## Configuration (env vars)

| Variable | Default | Meaning |
|---|---|---|
| `ANTHROPIC_API_KEY` | – | enables the real model |
| `SELFCORRECT_MODEL` | `claude-sonnet-4-6` | model id |
| `SELFCORRECT_MAX_ATTEMPTS` | `4` | correction budget before escalating |
| `SELFCORRECT_TEST_TIMEOUT` | `60` | per-run pytest timeout (s) |
| `SELFCORRECT_PORT` / `SELFCORRECT_HOST` | `8765` / `127.0.0.1` | web UI |
| `SELFCORRECT_MOCK` | `0` | force offline provider |

## Safety notes (read before pointing at production code)

- **Human-in-the-loop by default.** The agent never edits your file on its own.
  The web flow and `run_headless` both stop at a proposal; writing happens only
  on explicit approval (`apply`).
- **Backups.** Every apply copies the original to `*.bak.<timestamp>` first.
- **Generated tests execute code** in a temp sandbox subprocess with a timeout.
  Run the agent in an environment you trust, and review the proposed change and
  tests before applying to anything important.
- **Scope.** Start with one file. The agent improves the target file and writes
  one test file beside it; it touches nothing else.
