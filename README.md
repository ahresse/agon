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

- **Backend** (`backend/`): FastAPI + SQLAlchemy (SQLite), an in-process
  SQLite-backed job queue, and an LXD-based container runner. Built-in Python
  quality plugins: `ruff` lint, `radon` complexity, standard-library idioms,
  `mypy` typing, `bandit` security, and `black`+docstring formatting, plus a
  themed AI-agent test.
- **Frontend** (`frontend/`): React + TypeScript (Vite) — upload, review breakdown,
  weight editor, history, and admin configuration pages.

## Requirements

- Python 3.11+ and Node.js.
- LXD installed and initialized (`lxd init`) for real sandboxed execution.

## Quick start (development)

### 1. Provision the test container image (once)

```bash
./backend/src/runners/provision_image.sh   # builds the `agon-python` LXD image
```

If LXD is unavailable (dev/CI only), set `AGON_USE_LOCAL_RUNNER=1` to use the
non-isolating local runner — never use this in production.

### 2. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
python -m src.seed          # seeds admin/reviewer users + built-in tests
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

Default accounts: `admin` / `admin`, `reviewer` / `reviewer`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                 # or: npm run build && npm run preview
```

Open the printed local URL and sign in. Upload a `.zip` or `.tar.gz` of Python
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
cd backend  && pytest            # backend (unit, contract, integration)
cd frontend && npx vitest run    # frontend components
```

## Status

- `001-code-review-flow` — implemented (upload → weighted grade, weight overrides,
  admin config, history, AI-agent test, containerized execution).
- `002-one-command-deploy` — specified; single-command, host-safe deployment with
  local web access is planned but not yet implemented.
