# SKILL: AGON V2 Requirements & System Engineering

## Project Context

**AGON** is a Python application that evaluates coding assignments packaged as
archives (`.tar.gz`, `.zip`). The current version (V1) does the following:

1. Spins up an ephemeral LXD container from a configurable image (default
   `ubuntu:24.04`).
2. Uploads the archive into the container.
3. Extracts it.
4. Runs a hard-coded set of static-analysis checks (`archive-format`,
   `pylint`, `flake8`).
5. Derives a grade (0–20) for each check, aggregates them with fixed weights,
   prints a colored summary, opens a shell, then destroys the container.

**AGON V2 goals** (from the user's brief and the `REQ*.yml` documents):

- Keep the container lifecycle but make the *test suite* modular and
  user-definable.
- Support **atomic tests**: small, independent checks that can be deterministic
  (run a command inside the container, compute a grade from stdout/stderr) or
  **agent-based** (dispatch a prompt+source-tree excerpt to an AI agent and
  capture a grade + reasoning).
- Support **injection**: push auxiliary files (test harnesses, mocks, config,
  etc.) into the container at pre-extract / post-extract / independent moments.
- Support **setup-phase detection**: read `README`, `Makefile`,
  `requirements.txt`, `pyproject.toml`, etc., and run the inferred build/install
  steps before the actual tests.
- Support **named test-suite presets** so users can say
  `--preset python-project` instead of listing 15 individual tests.
- Keep the weighted aggregation and the final summary/report.
- Use **Doorstop** (requirements management using plain YAML files in git) to
  trace every architectural decision back to a requirement.

## How the Requirements Must Be Organised

### Single parent document for the *framework* only

There is **only one top-level Doorstop document** called `REQ` (stored under
`docs/reqs/`). It holds *normative* requirements that describe the AGON V2 framework
itself: container lifecycle, test orchestration, aggregation, CLI, preset
registry, injection engine, setup-phase handling, and deterministic/agent test
runners.

There is **no HLREQ / LLREQ / TEST split inside the framework document**.
Doorstop's natural hierarchy (levels like `1.1`, `1.2`, …) is enough to keep the
requirements readable.

### Future documents for downstream consumers

Later, the user will create **separate Doorstop documents** (e.g. `JOB`,
`PLUGIN`, `ASSESS`) that sit *beside* `REQ`, not under it. Those documents will
contain:

- Concrete test definitions (the actual atomic tests that run inside the
  container).
- Job / plugin specs (e.g. a “python-linter” plugin, a “rust-compiler” plugin).
- Assessment rubrics (how a specific agent prompt maps to the 0–20 grading
  scale).

Those future documents *link back* to the framework requirements (e.g. a
`LLREQ` item in `ASSESS` links to `REQ003` or `REQ005`) but they live in their
own directories with their own `.doorstop.yml`. This keeps the framework lean
and avoids polluting the core requirements with implementation-specific test
logic.

### Naming/numbering conventions (current agreement)

- `docs/reqs/` → `.doorstop.yml` with `prefix: REQ`
- Items: `REQ001.yml` … `REQ999.yml`
- `level:` follows the Doorstop decimal scheme (`1.1`, `1.2`, `1.10`, …).
- `links:` is left empty (`[]`) until the user explicitly adds parent/child
  links. The `reviewed:` field can be `null` during drafting and populated
  only when the user marks the item as reviewed.
- All items should be `normative: true` and `active: true` unless they are
  explicitly retired.

## What "Setup Phase" Means in This Context

The setup phase is the *bridge* between "raw extracted archive" and "ready to
assess". In V1 nothing is built or installed; pylint and flake8 just run on the
source as-is. In V2 the user wants to support archives that contain their own
build instructions. Therefore the framework requirements must mandate:

1. **Detection** (`REQ013`) – scan for well-known instruction files.
2. **Execution** (`REQ014`) – run inferred steps (dependency install → build →
   test harness preparation) inside the container, in a predictable order,
   capturing logs.
3. **Resilience** (`REQ015`) – if a setup step fails, fail gracefully; zero-out
   dependent tests but let independent ones continue, and surface the failure in
   the summary.
4. **Override** (`REQ016`) – allow `--skip-setup` so the evaluator can still
   run a "cold" assessment when desired.

When the user adds concrete *test* or *plugin* requirements later, those should
focus on *what* is being tested, while the framework requirements in `REQ`
focus on *how* the test engine works.

## Key Take-Aways for Future Work

- Do **not** introduce HL/LL/TEST tiers inside `docs/reqs/`.
- Do **not** add test-specific logic (e.g. "flake8 must report less than 5
  errors") into the framework requirements.
- Keep `REQ` items concise, verifiable, and implementation-agnostic.
- When concrete checks are defined later, place them in a sibling document
  (e.g. `asr/` for Assessments, `job/` for Jobs) and link them upstream to the
  relevant `REQ` items.
- Update this SKILL.md whenever the requirement topology changes.
