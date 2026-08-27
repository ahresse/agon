# Phase 0 Research: End-to-End Candidate Code Review Flow

All Technical Context choices were resolved during planning (no open NEEDS CLARIFICATION). This
document records the decisions, rationale, and rejected alternatives.

## 1. Backend language & framework

- **Decision**: Python 3.11 with FastAPI + Uvicorn.
- **Rationale**: The project is Python-centric (assessed code is Python; test plugins are naturally
  authored in Python). FastAPI provides first-class async for driving background jobs and container
  I/O, Pydantic schemas that double as the API contract, and a small footprint suitable for arm64.
- **Alternatives considered**: Go (smallest footprint, single binary, but splits the language from
  the Python test-plugin ecosystem, raising plugin-authoring friction — rejected against Principle
  III's goal of easy test development). Node.js/TypeScript (viable, but duplicates the frontend
  language on the backend while distancing it from Python plugins — rejected).

## 2. Frontend stack

- **Decision**: React + TypeScript, built with Vite.
- **Rationale**: Mature ecosystem for structured dashboards (per-test breakdown, pros/cons, weight
  editor). TypeScript enables generating a typed client from the OpenAPI contract, reducing
  frontend/backend drift. Vite yields a small static bundle servable from the Pi.
- **Alternatives considered**: Vue (comparable; React chosen for larger component ecosystem).
  Server-rendered templates (lowest JS footprint, but the required interactive weight-editing and
  instant re-grade UX are more naturally an SPA concern — rejected).

## 3. Storage

- **Decision**: SQLite (single file) for structured data; local filesystem for uploaded archives,
  referenced by DB rows.
- **Rationale**: Zero-configuration, single-file database is ideal for a single self-hosted
  Raspberry Pi (Principle V). Expected concurrency (team-scale) is well within SQLite's limits.
  Grading is a pure recomputation over stored rows, which SQLite serves comfortably.
- **Alternatives considered**: PostgreSQL (stronger concurrency and tooling, but a heavier resident
  service on constrained hardware — rejected for this single-instance scope; the persistence layer
  is abstracted via SQLAlchemy so a later migration is possible).

## 4. Asynchronous test execution

- **Decision**: In-process, SQLite-backed job queue. Jobs (test runs) are persisted as rows with a
  status lifecycle; a worker pool within the backend process claims and executes them.
- **Rationale**: No external broker keeps the footprint minimal on a Pi (Principle V). Persisting
  job state in the DB survives restarts and makes progress observable for the async UX (FR-003).
  Container start + test runtime dominate latency, so a broker adds little throughput benefit here.
- **Alternatives considered**: Redis + Celery / RQ (better horizontal scale, but adds a resident
  broker and worker processes — rejected against the single-instance, low-footprint constraint).

## 5. Containerized execution (LXC/LXD)

- **Decision**: Each test run executes in a fresh, disposable LXD container via the LXD API
  (pylxd). Candidate code and AI-agent tests alike run only inside containers; results are read back
  over the API. A per-test timeout enforces failure isolation.
- **Rationale**: Constitution II is non-negotiable — no host execution. LXD is native to Ubuntu and
  arm64-capable, aligning with the deployment target. Disposable containers guarantee inter-test
  isolation (Principle II) and clean, reproducible runs (Principle I).
- **Alternatives considered**: Docker/OCI runtimes (workable, but the constitution explicitly names
  LXC/LXD; LXD's system-container model also fits running full toolchains — chosen). Host processes
  with namespaces only (rejected — insufficient isolation and constitution violation).

## 6. AI-agent test integration

- **Decision**: The AI-agent test targets a specific theme and calls a pluggable provider through a
  configurable interface from *inside* its container. The provider is abstracted behind a small
  interface so the concrete model/endpoint is a deployment choice.
- **Rationale**: Keeps AI agents subject to the same containerization guarantee (Principle II) and
  the same weight-in/grade-out plugin contract (Principle III), so an agent grade folds into the
  weighted mean identically to a metric test.
- **Alternatives considered**: Hard-coding a single external LLM API (reduces flexibility and could
  break self-hosting if offline — rejected). Local on-device model only (viable for offline use but
  heavy for a Pi and premature to fix now — deferred; the abstract provider allows either later).

## 7. Language detection & rejection

- **Decision**: Detect language from archive contents (file extensions plus lightweight content
  heuristics). Accept Python; reject anything else with a clear message before any assessment starts.
- **Rationale**: Satisfies FR-002/FR-016 and avoids spinning up containers for unsupported input.
  Keeping detection behind a small interface lets future languages plug in via the same test
  contract (Principle III).
- **Alternatives considered**: Reviewer-declared language at upload (simpler but error-prone and
  weaker guarantee — auto-detection chosen; a manual confirmation step can be layered later).

## 8. Grading computation

- **Decision**: Final grade is a pure function: weighted mean of the 0-100 test grades using
  effective weights (admin defaults overlaid with per-review reviewer overrides). Failed/timed-out
  tests contribute grade 0 but retain their weight. Recomputation reads stored `TestResult`s only.
- **Rationale**: Purity makes weight changes an instant recompute with no re-execution (FR-010,
  SC-003) and makes grades fully explainable (Principle IV). Failure isolation (FR-007) is a
  grading rule, not an execution branch.
- **Alternatives considered**: Excluding failed tests from the mean (rejected — masks real quality
  gaps and contradicts the chosen "isolate & continue" edge-case behavior). Re-running on weight
  change (rejected — violates FR-010 and SC-003).

## 9. Built-in Python quality tests (metric-based plugins)

- **Decision**: Ship a suite of deterministic, metric-based Python quality plugins, each conforming
  to the weight-in/grade-out contract and running inside its own container. Each maps a measurable
  signal to a reproducible 0-100 grade with structured pros/cons (Principle I). Initial suite:

  | Plugin key | Theme | Tool / signal | 0-100 grade derivation | Evidence (pros/cons) |
  |------------|-------|---------------|------------------------|----------------------|
  | `lint_ruff` | Style & correctness | `ruff check` (JSON) | 100 minus a weighted penalty per violation, normalized by lines-of-code; 0 floor | Top violation codes/messages as cons; clean files as pros |
  | `complexity_radon` | Complexity | `radon cc` (cyclomatic) + `radon mi` (maintainability index) | Blend: MI mapped to 0-100; functions above CC threshold penalized | High-CC functions as cons; simple/maintainable modules as pros |
  | `stdlib_idioms` | Pythonic use of standard library | AST analysis: use of builtins/stdlib (`enumerate`, `zip`, comprehensions, context managers, `pathlib`, `dataclasses`) vs. anti-patterns (bare `except`, mutable default args, manual index loops, `os.path` where `pathlib` fits) | Ratio of idiomatic constructs to detected anti-patterns, scaled to 0-100 | Idioms used as pros; anti-patterns with line refs as cons |
  | `type_check_mypy` | Static typing | `mypy` (strict-ish) error count + annotation coverage | 100 minus penalty per type error, weighted by annotation coverage | Missing/incorrect annotations as cons; well-typed APIs as pros |
  | `security_bandit` | Security | `bandit` (JSON) severity-weighted issue count | 100 minus severity-weighted penalties (HIGH ≫ MEDIUM ≫ LOW) | Security issues (with CWE/test id) as cons; clean scan as pro |
  | `formatting_black` | Formatting & docs | `black --check --diff` conformance + docstring coverage (AST) | Blend of formatting-conformance ratio and public-symbol docstring coverage | Undocumented/ill-formatted symbols as cons; conformant/documented as pros |

- **Rationale**: These tools are the de-facto Python quality toolchain, are deterministic (same input
  → same grade, Principle I), install cleanly on arm64, and each already emits machine-readable output
  suited to structured pros/cons evidence (Principle IV). Packaging each as an independent plugin
  keeps them addable/removable without core changes (Principle III) and lets admins tune default
  weights per quality dimension (FR-008).

- **Grade normalization**: Each plugin normalizes its raw tool output to 0-100 so grades are
  comparable across dimensions before weighting. Normalization thresholds (e.g., penalty-per-violation,
  CC threshold) live in each plugin's `config` so admins can tune without code changes.

- **Container toolchain**: The metric container image/profile bundles `ruff`, `radon`, `mypy`,
  `bandit`, `black`, and `coverage`/`pytest`. Tools run against the candidate source read-only inside
  the disposable container; only the structured `{grade, pros, cons}` is read back (Principle II).

- **Alternatives considered**: A single monolithic "quality" test aggregating all tools (rejected —
  collapses independent signals into one grade, defeating per-dimension weighting and the extensible
  plugin model of Principle III). `pylint` as the primary linter (viable, but `ruff` is far faster on
  arm64 and covers most `pylint`/`flake8` rules — chosen; `pylint` can be added later as its own
  plugin via the same contract). `flake8` + plugins (superseded by `ruff` for speed/footprint).

- **`test_coverage_pytest` (deferred, optional)**: Running the candidate's own test suite under
  `coverage` in-container is attractive but depends on submissions shipping tests and safe execution
  of candidate tests; deferred behind the same contract to a follow-up, since it executes candidate
  code (still containerized) rather than only statically analyzing it.
