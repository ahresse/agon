# Phase 0 Research: Live Review Status with Progress Bar and ETA

Records the decisions behind delivering live status, a progress bar, and an ETA on the review page,
honoring the server-rendered, no-authored-JavaScript constraint (feature 005).

## 1. Live-update delivery

- **Decision**: The review-detail page embeds a **server-rendered progress fragment** that re-polls
  itself every **2 seconds** via the vendored htmx helper (`hx-get` + `hx-trigger="every 2s"`,
  `hx-swap="outerHTML"`). When the review reaches a terminal status the fragment renders the final state
  **without** the polling trigger, so polling stops automatically.
- **Rationale**: Satisfies the clarified mechanism (poll a fragment) and cadence (2s) with no authored
  JavaScript. Interval polling self-recovers from a transient hiccup (the next poll simply succeeds,
  FR-008) and is trivially light on the Pi (Principle V). Meets the ≤3s freshness targets (SC-001/005)
  with margin.
- **Alternatives considered**: Server-sent events (rejected per clarification — heavier, and a pushed
  stream is unnecessary at this cadence). Manual refresh (rejected — the feature exists to remove it).

## 2. Progress measurement

- **Decision**: Progress = **completed test results / total enabled tests** for the review, at
  whole-test granularity. A test result counts as completed whether it succeeded or failed/timed out
  (FR-002, FR-007). "Total" is the count of enabled tests (the set the review runs); "completed" is the
  count of persisted `TestResult` rows for that review.
- **Rationale**: This is the unit the reviewer already understands from the breakdown, is derivable from
  existing data with no schema change, and keeps advancing on failure (a failed result is still a row).
- **Alternatives considered**: Sub-test/percent-within-a-test progress (rejected — tests don't report
  sub-progress; adds complexity for little value). Weight-based progress (rejected — weights are about
  grading, not time).

## 3. Estimated time remaining (ETA)

- **Decision**: ETA = **(elapsed so far / completed count) × remaining count**, i.e. average observed
  time per completed test applied to the tests not yet done. Elapsed is measured from the assessment's
  start (the job's start time, falling back to the review's creation time). The value is **clamped at
  zero** (never negative) and rounded to a friendly unit (seconds). When **no test has completed yet**,
  no meaningful average exists, so the UI shows **"estimating…"** instead of a number (FR-004). As the
  final test completes, remaining → 0 so ETA → 0 ("finishing").
- **Rationale**: A simple, explainable running average stabilizes naturally as more tests finish
  (SC-004) and cannot go negative (SC-003). It needs only timestamps already available.
- **Alternatives considered**: Per-test historical averages across reviews (rejected for v1 — more state,
  marginal gain; container start dominates and varies). Exponential smoothing (rejected — unnecessary
  precision for a few-second, few-test wait). Fixed/declared per-test durations (rejected — tests vary).

## 4. Terminal handling and stopping the poll

- **Decision**: While the review is `PENDING`/`RUNNING`, the fragment shows status + progress bar + ETA
  and includes the poll trigger. When the review is `COMPLETED`/`FAILED`, the fragment renders a terminal
  marker **without** the poll trigger and triggers the page to reveal the final grade + breakdown
  (already implemented in feature 005) — e.g. via htmx swapping the fragment to a "done" state that
  reloads the detail area or shows the stored result. No progress bar/ETA is shown for terminal reviews
  (FR-005, FR-010).
- **Rationale**: Stopping the trigger at terminal status prevents endless polling after completion (edge
  case: page left open long after completion) and satisfies "final result appears automatically."
- **Alternatives considered**: Keep polling forever and no-op (rejected — needless load). Client-side
  timer to stop (rejected — that is authored JS).

## 5. Reopening a running review

- **Decision**: Because the fragment is server-rendered from current data on every request, reopening a
  running review immediately shows the **current** status/progress/ETA on first render and resumes
  polling from there (FR-006, SC-006). A review that finished while away renders its terminal state
  directly with no progress UI (FR-010).
- **Rationale**: Statelessness of the fragment makes resume-on-reopen automatic — no session/progress
  state to reconcile.
- **Alternatives considered**: Persisting a progress snapshot (rejected — unnecessary; derivation is
  cheap and always current).

## 6. Access control

- **Decision**: The progress fragment endpoint reuses the existing page-auth/ownership check: only the
  review's owning reviewer receives progress; others get the standard denial (FR-009).
- **Rationale**: Reuses proven access control; no new exposure.
- **Alternatives considered**: A separate public progress token (rejected — new surface, not needed).
