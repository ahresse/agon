---
description: "Task list for Live Review Status with Progress Bar and ETA"
---

# Tasks: Live Review Status with Progress Bar and ETA

**Input**: Design documents from `/specs/006-live-review-progress/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included (unit progress/ETA math + web fragment tests), consistent with the project's testing
strategy.

**Organization**: Tasks are grouped by user story (US1–US3) to enable independent implementation and
testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US3)
- Include exact file paths in descriptions

## Path Conventions

- Single Python service: `backend/src/`, `backend/tests/` (per plan.md). Server-rendered UI, no authored JS.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new dependencies (htmx + Jinja2 already present). Establish the poll-interval constant.

- [X] T001 Add the progress poll-interval constant (2 seconds) referenced by the fragment in backend/src/config.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The pure progress/ETA computation that every user story reads. **MUST complete before the
fragment/UI is built.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Implement pure progress computation (status, total enabled tests, completed test results, fraction, is_terminal) and ETA (`max(0, elapsed/completed × remaining)`, `None` when no test completed, 0 when terminal) using Job.started_at→Review.created_at for elapsed, in backend/src/services/review_progress.py

**Checkpoint**: Progress/ETA are computable from existing data; fragment + UI can be built.

---

## Phase 3: User Story 1 - Reviewer watches an assessment progress live (Priority: P1) 🎯 MVP

**Goal**: The review page shows live status + a progress bar (completed/total) + an ETA, updating every
2 seconds without a refresh, and auto-finalizes to the grade + breakdown when done.

**Independent Test**: Start an assessment, stay on the review page without refreshing, and confirm the
status, progress bar fill, and ETA update as tests complete and the final result appears automatically.

### Tests for User Story 1 ⚠️

- [X] T003 [P] [US1] Unit test: progress fraction = completed/total (failures count as completed); is_terminal true for COMPLETED/FAILED in backend/tests/unit/test_review_progress.py
- [X] T004 [P] [US1] Web test: GET /ui/reviews/{id}/progress renders status + progress bar; while running includes the 2s poll trigger; when terminal omits the trigger and shows the final result in backend/tests/web/test_progress_fragment.py

### Implementation for User Story 1

- [X] T005 [US1] Implement GET /ui/reviews/{id}/progress fragment route (owner-only, reuses page auth) computing progress via review_progress in backend/src/api/web.py
- [X] T006 [US1] Create the progress fragment template: status text, progress bar (fill = completed/total), ETA; while running self-polls via hx-get + hx-trigger="every 2s" + hx-swap="outerHTML"; when terminal omits the poll trigger and reveals the final grade + breakdown in backend/src/templates/fragments/progress.html
- [X] T007 [US1] Embed the progress fragment in the review-detail page so a pending/running review shows live progress and a terminal review shows the stored breakdown in backend/src/templates/review_detail.html

**Checkpoint**: MVP — live status + progress bar + ETA that auto-finalizes, no authored JavaScript.

---

## Phase 4: User Story 2 - Reviewer sees an accurate, stabilizing estimate (Priority: P2)

**Goal**: The ETA is trustworthy — non-negative, "estimating…" before any test finishes, and trending
toward zero as tests complete.

**Independent Test**: Run an assessment with several tests; confirm the ETA shows "estimating…" first,
then a non-negative value that decreases overall and resolves to zero/"finishing" at the end.

### Tests for User Story 2 ⚠️

- [X] T008 [P] [US2] Unit test: ETA is None (→ "estimating…") when completed=0; non-negative always; decreases as completed grows for fixed elapsed; 0 when terminal in backend/tests/unit/test_review_progress.py

### Implementation for User Story 2

- [X] T009 [US2] Render the ETA in the fragment as "estimating…" when None, a friendly duration otherwise, and "finishing" at ~0 while running in backend/src/templates/fragments/progress.html

**Checkpoint**: US1 + US2 — live progress with a sensible, stabilizing ETA.

---

## Phase 5: User Story 3 - Reviewer returns to a still-running review and resumes live updates (Priority: P3)

**Goal**: Reopening a running review immediately shows current progress/ETA and resumes polling; a
review finished while away shows the final result directly.

**Independent Test**: Start an assessment, leave, reopen while running → current progress shows and keeps
updating; reopen after completion → final result only, no progress bar/ETA.

### Tests for User Story 3 ⚠️

- [X] T010 [P] [US3] Web test: reopening a running review renders current progress on first request and includes the poll trigger; an already-completed review renders the final result with no progress bar/ETA/trigger in backend/tests/web/test_progress_fragment.py

### Implementation for User Story 3

- [X] T011 [US3] Ensure the fragment is fully stateless/current on every request (no cached progress) so reopen resumes live and terminal reviews skip the in-progress UI in backend/src/api/web.py

**Checkpoint**: All user stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Robustness, access control, and validation.

- [X] T012 [P] Web test: non-owner request to /ui/reviews/{id}/progress is denied/not-found (FR-009) in backend/tests/web/test_progress_fragment.py
- [X] T013 [P] Unit test: total=0 edge (no enabled tests) yields fraction 1.0 and no negative/NaN ETA in backend/tests/unit/test_review_progress.py
- [X] T014 Run quickstart.md validation scenarios end-to-end in specs/006-live-review-progress/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories (progress computation)
- **User Stories (Phases 3–5)**: All depend on Foundational; US1 is MVP
- **Polish (Phase 6)**: Depends on the desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: After Foundational — delivers the fragment, live poll, and auto-finalize (MVP)
- **US2 (P2)**: After US1's fragment exists — refines the ETA presentation
- **US3 (P3)**: After US1 — relies on the fragment being stateless/current for resume-on-reopen

### Within Each User Story

- Tests written first and expected to fail before implementation
- Pure computation (Foundational) → fragment route → template → page embed

### Parallel Opportunities

- Unit tests (T003, T008, T013) target the same test file but distinct cases; the web tests (T004, T010,
  T012) target the same web-test file — group by file, run story test-writing in parallel where files differ
- The progress computation (T002) is independent of template work and unblocks everything

---

## Parallel Example: User Story 1

```bash
# Tests for US1 (write first):
Task: "Unit progress fraction/terminal in backend/tests/unit/test_review_progress.py"     # T003
Task: "Web progress fragment render + poll-stop in backend/tests/web/test_progress_fragment.py"  # T004
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1: Setup (poll-interval constant)
2. Phase 2: Foundational (progress/ETA computation)
3. Phase 3: User Story 1 — fragment route + template + page embed (live poll, auto-finalize)
4. **STOP and VALIDATE**: watch status/progress/ETA update and the result appear automatically
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → progress computable
2. US1 → live status + progress bar + ETA (MVP)
3. US2 → stabilized, non-negative ETA with "estimating…"
4. US3 → resume-on-reopen + terminal-only final result

---

## Notes

- [P] = different files, no dependencies
- Live updates are htmx interval polling of a server-rendered fragment (2s) — no authored JavaScript (feature 005)
- Progress is derived (completed test results / total enabled tests); no schema change
- Failed/timed-out tests count as completed so the bar never stalls (FR-007)
- Polling stops once the review is terminal (FR-001/FR-005/FR-010)
- Verify tests fail before implementing; commit after each task or logical group
