---
description: "Task list for End-to-End Candidate Code Review Flow"
---

# Tasks: End-to-End Candidate Code Review Flow

**Input**: Design documents from `/specs/001-code-review-flow/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included (contract + integration tests per user story), consistent with the plan's
testing strategy and the constitution's measurability/isolation gates.

**Organization**: Tasks are grouped by user story (US1–US5) to enable independent implementation
and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Include exact file paths in descriptions

## Path Conventions

- Web app: `backend/src/`, `backend/tests/`, `frontend/src/`, `frontend/tests/` (per plan.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create backend/ and frontend/ directory structure per plan.md (models, services, runners, tests_plugins, api; components, pages, services)
- [X] T002 Initialize Python 3.11 backend project with FastAPI, Uvicorn, SQLAlchemy, Pydantic, pylxd in backend/pyproject.toml
- [X] T003 Initialize React + TypeScript + Vite frontend project in frontend/package.json
- [X] T004 [P] Configure backend linting/formatting (ruff + black) in backend/pyproject.toml
- [X] T005 [P] Configure frontend linting/formatting (eslint + prettier) in frontend/.eslintrc and frontend/.prettierrc
- [X] T006 [P] Configure pytest in backend/pyproject.toml and Vitest in frontend/vitest.config.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Configure SQLAlchemy engine + SQLite session management in backend/src/db.py
- [X] T008 Define base ORM setup and migrations/schema bootstrap in backend/src/models/base.py
- [X] T009 [P] Create User model with role enum (REVIEWER/ADMIN) in backend/src/models/user.py
- [X] T010 [P] Create Test model (key, name, type, theme, enabled, default_weight) in backend/src/models/test.py
- [X] T011 [P] Create Submission model in backend/src/models/submission.py
- [X] T012 [P] Create Review model with status enum in backend/src/models/review.py
- [X] T013 [P] Create TestResult model in backend/src/models/test_result.py
- [X] T014 [P] Create WeightConfiguration model in backend/src/models/weight_configuration.py
- [X] T015 Implement session-based authentication + role authorization dependency in backend/src/api/auth_deps.py
- [X] T016 Setup FastAPI app, routing, error handling, and structured logging in backend/src/api/main.py
- [X] T017 Implement environment/config management (DB path, container profile, AI provider) in backend/src/config.py
- [X] T018 Implement LXC/LXD container runner (create, inject source, timeout, read result, destroy) in backend/src/runners/container_runner.py
- [X] T019 Define/provision metric container image/profile bundling ruff, radon, mypy, bandit, black (arm64) and document it in backend/src/runners/metric_image.md
- [X] T020 Define test plugin interface + registry (weight-in/grade-out) in backend/src/tests_plugins/registry.py
- [X] T021 Implement in-process SQLite-backed job queue with worker pool and status lifecycle (PENDING→RUNNING→COMPLETED/FAILED) in backend/src/services/job_queue.py
- [X] T022 [P] Seed script: default ADMIN + REVIEWER users and built-in tests — register the 6 Python quality METRIC plugins (lint_ruff, complexity_radon, stdlib_idioms, type_check_mypy, security_bandit, formatting_black) with default weights + ≥1 AI_AGENT test in backend/src/seed.py
- [X] T023 [P] Setup frontend API client typed from contracts/openapi.yaml in frontend/src/services/apiClient.ts
- [X] T024 [P] Implement login page and session handling in frontend/src/pages/Login.tsx
- [X] T025 [P] Contract/integration test: authentication + Reviewer/Admin role distinction (FR-015) in backend/tests/contract/test_auth.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Reviewer submits code and receives a weighted grade (Priority: P1) 🎯 MVP

**Goal**: A reviewer uploads a Python submission, tests run async in containers, and a final
weighted grade with per-test breakdown and pros/cons is displayed.

**Independent Test**: Upload a valid Python archive; confirm a final 0-100 grade, per-test
breakdown, and pros/cons appear; confirm non-Python uploads are rejected.

### Tests for User Story 1 ⚠️

- [X] T026 [P] [US1] Contract test POST /submissions (202 + 422 rejection) in backend/tests/contract/test_submissions.py
- [X] T027 [P] [US1] Contract test GET /reviews/{id} breakdown shape in backend/tests/contract/test_review_detail.py
- [X] T028 [P] [US1] Plugin-contract conformance (grade 0-100, timeout→FAILED, no host execution) in backend/tests/contract/test_plugin_contract.py
- [X] T029 [P] [US1] Conformance test for the 6 Python quality metric plugins (deterministic 0-100 grade + non-empty pros/cons on fixture code) in backend/tests/contract/test_quality_plugins.py
- [X] T030 [P] [US1] Integration test upload→run→grade happy path in backend/tests/integration/test_review_flow.py
- [X] T031 [P] [US1] Integration test non-Python/empty rejection in backend/tests/integration/test_upload_rejection.py

### Implementation for User Story 1

- [X] T032 [P] [US1] Implement language detection (accept Python, reject others/empty/corrupt) in backend/src/services/language_detection.py
- [X] T033 [P] [US1] Implement shared metric-plugin helpers (raw-signal → 0-100 normalization, pros/cons builders, subprocess+JSON runner) in backend/src/tests_plugins/quality/common.py
- [X] T034 [P] [US1] Implement lint_ruff plugin (ruff check JSON → grade + violation pros/cons) in backend/src/tests_plugins/quality/lint_ruff.py
- [X] T035 [P] [US1] Implement complexity_radon plugin (radon cc + mi → grade + complex-function cons) in backend/src/tests_plugins/quality/complexity_radon.py
- [X] T036 [P] [US1] Implement stdlib_idioms plugin (AST idiom vs anti-pattern analysis → grade + evidence) in backend/src/tests_plugins/quality/stdlib_idioms.py
- [X] T037 [P] [US1] Implement type_check_mypy plugin (mypy errors + annotation coverage → grade) in backend/src/tests_plugins/quality/type_check_mypy.py
- [X] T038 [P] [US1] Implement security_bandit plugin (bandit JSON severity-weighted → grade + issue cons) in backend/src/tests_plugins/quality/security_bandit.py
- [X] T039 [P] [US1] Implement formatting_black plugin (black --check + docstring coverage → grade) in backend/src/tests_plugins/quality/formatting_black.py
- [X] T040 [US1] Implement grading service (weighted mean, failed=0 retains weight) in backend/src/services/grading.py
- [X] T041 [US1] Implement scheduling service (enqueue enabled tests per review onto the job queue) in backend/src/services/scheduler.py
- [X] T042 [US1] Implement submissions router (upload, detect, create Submission+Review, dispatch async via scheduler/job queue) in backend/src/api/submissions.py
- [X] T043 [US1] Implement reviews detail router GET /reviews/{id} (breakdown + aggregated pros/cons) in backend/src/api/reviews_detail.py
- [X] T044 [US1] Wire test runner to execute plugins in the metric container via the job queue and persist TestResult; failure isolation (FR-007) in backend/src/runners/test_runner.py
- [X] T045 [P] [US1] Build Upload page (candidate label + archive) in frontend/src/pages/Upload.tsx
- [X] T046 [P] [US1] Build Review detail page with grade breakdown + pros/cons panel in frontend/src/pages/ReviewDetail.tsx
- [X] T047 [P] [US1] Build grade breakdown + pros/cons components in frontend/src/components/GradeBreakdown.tsx
- [X] T048 [US1] Add validation, error messages, and logging for upload/assessment in backend/src/api/submissions.py

**Checkpoint**: MVP — a reviewer can upload Python code and get an explainable weighted grade.

---

## Phase 4: User Story 2 - Reviewer overrides weights and re-grades instantly (Priority: P2)

**Goal**: Reviewer changes per-review weights; final grade recomputes instantly from stored
results without re-running tests; overrides isolated per reviewer.

**Independent Test**: Change a weight on a completed review; grade updates <2s with no re-run;
zero-weight case rejected.

### Tests for User Story 2 ⚠️

- [X] T049 [P] [US2] Contract test PUT /reviews/{id}/weights (200 recompute, 422 all-zero) in backend/tests/contract/test_weights.py
- [X] T050 [P] [US2] Integration test weight override recompute without re-execution, asserting recompute completes < 2s (SC-003), in backend/tests/integration/test_weight_override.py
- [X] T051 [P] [US2] Integration test per-reviewer override isolation (SC-007) in backend/tests/integration/test_override_isolation.py

### Implementation for User Story 2

- [X] T052 [US2] Implement effective-weight resolution (override else default) in backend/src/services/grading.py
- [X] T053 [US2] Implement reviews weights router PUT /reviews/{id}/weights (apply overrides, recompute, enforce FR-017) in backend/src/api/reviews_weights.py
- [X] T054 [P] [US2] Build per-review weight editor with instant recompute in frontend/src/components/WeightEditor.tsx
- [X] T055 [US2] Integrate weight editor into Review detail page in frontend/src/pages/ReviewDetail.tsx

**Checkpoint**: US1 + US2 both work independently.

---

## Phase 5: User Story 3 - Admin configures tests and default weights (Priority: P2)

**Goal**: Admin enables/disables tests and sets global default weights; only enabled tests run;
config restricted to admins.

**Independent Test**: As admin set a default weight/toggle; new assessment reflects it; reviewer
config attempt returns 403.

### Tests for User Story 3 ⚠️

- [X] T056 [P] [US3] Contract test PUT /admin/tests/{id} (200 admin, 403 reviewer) in backend/tests/contract/test_admin_tests.py
- [X] T057 [P] [US3] Integration test default weight applied + disabled test excluded in backend/tests/integration/test_admin_config.py
- [X] T058 [P] [US3] Contract test admin user-management (200 admin, 403 reviewer) in backend/tests/contract/test_admin_users.py

### Implementation for User Story 3

- [X] T059 [US3] Implement tests router GET /tests and admin PUT /admin/tests/{id} with role guard in backend/src/api/tests.py
- [X] T060 [US3] Implement admin user-management API (create/list/update users, role assignment, admin-only guard) in backend/src/api/users.py
- [X] T061 [P] [US3] Build Admin test-config page (enable/disable, default weight for each quality metric) in frontend/src/pages/AdminConfig.tsx
- [X] T062 [P] [US3] Build Admin user-management page (create/list users, assign roles) in frontend/src/pages/AdminUsers.tsx

**Checkpoint**: US1–US3 independently functional.

---

## Phase 6: User Story 4 - Reviewer browses past reviews (Priority: P3)

**Goal**: History view lists completed reviews and reopens stored breakdowns unchanged.

**Independent Test**: Complete two assessments; both appear in history and reopen with intact
breakdown and pros/cons.

### Tests for User Story 4 ⚠️

- [X] T063 [P] [US4] Contract test GET /reviews list in backend/tests/contract/test_reviews_list.py
- [X] T064 [P] [US4] Integration test history persistence + fidelity (SC-005) in backend/tests/integration/test_history.py

### Implementation for User Story 4

- [X] T065 [US4] Implement reviews list router GET /reviews (list summaries for current reviewer, including FAILED reviews) in backend/src/api/reviews_list.py
- [X] T066 [P] [US4] Build History page (list + open) in frontend/src/pages/History.tsx

**Checkpoint**: US1–US4 independently functional.

---

## Phase 7: User Story 5 - AI-agent test contributes to the grade (Priority: P3)

**Goal**: A containerized AI-agent test (scoped to a theme) returns a 0-100 grade + pros/cons and
folds into the weighted mean identically to metric tests.

**Independent Test**: Run an assessment including the AI-agent test; confirm containerized run,
0-100 grade with pros/cons, and inclusion in the weighted mean.

### Tests for User Story 5 ⚠️

- [X] T067 [P] [US5] Integration test AI-agent test runs containerized and folds into grade (FR-013, SC-006) in backend/tests/integration/test_ai_agent.py

### Implementation for User Story 5

- [X] T068 [P] [US5] Implement pluggable AI provider interface in backend/src/tests_plugins/ai_provider.py
- [X] T069 [US5] Implement AI-agent test plugin (theme-scoped, in-container provider call) in backend/src/tests_plugins/ai_agent_example.py

**Checkpoint**: All user stories independently functional.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple user stories

- [X] T070 [P] Add unit tests for grading math and effective weights in backend/tests/unit/test_grading.py
- [X] T071 [P] Add unit tests for language detection edge cases in backend/tests/unit/test_language_detection.py
- [X] T072 [P] Add unit tests for job queue status transitions in backend/tests/unit/test_job_queue.py
- [X] T073 [P] Add unit tests for quality-metric grade normalization (boundary + empty-input cases) in backend/tests/unit/test_quality_normalization.py
- [X] T074 [P] Performance test: weight-change re-grade completes < 2s (SC-003) in backend/tests/integration/test_regrade_perf.py
- [X] T075 Security hardening: enforce role guards, input validation, container isolation review
- [X] T076 [P] Add frontend component tests for breakdown/weight editor in frontend/tests/
- [X] T077 Run quickstart.md validation scenarios end-to-end on arm64/Ubuntu

---

## Phase 9: Archive Format Amendment — accept .tar.gz uploads (FR-001)

**Purpose**: Broaden the upload flow to accept zip and gzip-tar archives, with host-safe extraction
(reject path traversal, absolute paths, and symlinks). Amends FR-001 and its edge cases.

- [X] T078 [US1] Implement format-detecting archive extraction (zip + tar.gz/tgz/tar) with zip-slip/tar-slip, absolute-path, and symlink rejection plus max-size/member-count guards in backend/src/services/archive_extraction.py
- [X] T079 [US1] Wire submissions router to the new extractor; map unsupported/corrupted/unsafe archives to 422 in backend/src/api/submissions.py
- [X] T080 [P] [US1] Extend contract test: .tar.gz + .tgz happy path and malformed-gzip 422 in backend/tests/contract/test_submissions.py
- [X] T081 [P] [US1] Add extraction safety unit tests (traversal, absolute path, symlink, size cap) in backend/tests/unit/test_archive_extraction.py
- [X] T082 [P] [US1] Update upload description (accepted formats) in specs/001-code-review-flow/contracts/openapi.yaml

---

## Phase 10: LXD Execution Backend (Constitution II — real container isolation)

**Purpose**: Provide the production containerized execution path referenced by `LXDRunner`, so tests
run inside disposable LXD containers on the host (never on the host process).

- [X] T083 [US1] Implement in-container plugin entrypoint (register plugins, run one, emit JSON result) in backend/src/runners/in_container.py
- [X] T084 [US1] Implement LXD backend (launch ephemeral container, push src+submission, exec entrypoint under timeout, parse result, force-delete) in backend/src/runners/lxd_backend.py
- [X] T085 [P] [US1] Add mocked-CLI unit tests for the LXD lifecycle and result parsing in backend/tests/unit/test_lxd_backend.py
- [X] T086 [US1] Add LXD image provisioning script (Python 3.11 + pinned toolchain) matching metric_image.md in backend/src/runners/provision_image.sh
- [X] T087 [US1] Add image-availability preflight + actionable errors (missing image / missing lxc / local-runner hint) in backend/src/runners/lxd_backend.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phases 3–7)**: All depend on Foundational; US1 is MVP
- **Polish (Phase 8)**: Depends on desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: After Foundational — no dependency on other stories (MVP)
- **US2 (P2)**: After Foundational — builds on US1's stored results but independently testable
- **US3 (P2)**: After Foundational — independent; affects which tests run
- **US4 (P3)**: After Foundational — reads persisted reviews from US1
- **US5 (P3)**: After Foundational — reuses US1 runner/grading; adds AI provider

### Within Each User Story

- Tests written first and failing before implementation
- Models → services → endpoints → integration → UI

### Parallel Opportunities

- Setup tasks marked [P] run in parallel
- Foundational model tasks (T009–T014) run in parallel; T022/T023/T024/T025 run in parallel
- All test tasks within a story marked [P] run in parallel
- The 6 Python quality metric plugins (T034–T039) are independent files and run in parallel
- After Foundational, US1–US5 can be staffed in parallel

---

## Parallel Example: User Story 1

```bash
# Tests for US1 together:
Task: "Contract test POST /submissions in backend/tests/contract/test_submissions.py"      # T026
Task: "Contract test GET /reviews/{id} in backend/tests/contract/test_review_detail.py"    # T027
Task: "Integration test upload→run→grade in backend/tests/integration/test_review_flow.py" # T030

# Python quality metric plugins together (independent files):
Task: "lint_ruff plugin in backend/src/tests_plugins/quality/lint_ruff.py"                  # T034
Task: "complexity_radon plugin in backend/src/tests_plugins/quality/complexity_radon.py"    # T035
Task: "stdlib_idioms plugin in backend/src/tests_plugins/quality/stdlib_idioms.py"          # T036
Task: "type_check_mypy plugin in backend/src/tests_plugins/quality/type_check_mypy.py"      # T037
Task: "security_bandit plugin in backend/src/tests_plugins/quality/security_bandit.py"      # T038
Task: "formatting_black plugin in backend/src/tests_plugins/quality/formatting_black.py"     # T039
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup
2. Phase 2: Foundational (CRITICAL — blocks all stories)
3. Phase 3: User Story 1
4. **STOP and VALIDATE**: Test US1 independently (upload → weighted grade + breakdown)
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US1 → MVP (upload to graded review)
3. US2 → custom weights + instant re-grade
4. US3 → admin test/weight configuration
5. US4 → review history
6. US5 → AI-agent test

---

## Notes

- [P] = different files, no dependencies
- [Story] label maps each task to its user story for traceability
- Every test execution path (US1 runner, US5 AI agent) MUST run in LXC/LXD containers (Constitution II)
- Verify tests fail before implementing
- Commit after each task or logical group
