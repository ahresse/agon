---
description: "Task list for Single-Language (Python) Stack — Eliminate JavaScript"
---

# Tasks: Single-Language (Python) Stack — Eliminate JavaScript

**Input**: Design documents from `/specs/005-python-only-stack/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included (rendered-HTML page tests + htmx fragment tests + a JS guardrail), replacing the
removed Vitest suite, consistent with the project's testing strategy.

**Organization**: Tasks are grouped by user story (US1–US3) to enable independent implementation and
testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US3)
- Include exact file paths in descriptions

## Path Conventions

- Single Python service: `backend/src/`, `backend/tests/` (per plan.md). No `frontend/` after this feature.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the server-side templating dependency and the vendored, non-authored helper asset.

- [X] T001 Add Jinja2 to backend dependencies in backend/pyproject.toml
- [X] T002 [P] Vendor the non-authored helper as a static asset (no build step) at backend/src/static/vendor/htmx.min.js
- [X] T003 [P] Add a shared base Jinja2 template (layout, includes the vendored helper, structured-breakdown-friendly markup) in backend/src/templates/base.html

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Wire templating + static serving into the app and establish the web router, session-aware
page auth, and shared render helpers. **These MUST complete before any page/fragment is built.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Configure Jinja2 templates and mount the static assets directory on the FastAPI app in backend/src/api/main.py
- [X] T005 Create the web router module (HTML pages + fragments) and include it in the app in backend/src/api/web.py
- [X] T006 Implement page-auth helpers: redirect unauthenticated page requests to /login and enforce the existing admin guard for admin pages/fragments in backend/src/api/web_auth.py
- [X] T007 Implement a shared template-render helper (renders full pages and bare fragments from existing read models) in backend/src/api/web_render.py

**Checkpoint**: Templating, static serving, web router, and page auth are ready; pages/fragments can be built.

---

## Phase 3: User Story 1 - Maintainer works in a single language across the whole system (Priority: P1) 🎯 MVP

**Goal**: Every reviewer- and admin-facing capability is delivered server-rendered in Python; the
separate JavaScript client and its toolchain are removed; a guardrail prevents new JS.

**Independent Test**: Inventory the repo — the web interface and backend are one language, no
project-authored JS/TS or JS package/build toolchain exists, and the full app builds and runs without a
JS runtime.

### Tests for User Story 1 ⚠️

- [X] T008 [P] [US1] Guardrail test: fails if any project-authored .js/.ts/.tsx/.jsx or JS package manifest exists (excluding static/vendor/) in backend/tests/meta/test_no_javascript.py
- [X] T009 [P] [US1] Page test: login, upload, history, review-detail, admin-tests, admin-users routes render 200 with expected structure/auth in backend/tests/web/test_pages.py

### Implementation for User Story 1

- [X] T010 [P] [US1] Login page + POST /login (establish session) and POST /logout, with templates, in backend/src/api/web.py and backend/src/templates/login.html
- [X] T011 [P] [US1] Upload page GET/POST /ui/upload (candidate label + archive, reuse existing upload service + rejection messaging) in backend/src/api/web.py and backend/src/templates/upload.html
- [X] T012 [P] [US1] History page GET /ui/reviews (list prior reviews: candidate, date, grade, status) in backend/src/api/web.py and backend/src/templates/history.html
- [X] T013 [US1] Review-detail page GET /ui/reviews/{id} rendering final grade + per-test breakdown (grade, weight, contribution), aggregated pros/cons, and per-test evidence logs in backend/src/api/web.py and backend/src/templates/review_detail.html
- [X] T014 [P] [US1] Admin test-config page GET + POST /ui/admin/tests[/{id}] (enable/disable, default weight; admin-guarded) in backend/src/api/web.py and backend/src/templates/admin_tests.html
- [X] T015 [P] [US1] Admin users page GET/POST /ui/admin/users[/{id}] (list, create, role update; admin-guarded) in backend/src/api/web.py and backend/src/templates/admin_users.html
- [X] T016 [US1] Root route GET / redirects to history or login in backend/src/api/web.py
- [X] T017 [US1] Delete the JavaScript client and its toolchain entirely (frontend/ directory: src, tests, package.json, package-lock.json, vite/tsconfig/vitest configs, index.html)
- [X] T018 [US1] Remove JS-toolchain references from ignore files and project docs (.gitignore Node section as appropriate; README) in .gitignore and README.md

**Checkpoint**: MVP — the whole app is single-language Python, server-rendered, with the JS client removed and a guardrail in place.

---

## Phase 4: User Story 2 - Reviewer uses the web interface with no behavioral regression (Priority: P1)

**Goal**: Interactive behaviors that needed authored JS — instant re-grade on weight change and
expanding a test's evidence log — are preserved as partial, server-driven in-place updates (no full-page
navigation), via the vendored helper.

**Independent Test**: On a completed review, change a weight and see the grade update in place; expand a
test and see its evidence log appear in place; all-zero weights rejected inline; behavior matches the
prior client.

### Tests for User Story 2 ⚠️

- [X] T019 [P] [US2] Fragment test: POST /ui/reviews/{id}/weights returns an updated grade fragment (recomputed, no full page) and 422/inline-message on all-zero in backend/tests/web/test_fragments.py
- [X] T020 [P] [US2] Fragment test: GET /ui/reviews/{id}/tests/{test_id}/log returns the evidence-log fragment with present/empty/no-log states in backend/tests/web/test_fragments.py
- [X] T021 [P] [US2] Parity test: review-detail page shows the same structured breakdown + pros/cons + contributions as the read model in backend/tests/web/test_parity.py

### Implementation for User Story 2

- [X] T022 [US2] Weight-editor form + grade fragment: POST /ui/reviews/{id}/weights applies overrides, recomputes from stored results, swaps the grade/breakdown area in place; reject all-zero inline in backend/src/api/web.py and backend/src/templates/fragments/grade.html
- [X] T023 [US2] Evidence-log fragment: GET /ui/reviews/{id}/tests/{test_id}/log renders the log (present / "No additional evidence" / "No log available") expanded in place in backend/src/api/web.py and backend/src/templates/fragments/evidence_log.html
- [X] T024 [US2] Add htmx attributes to the weight editor and per-test rows in review_detail.html to trigger the fragment swaps (no authored JS) in backend/src/templates/review_detail.html

**Checkpoint**: US1 + US2 — full behavior parity including in-place re-grade and log expansion.

---

## Phase 5: User Story 3 - Operator deploys the single-language stack with a smaller toolchain (Priority: P2)

**Goal**: The one Python service serves both API and web interface; deploy/run requires no JavaScript
runtime, package manager, or bundler.

**Independent Test**: On a clean host, build and run the app end-to-end with zero JS tooling; the
interface is served by the Python service.

### Tests for User Story 3 ⚠️

- [X] T025 [P] [US3] Deploy/serve test: the app serves the web interface (GET / and /static/vendor/htmx.min.js) from the single service with no JS build artifact in backend/tests/web/test_serving.py

### Implementation for User Story 3

- [X] T026 [US3] Update the deploy flow to build/run only the Python service (drop any frontend build/install step) in backend/src/runners/metric_image.md and specs/002-one-command-deploy/quickstart.md references as applicable
- [X] T027 [US3] Update 001 quickstart to describe running the single Python service (remove frontend build/serve steps) in specs/001-code-review-flow/quickstart.md

**Checkpoint**: All user stories independently functional; deployment is JS-toolchain-free.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Consistency, accessibility of the rendered pages, and validation.

- [X] T028 [P] Add a shared error/empty-state partial and wire it into pages (unauthorized, not-found, empty lists) in backend/src/templates/fragments/message.html
- [X] T029 [P] Ensure log/output content renders as inert text in templates (autoescape on; preformatted) across review_detail.html and fragments/evidence_log.html
- [X] T030 Run quickstart.md validation scenarios end-to-end in specs/005-python-only-stack/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phases 3–5)**: All depend on Foundational; US1 is MVP
- **Polish (Phase 6)**: Depends on the desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: After Foundational — delivers all pages + removes the JS client (MVP)
- **US2 (P1)**: After US1's review-detail page exists — adds the in-place fragment interactions
- **US3 (P2)**: After US1 — validates/records JS-free deployment

### Within Each User Story

- Tests written first and expected to fail before implementation
- Templates + routes reuse existing services/read models (no business-logic changes)

### Parallel Opportunities

- Setup: T002 and T003 in parallel
- US1: page tasks T010/T011/T012/T014/T015 edit separate template files and can run in parallel; T013 (review detail) and T016/T017/T018 are sequential-ish (shared web.py / repo-wide)
- US2: fragment tests T019–T021 in parallel; implementation shares web.py/templates (sequential)
- After Foundational, US1 pages can be staffed in parallel; US2 depends on the review-detail page

---

## Parallel Example: User Story 1

```bash
# Tests for US1 together:
Task: "Guardrail no-JS test in backend/tests/meta/test_no_javascript.py"          # T008
Task: "Page render tests in backend/tests/web/test_pages.py"                       # T009

# Independent page templates together:
Task: "Login page in backend/src/templates/login.html"                            # T010
Task: "Upload page in backend/src/templates/upload.html"                           # T011
Task: "History page in backend/src/templates/history.html"                         # T012
Task: "Admin users page in backend/src/templates/admin_users.html"                # T015
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1: Setup (Jinja2 + vendored helper + base template)
2. Phase 2: Foundational (templating/static mount, web router, page auth, render helper)
3. Phase 3: User Story 1 — all pages server-rendered; delete `frontend/`; guardrail
4. **STOP and VALIDATE**: single-language inventory + every page renders and is access-controlled
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → templating ready
2. US1 → single-language server-rendered app (MVP), JS client removed
3. US2 → in-place re-grade + log expand (behavior parity)
4. US3 → JS-toolchain-free deployment validated

---

## Notes

- [P] = different files, no dependencies
- Only project-authored JavaScript/TypeScript and the JS toolchain are forbidden; the vendored
  `static/vendor/htmx.min.js` is a non-authored static asset and is excluded from the guardrail (FR-002/FR-010)
- Interactivity is server-driven: fragments are rendered in Python and swapped in place (FR-005)
- No grading/data/role changes; templates reuse existing services and read models (FR-009)
- Verify tests fail before implementing; commit after each task or logical group
