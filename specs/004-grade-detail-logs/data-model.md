# Phase 1 Data Model: Per-Grade Detail and Evidence Logs

Derived from the Key Entities and Functional Requirements in [spec.md](./spec.md). This feature adds a
single value to an existing entity; no new entities.

## Changed entity

### Test Result (extended)

The outcome of one Test within a Review now carries the evidence behind its grade.

| Field | Description | Rules |
|-------|-------------|-------|
| id | Unique identifier | Required, unique (unchanged) |
| review | Parent Review | Required (unchanged) |
| test | The executed Test | Required (unchanged) |
| grade | 0-100 score | Required (unchanged) |
| status | success or failed | Required (unchanged) |
| pros | Structured positive findings | Unchanged |
| cons | Structured negative findings | Unchanged |
| **log** | **Evidence: the observations/tool output/failure reason behind the grade** | **Optional; capped at 256 KiB, truncated with a marker if longer; absent = no log captured (pre-feature result)** |
| ran_at | Execution timestamp | Unchanged |

- **Absent vs. empty distinction** (FR-007, FR-010):
  - **absent** (no value) → the result predates evidence capture → shown as "No log available for this
    result".
  - **empty** → the test ran and recorded no additional evidence → shown as "No additional evidence".
  - **text** → shown as inert preformatted text.
- **Capture-time bound**: a log longer than 256 KiB is truncated to the cap with a trailing
  `… [log truncated]` marker before it is stored.
- **Failure path**: for a failed/timed-out result, the log leads with a sanitized reason (error type +
  message or timeout) followed by the full raw error output; for a no-assessable-input result, the log
  states that no input was found. For a passing result, the log is a focused excerpt of the concrete
  findings that drove the grade.

## Conceptual view surfaced to reviewers

### Test Result Detail (read model)

Assembled for the review-detail view; not a stored entity.

| Field | Source |
|-------|--------|
| test id, test name | Test |
| grade, status | Test Result |
| effective weight, contribution | Weight resolution + grading (unchanged) |
| pros, cons | Test Result |
| **log** | **Test Result log (optional)** |

## Relationships

Unchanged. The log is intrinsic to a Test Result (1:1 with the result it explains).

## Derived computations

- **Grade/contribution**: unchanged; the log is evidence, never an input to the weighted mean
  (Principle IV; recomputation on weight change still reads stored results only and does not alter logs).

## Evolution of existing data

- New results capture the log value.
- Results created before this feature have no log value and are labeled "No log available for this
  result" wherever they are viewed. The addition is purely additive — existing results and views keep
  working.
