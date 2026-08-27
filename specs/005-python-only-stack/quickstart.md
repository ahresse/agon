# Quickstart: Single-Language (Python) Stack — Eliminate JavaScript

Validation guide proving the whole system runs in one language (Python) with no project-authored
JavaScript, and that the server-rendered web interface preserves existing behavior. Maps to acceptance
criteria in [spec.md](./spec.md); see [contracts/web-ui-routes.md](./contracts/web-ui-routes.md).

## Prerequisites

- The Python application (single service) built and runnable per the project setup.
- No JavaScript runtime, package manager, or bundler installed or required.

## Setup

```bash
# From repo root — one language, one service:
cd app
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
python -m src.seed
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
# Open http://127.0.0.1:8000/ in a browser.
```

## Validation scenarios

### 1. Single-language guarantee (User Story 1, SC-001/SC-002)

1. Inventory the repository for project-authored `.js`/`.ts`/`.tsx`/`.jsx` files and JS package
   manifests (excluding the vendored `static/vendor/` asset).
2. **Expected**: none exist; the `frontend/` project is gone. The app builds and runs with no JS runtime,
   package manager, or bundler. Confirms FR-001, FR-002, FR-003, FR-007, FR-011.

### 2. No behavioral regression — reviewer flow (User Story 2, SC-003)

1. Sign in; upload a valid submission; open the completed review.
2. **Expected**: the review-detail page shows the final weighted grade, per-test breakdown (grade,
   weight, contribution), aggregated pros/cons, and expandable evidence logs — equivalent to before.
   Confirms FR-004.
3. Upload a non-Python/unsafe archive → **Expected**: rejected with the same clear messaging.

### 3. Instant re-grade in place (User Story 2, FR-005 clarified)

1. On a completed review, change a test's weight and submit.
2. **Expected**: the grade area re-renders in place (partial, server-driven update) with the recomputed
   grade — no full-page navigation. Setting all weights to zero shows an inline rejection.

### 4. Evidence log expand in place (FR-005)

1. Expand a test's evidence log.
2. **Expected**: the log fragment appears in place; present/empty/no-log states render correctly.

### 5. Admin capabilities (User Story 1)

1. As admin, change a test's default weight / toggle enabled, and create/update a user.
2. **Expected**: works as before; non-admins are denied admin routes.

### 6. Deployment without a JS toolchain (User Story 3, SC-005/SC-007)

1. On a clean supported host, build and run the application.
2. **Expected**: completes with zero JavaScript runtime/package/build tools; the interface is served by
   the single Python service.

### 7. Guardrail against reintroducing JavaScript (SC-006, FR-008)

1. Run the repository guardrail check.
2. Add a stray `.ts`/`.js` project file and re-run.
3. **Expected**: the check passes clean initially and fails when authored JS is introduced (vendored
   `static/vendor/` excluded).

### 8. UI test coverage in Python (SC-004)

1. Run the backend test suite.
2. **Expected**: pytest tests assert the rendered pages and interactive fragments (re-grade, log expand),
   covering the behaviors the removed Vitest tests covered.

## Constitution validation

- **Transparent Grading (IV)**: the server-rendered review detail presents the same structured breakdown
  and pros/cons.
- **Portable (V)**: removing the JS toolchain reduces footprint; only Jinja2 + one static asset are added.
- **Separation**: the web frontend remains a distinct presentation layer (routes/templates/assets) served
  by the backend, without JavaScript.
