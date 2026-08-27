# Quickstart: End-to-End Candidate Code Review Flow

A validation guide proving the feature works end-to-end on the target environment. This is a
run/validation guide — implementation details live in `tasks.md` and the implementation phase.

## Prerequisites

- Raspberry Pi (or arm64 host) running Ubuntu.
- LXD installed and initialized (`lxd init`), with a usable Python base image/profile.
- Python 3.11 available (single language — no JavaScript runtime/tooling required).
- Backend built per repository setup (see `backend/`); the web interface is served by the same
  Python service (feature 005).

## Setup

```bash
# Single Python service (from repo root) — serves the API and the web interface.
cd app
# install deps, initialize SQLite schema, seed an ADMIN and a REVIEWER user,
# and register built-in tests (at least one METRIC and one AI_AGENT).
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
# Open http://127.0.0.1:8000/ in a browser.
```

Reference: API surface in [contracts/openapi.yaml](./contracts/openapi.yaml); test plugin behavior
in [contracts/test-plugin-contract.md](./contracts/test-plugin-contract.md); entities in
[data-model.md](./data-model.md).

## Validation scenarios

Each scenario maps to acceptance criteria in [spec.md](./spec.md).

### 1. Reviewer submits Python code and receives a weighted grade (User Story 1)

1. Sign in as the seeded Reviewer.
2. Upload a valid Python archive with a candidate label.
3. Observe the review enter `RUNNING`, then `COMPLETED` (async).
4. **Expected**: a final grade 0-100, a per-test breakdown (grade, weight, contribution), and an
   aggregated pros/cons list. Confirms FR-001, FR-003, FR-005, FR-006, FR-012.

### 2. Non-Python upload is rejected (User Story 1, edge cases)

1. As the Reviewer, upload a non-Python archive (and separately, an empty/corrupted archive).
2. **Expected**: HTTP 422 with a clear message; no review is created and no container starts.
   Confirms FR-002, FR-016.

### 3. Failure isolation (edge cases)

1. Run an assessment where one test is forced to crash or exceed its timeout.
2. **Expected**: that test shows `FAILED` with grade 0 and a flag; remaining tests still contribute
   and the review completes. Confirms FR-007, SC-004.

### 4. Reviewer overrides weights, grade recomputes instantly (User Story 2)

1. Open a completed review; change one test's weight.
2. **Expected**: final grade updates in under 2 s with no test re-execution; overrides persist and do
   not affect other reviewers' views of the same submission. Confirms FR-009, FR-010, SC-003, SC-007.
3. Set all effective weights to 0.
4. **Expected**: HTTP 422 requiring at least one positive weight. Confirms FR-017.

### 5. Admin configures tests and default weights (User Story 3)

1. Sign in as Admin; set a test's default weight and toggle enabled state.
2. Start a new assessment as Reviewer.
3. **Expected**: only enabled tests run; the new default weight is applied. Confirms FR-008.
4. As a Reviewer, attempt an admin-only config change → **Expected**: HTTP 403. Confirms FR-014.

### 6. AI-agent test contributes to the grade (User Story 5)

1. Run an assessment including the AI-agent test (scoped to its theme).
2. **Expected**: it runs in its own container, returns a 0-100 grade with pros/cons, and folds into
   the weighted mean like any metric test. Confirms FR-004, FR-013, SC-006.

### 7. History persists and is browsable (User Story 4)

1. Complete two assessments; open the history list; reopen each.
2. **Expected**: both appear with candidate, date, and final grade; reopening shows the stored
   breakdown and pros/cons unchanged. Confirms FR-011, SC-005.

## Constitution validation

- **Sandboxing (II)**: verify each test run creates and destroys a container; no execution on host
  (SC-006).
- **Measurable/Transparent (I, IV)**: every displayed grade traces to per-test grades × weights.
- **Portable (V)**: the full flow above runs on the Raspberry Pi / Ubuntu (arm64) instance.
