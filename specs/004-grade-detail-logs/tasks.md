---
description: "Task list for Per-Grade Detail and Evidence Logs in the UI"
---

# Tasks: Per-Grade Detail and Evidence Logs in the UI

**Input**: Design documents from `/specs/004-grade-detail-logs/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included (unit + contract + integration + component), consistent with the project's existing
testing strategy and the constitution's measurability gates.

**Organization**: Tasks are grouped by user story (US1–US3) to enable independent implementation and
testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US3)
- Include exact file paths in descriptions

## Path Conventions

- Web app: `backend/src/`, `backend/tests/`, `frontend/src/`, `frontend/tests/` (per plan.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project scaffolding; this feature extends existing pipeline files. Establish the
size-cap constant used across capture and truncation.

- [ ] T001 Add the evidence-log size cap constant (262144 bytes = 256 KiB) and a `truncate_log(text)` helper (appends `… [log truncated]`) in backend/src/tests_plugins/log_util.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Thread the optional `log` value through the contract, execution boundary, runner result,
storage, and read model. **These MUST complete before any user story surfaces a log.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Extend PluginOutput with an optional `log: str = ""` field (kept backward-compatible) in backend/src/tests_plugins/registry.py
- [ ] T003 Add a nullable `log` column to the TestResult model in backend/src/models/test_result.py
- [ ] T004 Add an idempotent additive migration that adds the `log` column to `test_results` if missing, run at startup, in backend/src/db.py
- [ ] T005 Add `log` to ExecutedResult and capture it from PluginOutput; on crash/timeout compose the log as a sanitized reason first then the full raw error beneath; truncate via truncate_log in backend/src/runners/test_runner.py
- [ ] T006 Emit `log` in the in-container JSON result in backend/src/runners/in_container.py
- [ ] T007 Parse `log` from the container result (default empty when absent) in backend/src/runners/lxd_backend.py
- [ ] T008 Persist `log` on each TestResult when recording results in backend/src/services/review_service.py
- [ ] T009 Add `log: str | None` to TestResultOut in backend/src/api/schemas.py
- [ ] T010 Include each result's `log` in the assembled review detail in backend/src/api/review_detail.py
- [ ] T011 [P] Add `log: string | null` to the TestResult type in frontend/src/services/apiClient.ts

**Checkpoint**: Evidence logs are captured, stored, and returned end-to-end; UI wiring can begin.

---

## Phase 3: User Story 1 - Reviewer inspects how a single test's grade was derived (Priority: P1) 🎯 MVP

**Goal**: A reviewer can expand any individual test in a completed review to see its detailed findings
and captured evidence log (a focused excerpt) alongside its grade and weight; other tests stay collapsed.

**Independent Test**: Upload a submission with a known issue; open the review, expand one test, and
confirm its evidence log names the concrete finding and corresponds to the grade while other tests
remain collapsed.

### Tests for User Story 1 ⚠️

- [ ] T012 [P] [US1] Contract test: GET /reviews/{id} returns a `log` field per result in backend/tests/contract/test_review_detail_log.py
- [ ] T013 [P] [US1] Integration test: passing test's log is a focused excerpt of findings and folds into the persisted result in backend/tests/integration/test_evidence_log.py
- [ ] T014 [P] [US1] Component test: expanding one test reveals its log and keeps others collapsed in frontend/tests/GradeBreakdownLog.test.tsx

### Implementation for User Story 1

- [ ] T015 [P] [US1] Populate `log` with a focused findings excerpt (issue + location) in the ruff, radon, stdlib-idioms, mypy, bandit, black, and git-history plugins in backend/src/tests_plugins/quality/*.py
- [ ] T016 [US1] Add an expandable per-test evidence panel (grade, weight, contribution, pros/cons, log) rendering the log as inert, scrollable preformatted text with independent expand/collapse in frontend/src/components/GradeBreakdown.tsx
- [ ] T017 [US1] Ensure the breakdown makes each test's contribution traceable alongside its evidence (FR-011) in frontend/src/components/GradeBreakdown.tsx

**Checkpoint**: MVP — a reviewer can trace any grade to its concrete evidence log.

---

## Phase 4: User Story 2 - Reviewer reviews logs for a failed or zero-scored test (Priority: P2)

**Goal**: For a failed, timed-out, or zero-scored test, the log leads with a sanitized reason and
includes the full raw error beneath, or states that no assessable input was found.

**Independent Test**: Produce a review with a failed/timed-out test and a no-input test; open each and
confirm the log shows the sanitized reason (then raw error) / the no-input message rather than an empty
result.

### Tests for User Story 2 ⚠️

- [ ] T018 [P] [US2] Unit test: test_runner failure path yields a log with sanitized reason first then raw error, grade 0, FAILED in backend/tests/unit/test_runner_log.py
- [ ] T019 [P] [US2] Integration test: no-assessable-input test records a "no assessable input" log in backend/tests/integration/test_failed_log.py

### Implementation for User Story 2

- [ ] T020 [US2] Ensure no-assessable-input branches in the quality plugins set an explanatory `log` (not empty) in backend/src/tests_plugins/quality/*.py
- [ ] T021 [US2] Render failed/zero-test logs (sanitized reason + raw error) clearly in the evidence panel in frontend/src/components/GradeBreakdown.tsx

**Checkpoint**: US1 + US2 both work independently.

---

## Phase 5: User Story 3 - Reviewer retains access to grade details for past reviews (Priority: P3)

**Goal**: Reopening a completed review from history shows the same per-test details and evidence logs
exactly as at assessment time; pre-feature results show "No log available".

**Independent Test**: Complete a review, reopen it later from history, expand a test, and confirm the
stored log is identical; open a pre-feature review and confirm the "No log available" indication.

### Tests for User Story 3 ⚠️

- [ ] T022 [P] [US3] Integration test: stored log is byte-identical on reopen (history fidelity) in backend/tests/integration/test_log_history.py
- [ ] T023 [P] [US3] Component test: null log shows "No log available"; empty log shows "No additional evidence" in frontend/tests/GradeBreakdownLog.test.tsx

### Implementation for User Story 3

- [ ] T024 [US3] Distinguish null (no log captured) from empty (ran, no evidence) in the evidence panel with the correct labels in frontend/src/components/GradeBreakdown.tsx

**Checkpoint**: All user stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cross-cutting quality, safety, and documentation.

- [ ] T025 [P] Unit test: truncate_log caps at 256 KiB and appends the marker (boundary + over-cap) in backend/tests/unit/test_log_util.py
- [ ] T026 [P] Component test: control-character/markup log content renders inert (no page alteration) and large logs stay scrollable in frontend/tests/GradeBreakdownLog.test.tsx
- [ ] T027 [P] Update the 001 test-plugin contract and OpenAPI to note the optional `log` field in specs/001-code-review-flow/contracts/openapi.yaml
- [ ] T028 Run quickstart.md validation scenarios end-to-end in specs/004-grade-detail-logs/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup (T001) — BLOCKS all user stories
- **User Stories (Phases 3–5)**: All depend on Foundational; US1 is MVP
- **Polish (Phase 6)**: Depends on the desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: After Foundational — no dependency on other stories (MVP)
- **US2 (P2)**: After Foundational — reuses the same log surface; failure path independently testable
- **US3 (P3)**: After Foundational — relies on US1's persisted log; adds history/no-log labeling

### Within Each User Story

- Tests written first and expected to fail before implementation
- Contract/model/runner changes (Foundational) → plugin log population → UI panel

### Parallel Opportunities

- Foundational: T011 (frontend type) runs in parallel with backend T002–T010
- All `[P]`-marked tests within a story run in parallel
- T015 edits multiple plugin files that can be split across contributors
- After Foundational, US1–US3 can be staffed in parallel (US3 UI labels depend on US1 panel)

---

## Parallel Example: User Story 1

```bash
# Tests for US1 together:
Task: "Contract test /reviews/{id} log field in backend/tests/contract/test_review_detail_log.py"   # T012
Task: "Integration test passing-test excerpt log in backend/tests/integration/test_evidence_log.py"  # T013
Task: "Component test expand-one-test in frontend/tests/GradeBreakdownLog.test.tsx"                   # T014
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup (T001)
2. Phase 2: Foundational (T002–T011) — threads the log end-to-end
3. Phase 3: User Story 1 — plugins populate logs; UI shows the expandable evidence panel
4. **STOP and VALIDATE**: expand a test and read its evidence log
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → log captured/stored/returned
2. US1 → MVP (inspect evidence behind any grade)
3. US2 → failure/zero logs (sanitized reason + raw error)
4. US3 → history fidelity + no-log labeling

---

## Notes

- [P] = different files, no dependencies
- The `log` field is additive/optional; existing plugins and pre-feature results keep working (Constitution III)
- Logs are produced inside the container and returned via the existing result channel (Constitution II)
- Grading is unchanged; the log is evidence, never a grading input (Constitution IV)
- Verify tests fail before implementing; commit after each task or logical group
