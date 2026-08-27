# Implementation Plan: Live Review Status with Progress Bar and ETA

**Branch**: `006-live-review-progress` | **Date**: 2026-08-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-live-review-progress/spec.md`

## Summary

While an assessment runs, the review page shows the live status, a progress bar (completed tests /
total enabled tests), and an estimated time remaining — all updated automatically without a manual
refresh. Delivery is a **server-rendered progress fragment re-polled every 2 seconds** by the vendored
htmx helper (no authored JavaScript, consistent with feature 005). Polling stops when the review reaches
a terminal status, at which point the page shows the final grade and per-test breakdown. Progress is
derived from existing data (the review's status/timestamps and its accumulating test results); no
grading, test-set, execution, or role changes.

## Technical Context

**Language/Version**: Python 3.11 (single language; server-rendered UI per feature 005)

**Primary Dependencies**: existing FastAPI + Jinja2; the vendored, non-authored htmx helper (already
present) provides interval polling and fragment swapping — no new dependency

**Storage**: unchanged — progress is derived at read time from the Review, its Job (start time), the set
of enabled Tests (total), and the accumulating TestResults (completed count)

**Testing**: pytest (rendered-fragment + progress-computation tests)

**Target Platform**: Raspberry Pi / Ubuntu (arm64), single self-hosted instance

**Project Type**: Web application — one Python service serving the API and the server-rendered UI

**Performance Goals**: Each poll re-renders a small fragment; a 2-second cadence meets the ≤3s freshness
targets (SC-001/SC-005) with light load on the Pi

**Constraints**: No authored JavaScript (feature 005) — live updates use htmx `hx-trigger="every 2s"`
polling; polling MUST stop at terminal status (FR-001); ETA never negative and shows "estimating…" when
unknown (FR-004); progress must keep advancing on test failure/timeout (FR-007); visible only to the
review's authorized reviewer (FR-009)

**Scale/Scope**: A handful of tests per review; one polling fragment endpoint plus a pure progress
computation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Measurable Assessment | Unchanged | PASS — grading untouched; progress is a derived read |
| II. Sandboxed Execution (NON-NEGOTIABLE) | Unchanged | PASS — no execution path change |
| III. Extensible Test Framework | Unchanged | PASS — no plugin change |
| IV. Weighted, Transparent Grading | Frontend presents the breakdown | PASS — final breakdown still shown; progress adds transparency during the wait |
| V. Portable & Self-Hostable | Modest footprint | PASS — derived reads + a small 2s poll; no new services/dependencies |

**Additional constraint — no authored JavaScript (feature 005)**: PASS — polling is an htmx attribute;
the progress fragment is server-rendered.

**Post-Design Re-check**: See end of Phase 1 — all gates remain PASS; Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/006-live-review-progress/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── progress-fragment.md     # Progress fragment route + progress/ETA contract
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── services/review_progress.py    # NEW: pure progress + ETA computation (completed/total, elapsed→ETA)
│   ├── api/web.py                      # NEW route: GET progress fragment; review-detail page includes it
│   └── templates/fragments/progress.html   # NEW: status + progress bar + ETA; polls itself while running
└── tests/
    ├── unit/test_review_progress.py    # progress/ETA math (non-negative, estimating…, monotonic)
    └── web/test_progress_fragment.py   # fragment rendering, polling stop at terminal, auth
```

**Structure Decision**: Add a pure `review_progress` computation (testable without HTTP) plus one
server-rendered progress fragment that the review-detail page embeds. The fragment carries the htmx
polling attributes and, while the review is pending/running, re-requests itself every 2 seconds; once the
review is terminal it renders the final state and omits the polling trigger (so polling stops) and
signals the page to show the completed breakdown.

## Complexity Tracking

> No constitution violations. Table intentionally empty.
