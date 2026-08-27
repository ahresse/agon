# Implementation Plan: Per-Grade Detail and Evidence Logs in the UI

**Branch**: `004-grade-detail-logs` | **Date**: 2026-08-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-grade-detail-logs/spec.md`

## Summary

Reviewers currently see each test's grade, weight, contribution, and short pros/cons, but not the
underlying evidence that produced the grade. This feature captures a per-test **evidence log** during
each test run, persists it with the test result, returns it wherever a review's detail is retrieved, and
presents it as an expandable, per-test panel (including the failure reason for failed/zero tests). Logs
are captured going forward; results assessed before this feature are labeled "no log available".

Approach: extend the test's assessment output with an optional evidence log, carry it through the
existing execution and result pipeline, persist it alongside the result, expose it in the review-detail
view, and present it as a collapsible per-test panel with safe text rendering and truncation for large
logs. The weighted grading model, test set, and roles are unchanged.

## Technical Context

**Assessment output**: Each test's result gains an optional evidence-log value; tests that do not
produce one yield an empty log. Existing tests keep working unchanged (additive, optional field).

**Storage**: The per-test result record gains an optional evidence-log value. New records
capture it; records created before this feature have no log and are labeled as such.

**Testing**: Automated coverage at the assessment-output, persistence, retrieval, and presentation
levels, plus scenario validation from `quickstart.md`.

**Target environment**: Single self-hosted instance on the project's supported hardware (per the
constitution); footprint stays modest.

**Performance goals**: The review-detail view remains interactive; each evidence log is bounded in size
so the record and the retrieved payload stay small.

**Constraints**: Evidence is produced inside the isolated, disposable execution boundary and read back
over the existing result channel (Constitution II — no new host-execution path); logs are rendered as
inert text (no embedded markup executes); large logs must not break the page.

**Scale/Scope**: Team-scale single instance; a handful of tests per review, each with a bounded log.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Derived from `.specify/memory/constitution.md` v1.0.0:

| Principle | Gate | Status |
|-----------|------|--------|
| I. Measurable Assessment | Evidence must trace the grade to measurable observations | PASS — the log records exactly the observations behind each grade, strengthening measurability |
| II. Sandboxed Execution (NON-NEGOTIABLE) | No new host-execution path | PASS — logs are produced inside the isolated execution boundary and returned via the existing result channel |
| III. Extensible Test Framework | No core change required to add tests | PASS — the evidence log is an optional output field with a safe default; existing tests need no change |
| IV. Weighted, Transparent Grading | Present a structured breakdown + evidence | PASS — this feature deepens transparency by exposing per-test evidence behind the weighted breakdown |
| V. Portable & Self-Hostable | Footprint stays modest | PASS — one optional record field + bounded text; no new services or dependencies |

**Post-Design Re-check**: See end of Phase 1 — all gates remain PASS; Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/004-grade-detail-logs/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── review-detail.md         # Review-detail view: per-test result + log
│   └── test-plugin-log.md       # Test-output contract extension (log field)
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Change surface (behavioral)

The evidence log is threaded through the existing pipeline as a single optional value:

1. **Assessment output** — a test may emit an evidence log; absence yields an empty log.
2. **Execution boundary** — the log is carried back with the rest of the result; the failure path records
   the error/timeout/no-input reason as the log.
3. **Persistence** — the log is stored with the test result (optional), bounded in size.
4. **Retrieval** — the review-detail view includes the log per test result.
5. **Presentation** — an expandable per-test panel shows the log as inert, scrollable text, with clear
   "no additional evidence" vs "no log available" indications.

**Structure Decision**: The change is a thin optional value threaded through the existing result flow
plus a presentation affordance. Built-in tests are updated to populate the log with their concrete
findings/tool output; the failure path records the failure reason.

## Complexity Tracking

> No constitution violations. Table intentionally empty.
