# Phase 0 Research: Single-Language (Python) Stack — Eliminate JavaScript

Records the decisions behind replacing the separate JavaScript client with a server-rendered Python web
interface while preserving behavior and honoring the "no authored JavaScript" constraint.

## 1. Server-rendering approach

- **Decision**: Render the web interface with **Jinja2 templates** served by the existing FastAPI app.
  Each current page becomes an HTML route returning a rendered template; a shared base template provides
  layout and includes the vendored helper.
- **Rationale**: Jinja2 is the standard, lightweight Python templating engine, already compatible with
  FastAPI/Starlette, and adds negligible footprint on the Pi (Principle V). It keeps the presentation
  layer distinct (its own routes/templates/assets), satisfying the "separate web-based frontend"
  constraint without JavaScript.
- **Alternatives considered**: A Python-to-HTML component library (e.g. building DOM in Python) —
  rejected as heavier and less transparent than templates. Full-page-only forms with no partial updates
  — rejected because the clarified requirement mandates in-place updates for re-grade/log-expand.

## 2. Preserving interactivity without authored JavaScript

- **Decision**: Use **htmx**, vendored as a single static `htmx.min.js` file (non-authored, no build
  step), to issue background requests on user actions and swap **server-rendered HTML fragments** into
  the page in place. Interactive actions (change a weight → re-grade; expand a test → show its evidence
  log) return fragments, not full pages.
- **Rationale**: The clarifications set (a) only project-authored/built JS is forbidden — a vendored,
  non-authored static asset is allowed; and (b) instant re-grade must be a partial in-place update with
  no full-page navigation. htmx delivers exactly this with attributes in the HTML and all logic on the
  server in Python. No bundler, package manager, or authored JS is introduced.
- **Alternatives considered**: Hand-written vanilla JS for fetch+swap (rejected — that is authored JS,
  violating FR-002). Full-page reloads on every action (rejected — violates the clarified in-place-update
  requirement). Alpine.js/others (rejected — htmx keeps behavior server-driven and templates the single
  source of truth; one helper is enough).

## 3. Reusing existing behavior/data

- **Decision**: The HTML routes reuse the **same services and read models** the JSON endpoints already
  use (auth/session, submission upload + validation, review detail assembly with per-test grade/weight/
  contribution/pros/cons/log, weight recomputation, history, admin test/user config). Only the
  presentation changes; the JSON API may remain for programmatic use.
- **Rationale**: Guarantees behavioral parity (FR-004, SC-003) with minimal risk, since grading and data
  paths are untouched (FR-009). Templates render the exact structured breakdown the constitution requires
  (Principle IV).
- **Alternatives considered**: Rewriting business logic for the web layer (rejected — needless
  duplication and regression risk). Removing the JSON API (deferred — out of scope; this feature changes
  the interface delivery, not the API's existence).

## 4. Session/auth in a server-rendered flow

- **Decision**: Reuse the existing signed session cookie. HTML routes require the session (redirect to
  the login page when unauthenticated); admin-only pages/fragments enforce the existing admin guard and
  return the appropriate denial. No new auth mechanism.
- **Rationale**: Preserves FR-004/FR-008 access rules with proven code; a redirect-to-login is the
  standard server-rendered pattern.
- **Alternatives considered**: Token-in-header (rejected — that is a client-app pattern; cookies suit
  server-rendered pages and htmx requests carry them automatically).

## 5. Testing the web interface in Python

- **Decision**: Replace the two Vitest component tests with **pytest** tests that drive the app's test
  client, asserting rendered HTML for each page (structured breakdown present, pros/cons, contributions)
  and asserting fragment behavior for the interactive actions (weight change returns an updated grade
  fragment; log expand returns the evidence fragment). Remove the Vitest/TS test toolchain.
- **Rationale**: Satisfies FR-006/SC-004 (no net loss of covered behavior) in the single language, and
  removes the JS test ecosystem (SC-005).
- **Alternatives considered**: A headless-browser end-to-end tool (rejected for v1 — heavier on the Pi;
  server-rendered HTML + fragment assertions cover the behavior deterministically). Keeping Vitest
  (rejected — it is the JS toolchain being removed).

## 6. Removing the JavaScript project and guardrail

- **Decision**: Delete `frontend/` (client source, `package.json`/lockfile, Vite/TS config, Vitest
  tests) entirely; the vendored htmx asset lives under the backend's static directory. Add a **guardrail
  check** (a repo test / CI step) that fails if any project-authored `.js`/`.ts`/`.tsx`/`.jsx` file or a
  JS package manifest reappears, excluding the vendored `static/vendor/` asset.
- **Rationale**: The clarification chose full deletion (recoverable via git history), giving an
  unambiguous single-language guarantee (SC-001/SC-002). The guardrail satisfies FR-008/SC-006 and
  prevents silent reintroduction.
- **Alternatives considered**: Archiving the client (rejected per clarification). No guardrail (rejected
  — FR-008 requires an explicit, reviewable trip on new JS).

## 7. Deployment impact

- **Decision**: The one deployable service now serves both the API and the web interface; the deploy/run
  process no longer installs a JS runtime, package manager, or bundler.
- **Rationale**: Directly satisfies FR-007/SC-005 and reduces the footprint on the self-hosted target
  (Principle V), consistent with the one-command-deploy feature's intent.
- **Alternatives considered**: A separate static file server for the interface (rejected — unnecessary; a
  single Python service is simpler and lighter).
