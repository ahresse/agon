# Implementation Plan: Single-Language (Python) Stack — Eliminate JavaScript

**Branch**: `005-python-only-stack` | **Date**: 2026-08-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-python-only-stack/spec.md`

## Summary

Consolidate the whole system into one project-authored language — Python — by replacing the separate
React/TypeScript single-page client with a **server-rendered web interface** delivered by the existing
Python backend, and removing the JavaScript build/test toolchain entirely. Reviewer- and admin-facing
behavior is preserved with no regression. Instant interactivity that previously required authored
JavaScript (instant re-grade on weight change, expanding a test's evidence log) is preserved via
**partial, server-driven updates** using a single **vendored, non-authored** helper (htmx) served as a
static asset — no build step, no authored JS. The grading model, plugin contract, data, and roles are
unchanged.

Approach: add HTML page routes that render Jinja2 templates from the same data the JSON endpoints
already produce; return HTML fragments for the interactive actions (weight re-grade, log expand) that
htmx swaps in place; serve the vendored htmx file as a static asset; delete `frontend/` and its tooling;
replace the two Vitest component tests with Python tests that assert the rendered HTML and fragment
behavior.

## Technical Context

**Language/Version**: Python 3.11 (single project-authored language)

**Primary Dependencies**: existing FastAPI + Uvicorn + SQLAlchemy + Pydantic; add Jinja2 for
server-side templating. One vendored static asset: `htmx.min.js` (non-authored, no build). No JavaScript
package manager or bundler.

**Storage**: unchanged (SQLite via SQLAlchemy)

**Testing**: pytest for backend + rendered-HTML/fragment assertions (replaces Vitest). The JavaScript
test toolchain is removed.

**Target Platform**: Raspberry Pi / Ubuntu (arm64), single self-hosted instance

**Project Type**: Web application — one deployable service that serves both the JSON API and the
server-rendered web interface

**Performance Goals**: Page renders and partial updates remain interactive on the Pi; removing the JS
build/runtime reduces the deployment toolchain

**Constraints**: No project-authored JavaScript/TypeScript and no JS package/build toolchain (FR-002);
interactivity via server-driven partial updates + a single vendored non-authored helper (FR-005);
behavior parity with the current client (FR-004); a guardrail flags any newly introduced JS (FR-008)

**Scale/Scope**: Replace 8 client pages/components + client API layer with server-rendered templates and
routes; delete the `frontend/` project

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Derived from `.specify/memory/constitution.md` v1.0.0:

| Principle | Gate | Status |
|-----------|------|--------|
| I. Measurable Assessment | Unchanged | PASS — grading/plugins untouched |
| II. Sandboxed Execution (NON-NEGOTIABLE) | Unchanged | PASS — no execution path changes |
| III. Extensible Test Framework | Unchanged | PASS — plugin contract untouched |
| IV. Weighted, Transparent Grading | Frontend MUST present structured breakdown + pros/cons + per-test contribution | PASS — the server-rendered interface presents the identical breakdown, pros/cons, and contributions |
| V. Portable & Self-Hostable | Full stack deployable on Pi; footprint is a constraint | PASS — removing the JS toolchain reduces footprint; adds only Jinja2 + one static asset |

**Additional constraint — "separate a backend service from a web-based frontend"**: PASS. The web
frontend remains a distinct presentation layer (its own routes, templates, and static assets) served by
the backend; "web-based frontend" does not mandate JavaScript. A server-rendered frontend satisfies the
separation. (No constitution change is required; if governance wants this reading recorded explicitly,
that is a separate `/speckit.constitution` action.)

**Post-Design Re-check**: See end of Phase 1 — all gates remain PASS; Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/005-python-only-stack/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── web-ui-routes.md         # Server-rendered page + fragment route contract
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── web.py                 # NEW: server-rendered page routes (login, upload, review detail,
│   │   │                          #      history, admin config, admin users) + htmx fragment routes
│   │   └── main.py                # mount Jinja2 templates + static assets; include web router
│   ├── templates/                 # NEW: Jinja2 templates (base + one per page) and fragments/
│   └── static/
│       └── vendor/htmx.min.js     # NEW: vendored, non-authored helper (static asset, no build)
└── tests/
    └── web/                       # NEW: rendered-HTML + fragment behavior tests (replace Vitest)

frontend/                          # DELETED entirely (recoverable via git history)
```

**Structure Decision**: Keep the single FastAPI service; add a server-rendered web layer (templates +
static assets + page/fragment routes) alongside the existing JSON API, and delete the separate
JavaScript client. Interactive actions return HTML fragments swapped in place by the vendored htmx
helper, preserving observable behavior (instant re-grade, log expand) with zero authored JavaScript.

## Complexity Tracking

> No constitution violations. Table intentionally empty.
