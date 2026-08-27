# Agon

Agon turns a candidate's Python submission into an explainable, weighted grade.
A reviewer uploads a code archive through the web interface; enabled tests
(metric-based and at least one AI-agent test) run **each in an isolated,
disposable LXC/LXD container**, every test emits a 0-100 grade plus structured
pros/cons, and the final grade is the weighted mean. Admins configure tests,
default weights, and users; reviewers can override weights per-review and see the
grade recompute instantly from stored results without re-running tests.

The project is developed with a spec-driven workflow; feature specifications,
plans, and tasks live under [`specs/`](./specs).

## Principles

Agon follows its [constitution](./.specify/memory/constitution.md):

1. **Measurable Assessment** — every grade traces to reproducible metrics.
2. **Sandboxed Execution (non-negotiable)** — all candidate code and AI agents run
   in LXC/LXD containers, never on the host.
3. **Extensible Test Framework** — tests are self-contained plugins (weight-in /
   grade-out) added without touching the core.
4. **Weighted, Transparent Grading** — weighted mean + per-test breakdown + pros/cons.
5. **Portable & Self-Hostable** — runs on a Raspberry Pi (Ubuntu, arm64).

## Architecture

- **Service** (`app/`): FastAPI + SQLAlchemy (SQLite), an in-process
  SQLite-backed job queue, and an LXD-based container runner. Built-in Python
  quality plugins: `ruff` lint, `radon` complexity, standard-library idioms,
  `mypy` typing, `bandit` security, `black`+docstring formatting, and a
  **git commit-quality** assessment, plus a themed AI-agent test.
- **Web interface** (`app/src/templates/`, `app/src/static/`): server-rendered
  HTML (Jinja2) served by the same Python service — upload, review breakdown, weight
  editor, history, and admin configuration pages. Interactivity (instant re-grade, log
  expand) uses a single vendored, non-authored helper (htmx) served as a static asset;
  the project authors **no JavaScript** (feature 005).

## Requirements

- Python 3.11+ (single language — no JavaScript runtime or package/build tooling required).
- LXD installed and initialized (`lxd init`) for real sandboxed execution.

## Quick start (development)

### One command (recommended)

```bash
./run.sh
```

This creates a virtualenv, installs the app, seeds the database on first run, and
starts the server at `http://127.0.0.1:8000/`. Override the bind address or the
runner with environment variables:

```bash
HOST=0.0.0.0 PORT=9000 ./run.sh          # bind on the LAN / custom port
AGON_USE_LOCAL_RUNNER=1 ./run.sh          # dev fallback without LXD (non-isolating)
```

Default accounts: `admin` / `admin`, `reviewer` / `reviewer`.

### Provision the test container image (once, for real sandboxed execution)

```bash
./app/src/runners/provision_image.sh   # builds the `agon-python` LXD image
```

If LXD is unavailable (dev/CI only), set `AGON_USE_LOCAL_RUNNER=1` to use the
non-isolating local runner — never use this in production.

### Manual setup (equivalent to `run.sh`)

```bash
cd app
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
python -m src.seed          # seeds admin/reviewer users + built-in tests
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

Default accounts: `admin` / `admin`, `reviewer` / `reviewer`.

Open `http://127.0.0.1:8000/` and sign in. The web interface is served by the same
Python service (no separate frontend build). Upload a `.zip` or `.tar.gz` of Python
source, then view the weighted grade, per-test breakdown, and pros/cons.

## Configuration (environment variables)

| Variable | Default | Purpose |
|----------|---------|---------|
| `AGON_DATABASE_URL` | `sqlite:///./agon.db` | Database URL |
| `AGON_UPLOAD_DIR` | `./uploads` | Uploaded submission storage |
| `AGON_LXD_PROFILE` | `agon-python` | LXD image/profile for test containers |
| `AGON_USE_LOCAL_RUNNER` | `0` | `1` = non-isolating dev fallback (never in prod) |
| `AGON_RUN_JOBS_INLINE` | `0` | `1` = run assessments synchronously in-request |
| `AGON_JOB_WORKERS` | `2` | Background worker count |
| `AGON_TEST_TIMEOUT` | `60` | Per-test timeout (seconds) |
| `AGON_AI_PROVIDER_URL` | _unset_ | Optional AI provider endpoint |

## Tests

```bash
cd app      && pytest            # full app (unit, contract, integration, web)
cd app      && pytest tests/meta # repo-hygiene + no-JavaScript guardrail
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) for commit conventions (enforced by the
repo-hygiene meta-tests).

## Status

- `001-code-review-flow` — implemented (upload `.zip`/`.tar.gz` → weighted grade,
  weight overrides, admin config, history, AI-agent test, containerized execution).
- `002-one-command-deploy` — specified; single-command, host-safe deployment with
  local web access is planned but not yet implemented.
- `003-git-quality-assessment` — implemented (a metric test grading a candidate's
  commit message quality, granularity, and signing when the submission includes a
  git history).
