# Phase 1 Data Model: Live Review Status with Progress Bar and ETA

This feature adds **no persisted schema**. Progress is a derived read model computed from existing data.

## Existing data used (unchanged)

| Source | Field(s) used | Purpose |
|--------|---------------|---------|
| Review | status, created_at, completed_at | Current status; elapsed-time fallback start; terminal detection |
| Job (for the review) | started_at | Preferred assessment start time for elapsed/ETA |
| Test (enabled) | count of enabled tests | Total units of work for the review |
| Test Result (for the review) | count of rows | Completed units of work (success or failure) |

## Derived read model (not persisted)

### Assessment Progress

Computed on each progress request; never stored.

| Field | Description | Rules |
|-------|-------------|-------|
| status | The review's current status | pending / running / completed / failed |
| total | Number of tests the review runs | Count of enabled tests; ≥ 0 |
| completed | Number of tests finished (success or failure) | Count of the review's test results; 0 ≤ completed ≤ total |
| fraction | completed / total | 0.0–1.0; defined as 1.0 when total is 0 (nothing to do) |
| eta_seconds | Estimated seconds remaining | ≥ 0 (clamped); `null` when not yet estimable (no test completed) |
| is_terminal | Whether the review is completed or failed | true → no progress bar/ETA; final result shown |

### Computation rules

- **completed / total** at whole-test granularity (spec FR-002). Failed/timed-out results count as
  completed (FR-007).
- **eta_seconds**:
  - If `completed == 0` (and not terminal): `null` → UI shows "estimating…" (FR-004).
  - Else: `max(0, (elapsed / completed) * (total - completed))`, where `elapsed` is now − start
    (Job.started_at, else Review.created_at). Never negative (SC-003); trends to 0 as completed → total
    (SC-004).
  - If `is_terminal`: `eta_seconds = 0` and the ETA/progress bar are not displayed (FR-005/FR-010).

## State transitions

None introduced. The review's own lifecycle (PENDING → RUNNING → COMPLETED/FAILED) is unchanged; the
progress view merely reflects it live.
