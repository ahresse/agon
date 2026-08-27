# Test Plugin & Container Execution Contract

This contract defines how a test plugin integrates with Agon so that new tests can be added without
changing the framework core (Constitution Principle III), and how every test — metric-based and
AI-agent — runs in an isolated LXC/LXD container (Constitution Principle II).

## Plugin interface (weight-in / grade-out)

Every test plugin registers under a stable `key` and exposes a single entry point conforming to:

**Input** (provided by the framework):

| Field | Description |
|-------|-------------|
| submission_path | Path (inside the container) to the candidate's Python source |
| config | Plugin-specific configuration (e.g., AI-agent theme, thresholds) |
| timeout_seconds | Hard limit after which the run is aborted and marked FAILED |

**Output** (returned by the plugin):

| Field | Type | Rules |
|-------|------|-------|
| grade | number | 0-100, required (Principle I, FR-005) |
| pros | string[] | Structured positive findings (evidence) |
| cons | string[] | Structured negative findings (evidence) |

Rules:

- A plugin MUST return a reproducible grade derived from measurable signals (Principle I).
- A plugin MUST NOT require changes to the framework core to be added, removed, or reconfigured.
- The `weight` is NOT a plugin concern — weighting is applied by the grading service using
  `Test.default_weight` and per-review overrides (Principle IV, FR-006/009).
- Language support (Python first) extends through this same interface; a plugin declares the
  language(s) it supports rather than the core special-casing languages (Principle III).

## Test types

- **METRIC**: computes grade from deterministic measurements over the source.
- **AI_AGENT**: scoped to a specific `theme`; obtains intelligence from a pluggable provider
  interface invoked from **inside** the container. It returns the same `{grade, pros, cons}` shape
  and is graded identically (FR-013).

## Built-in metric plugins (Python quality suite)

The initial METRIC plugins assess Python code quality; each is an independent plugin under
`backend/src/tests_plugins/` conforming to the interface above and normalizing its raw tool output to
a 0-100 grade (see research.md §9 for grade derivation and thresholds):

| Plugin key | Signal / tool | Assesses |
|------------|---------------|----------|
| `lint_ruff` | `ruff check` (JSON) | Style, lint errors, correctness smells |
| `complexity_radon` | `radon cc` + `radon mi` | Cyclomatic complexity & maintainability |
| `stdlib_idioms` | AST analysis | Pythonic use of builtins/standard library vs. anti-patterns |
| `type_check_mypy` | `mypy` | Static typing errors & annotation coverage |
| `security_bandit` | `bandit` (JSON) | Common security issues (severity-weighted) |
| `formatting_black` | `black --check` + docstring coverage | Formatting conformance & documentation |

Each plugin's tunable thresholds (penalty weights, CC threshold, strictness) live in its `config`, so
admins adjust behavior and default weights (FR-008) without core changes (Principle III). All metric
tools are bundled in the metric container image and run read-only against the candidate source
(Principle II).

## Container execution guarantees

For every test run the framework MUST:

1. Create a fresh, disposable LXC/LXD container; never execute candidate code or AI agents on the
   host (Principle II — NON-NEGOTIABLE).
2. Place the candidate source inside the container in isolation from other runs.
3. Enforce `timeout_seconds`. On crash or timeout the run is recorded as `status = FAILED`,
   `grade = 0`, and remaining tests continue (FR-007).
4. Read back only the structured `{grade, pros, cons}` result over the LXD API.
5. Destroy the container after the run, guaranteeing no cross-run contamination.

## Grading integration

- The grading service collects each plugin's `grade`, applies the effective weight, and computes the
  final grade as the weighted mean (FR-006). Failed tests keep grade 0 and retain their weight
  (FR-007).
- Recomputation on weight change reads stored results only and never re-invokes plugins or containers
  (FR-010, SC-003).

## Conformance tests (to be authored under backend/tests/contract/)

- A plugin returning a grade outside 0-100 is rejected.
- A plugin that raises/hangs beyond `timeout_seconds` yields a FAILED result with grade 0, and the
  overall review still completes.
- No test execution path runs outside a container (verified by asserting container lifecycle per run).
- Adding a new registered plugin requires no edit to core scheduling/grading modules.
