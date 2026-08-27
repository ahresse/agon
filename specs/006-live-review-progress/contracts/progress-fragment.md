# Contract: Review Progress Fragment

A server-rendered HTML fragment that shows a review's live status, progress bar, and estimated time
remaining, and re-polls itself every 2 seconds via the vendored htmx helper while the review is running.
Reuses existing page auth and ownership rules.

## Route

| Method | Path | Returns | Auth |
|--------|------|---------|------|
| GET | `/ui/reviews/{review_id}/progress` | Progress fragment (HTML partial) | review owner |

- Unauthenticated → redirect to login (page-auth behavior).
- Authenticated non-owner → the standard not-found/denied fragment (progress not exposed, FR-009).

## Fragment behavior

**While the review is pending/running** the fragment contains:

- The current **status** text.
- A **progress bar** whose fill = `completed / total` (whole-test granularity).
- An **estimated time remaining**: a friendly duration, or **"estimating…"** when no test has completed
  yet.
- A **self-poll trigger**: `hx-get="/ui/reviews/{id}/progress"`, `hx-trigger="every 2s"`,
  `hx-swap="outerHTML"` — so the fragment replaces itself every 2 seconds.

**When the review is terminal (completed/failed)** the fragment:

- Renders a terminal marker (e.g. "Completed" / "Failed") **without** a progress bar or ETA (FR-010).
- **Omits** the poll trigger so polling stops (edge case: page left open after completion).
- Causes the page to show the final grade + per-test breakdown (feature 005), e.g. by swapping in the
  completed detail or instructing the detail area to load the stored result. No manual refresh required
  (FR-005).

## Progress values (see data-model.md)

| Field | Meaning |
|-------|---------|
| status | pending / running / completed / failed |
| completed / total | finished tests / total enabled tests (failures count as finished) |
| fraction | completed / total (1.0 when total is 0) |
| eta | `max(0, avg_time_per_completed × remaining)`, or "estimating…" when not yet estimable; absent when terminal |

## Guarantees

- Fresh within 3 seconds of a test completing at the 2-second cadence (SC-001).
- ETA never negative; shows "estimating…" until the first test completes (FR-004, SC-003).
- Progress keeps advancing when a test fails/times out (FR-007, SC-007).
- No authored JavaScript: behavior is htmx attributes + server rendering (feature 005).
- Reopening a running review renders current progress immediately and resumes polling (FR-006, SC-006).
