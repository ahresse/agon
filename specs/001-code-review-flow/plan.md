# Implementation Plan: End-to-End Candidate Code Review Flow

**Branch**: `001-code-review-flow` | **Date**: 2026-08-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-code-review-flow/spec.md`

## Summary

Agon lets a Reviewer upload a candidate's Python code through a web interface and receive an
explainable grade. Enabled tests (metric-based and at least one AI-agent test) run asynchronously,
each in an isolated LXC/LXD container, and each emits a 0-100 grade plus structured pros/cons. The
final grade is the weighted mean of test grades. Admins set global default weights and manage tests
and users; Reviewers may override weights per-review and see the grade recompute instantly from
stored results without re-running tests. Completed reviews are persisted and browsable.

Technical approach: a FastAPI backend with an in-process, SQLite-backed job queue orchestrates
containerized test runs via LXC/LXD; a React + TypeScript SPA renders the structured breakdown and
pros/cons. AI-agent tests call a pluggable provider from inside their container. The whole stack
targets a single self-hosted Raspberry Pi running Ubuntu (arm64).

## Technical Context

**Language/Version**: Python 3.11 (backend); TypeScript 5.x (frontend); assessed candidate code is
Python 3.x

**Primary Dependencies**: FastAPI + Uvicorn (backend API/async), SQLAlchemy (persistence),
Pydantic (schemas), pylxd/LXD API (container orchestration); React + Vite + TypeScript (frontend)

**Storage**: SQLite (single-file, on-device); uploaded submissions stored on the local filesystem
with DB-tracked metadata

**Testing**: pytest (backend, unit + integration); Vitest + React Testing Library (frontend);
contract tests against the OpenAPI schema

**Target Platform**: Raspberry Pi running Ubuntu (arm64), single self-hosted instance

**Project Type**: Web application (separate backend + frontend), per constitution

**Performance Goals**: Weight-change re-grade renders in under 2 s (SC-003); assessment throughput
is bounded by container start plus test runtime, not by the app; single-instance interactive use

**Constraints**: All candidate code and AI agents MUST run in LXC/LXD containers, never on host
(constitution II); stack MUST run within Raspberry Pi resource limits (constitution V); no reliance
on hardware beyond the arm64 target

**Scale/Scope**: Single self-hosted instance; small concurrent reviewer count (team-scale, low
tens); large-scale/high-concurrency explicitly out of scope for this feature

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Derived from `.specify/memory/constitution.md` v1.0.0:

| Principle | Gate | Status |
|-----------|------|--------|
| I. Measurable Assessment | Every test yields a reproducible 0-100 grade + weight + evidence (pros/cons) | PASS — FR-005, data model `TestResult` carries grade + pros/cons evidence |
| II. Sandboxed Execution (NON-NEGOTIABLE) | All candidate code and AI agents run in LXC/LXD containers, never on host | PASS — plan orchestrates every test (including AI-agent) via LXD; no host execution path |
| III. Extensible Test Framework | Tests are self-contained plugins with a stable weight-in/grade-out contract; adding tests needs no core change | PASS — `contracts/test-plugin-contract.md` defines the plugin interface; language support extends via same contract |
| IV. Weighted, Transparent Grading | Final grade = weighted mean; reviewer custom weights; UI shows structured pros/cons + per-test breakdown | PASS — FR-006/009/012; grading is a pure function over stored `TestResult`s |
| V. Portable & Self-Hostable | Full stack runs on Raspberry Pi / Ubuntu (arm64); footprint is a design constraint | PASS — SQLite + in-process queue + LXD (native to Ubuntu); no heavy external services |

**Post-Design Re-check**: See end of Phase 1 below — all gates remain PASS; no violations, so
Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-code-review-flow/
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── openapi.yaml                 # HTTP API contract (backend ↔ frontend)
│   └── test-plugin-contract.md      # Test plugin + container execution contract
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/          # SQLAlchemy models: User, Submission, Test, Review, TestResult, WeightConfig
│   ├── services/        # grading (weighted mean), scheduling (job queue), language detection
│   ├── runners/         # LXC/LXD container orchestration; metric + AI-agent runners
│   ├── tests_plugins/   # built-in test plugins: Python quality metrics (lint_ruff, complexity_radon,
│   │                    #   stdlib_idioms, type_check_mypy, security_bandit, formatting_black) +
│   │                    #   one AI-agent test; plugin registry
│   └── api/             # FastAPI routers: auth, users (admin), submissions, tests, weights;
│                        #   reviews split per concern: reviews_detail, reviews_weights, reviews_list
└── tests/
    ├── contract/        # OpenAPI + plugin-contract conformance
    ├── integration/     # upload→run→grade flows, weight override re-grade, failure isolation
    └── unit/            # grading math, language detection, queue transitions

frontend/
├── src/
│   ├── components/      # grade breakdown, pros/cons panel, weight editor, test config
│   ├── pages/           # Upload, Review detail, History, Admin config, Login
│   └── services/        # API client (generated/typed from openapi.yaml)
└── tests/               # Vitest component + interaction tests
```

**Structure Decision**: Web application (Option 2). The constitution mandates a separate backend and
web frontend, so the repo uses `backend/` (FastAPI, containerized test orchestration, persistence)
and `frontend/` (React + TypeScript SPA). The test-plugin system lives under
`backend/src/tests_plugins/` with a registry so new tests are added without touching the core, per
Principle III.

## Complexity Tracking

> No constitution violations. Table intentionally empty.
