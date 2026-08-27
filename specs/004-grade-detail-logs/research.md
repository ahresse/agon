# Phase 0 Research: Per-Grade Detail and Evidence Logs

Records the decisions behind capturing, storing, transporting, and presenting a per-test evidence log,
resolving the open questions flagged in the spec's assumptions.

## 1. What "the log that gives the grade" contains

- **Decision**: The evidence log is the human-readable record a test produces while assessing the
  submission. For a **passing** test it is a **focused excerpt** of the concrete findings that drove the
  grade (e.g. specific issues with location), not the tool's full raw output. For a **failure** it leads
  with a **sanitized reason** (error type + message, timeout, or "no assessable input") followed by the
  **full raw error output** beneath. It is distinct from platform/system logs.
- **Rationale**: This is exactly the "why" behind the grade (spec FR-001, FR-005) and reinforces
  Measurable Assessment (Principle I). Platform/infrastructure logs are operator concerns, not reviewer
  evidence, and could leak internals — out of scope.
- **Alternatives considered**: Capturing full raw tool output verbatim (rejected as default — unbounded
  and noisy; tests instead compose a focused log, optionally including a bounded output excerpt).
  Deriving the log purely from pros/cons (rejected — loses the underlying detail the feature exists to
  expose).

## 2. Contract shape for the log

- **Decision**: Extend the test's assessment output with an **optional** evidence-log value that defaults
  to empty. Tests may populate it; those that don't yield an empty log, which the presentation renders as
  "no additional evidence".
- **Rationale**: Optionality keeps the test contract backward-compatible (Principle III) — no existing
  test must change to keep working. A single text value is the simplest transportable, storable, and
  renderable form.
- **Alternatives considered**: A structured/segmented log object (rejected for v1 — pros/cons already
  provide structure; a flat text log is enough and simpler to render safely). Making the log required
  (rejected — would force every test to change and break the additive-only goal).

## 3. Storage

- **Decision**: Store the evidence log as an **optional value on the per-test result record**.
  New records capture it; records created before this feature have no log and are labeled as such.
- **Rationale**: An optional field on the existing result is the minimal, portable change and directly
  satisfies persistence + historical-fidelity requirements (FR-002, FR-010, SC-003). Grading remains a
  pure function over stored results — the log is evidence, not an input.
- **Alternatives considered**: A separate evidence-log record (rejected — 1:1 with a result; an inline
  value is simpler and avoids a join). Storing logs outside the primary record store (rejected — splits
  the record from its evidence and complicates history fidelity).

## 4. Size bounding / truncation

- **Decision**: Cap the stored log at **256 KiB per test result**; if a test produces more, it is
  truncated at capture time with a trailing marker (e.g. `… [log truncated]`). The presentation
  additionally shows logs in a **scrollable, height-bounded** panel.
- **Rationale**: Protects storage footprint and retrieved payloads on the self-hosted target while
  keeping the salient evidence (FR-006, SC-005). 256 KiB comfortably holds typical output for a
  submission.
- **Alternatives considered**: No cap (rejected — a pathological submission could bloat storage and
  payloads). A separate "view full log" retrieval step (deferred — unnecessary once capture is bounded;
  can be added later if a larger cap is ever needed).

## 5. Transport across the execution boundary

- **Decision**: The result returned from the isolated execution boundary already carries the grade and
  findings; add the evidence log to that same result. Where execution is not isolated (a development
  fallback), the log passes through directly.
- **Rationale**: Reuses the sole result channel — no new host-execution path (Principle II). The channel
  safely carries arbitrary text (control characters are escaped in transit).
- **Alternatives considered**: A side artifact copied out of the execution boundary (rejected — extra
  I/O and a second channel to secure; the existing result is sufficient).

## 6. Safe presentation

- **Decision**: Present the log as **inert preformatted text** (monospace, whitespace-preserving) —
  never as markup. Long logs sit in a scrollable, bounded area with a copy affordance; an empty/absent
  log shows an explicit "No additional evidence" (present) or "No log available for this result"
  (pre-feature).
- **Rationale**: Satisfies safe-rendering and control-character handling (FR-009, edge cases). Content is
  escaped by default, so candidate-authored content cannot alter the page.
- **Alternatives considered**: Rich (markup/ANSI) rendering of logs (rejected for v1 — added surface area
  and risk; plain text is safe and sufficient).

## 7. Failure-path evidence

- **Decision**: On crash/timeout the framework records a sanitized failure reason as the start of the
  log (in addition to the existing con) and appends the full raw error output beneath it; a test that
  finds no assessable input records that reason as the log.
- **Rationale**: Directly satisfies FR-005 / User Story 2 — a failed test is no longer an unexplained
  zero.
- **Alternatives considered**: Relying only on the existing cons text (rejected — the feature's point is
  a dedicated, inspectable log surface, including for failures).

## 8. Authorization

- **Decision**: Logs are returned only through the existing review-detail retrieval, which already
  enforces review access; no new access path or sharing mechanism is introduced.
- **Rationale**: Reuses proven access control (FR-008, SC-004); least surface area.
- **Alternatives considered**: A dedicated log retrieval path (rejected — would duplicate authorization;
  the log rides on the already-authorized review detail).
