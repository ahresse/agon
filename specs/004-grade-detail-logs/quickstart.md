# Quickstart: Per-Grade Detail and Evidence Logs

Validation guide proving reviewers can see the evidence behind each grade. Maps to acceptance criteria
in [spec.md](./spec.md). See [contracts/](./contracts) and [data-model.md](./data-model.md) for shapes.

## Prerequisites

- A running Agon instance (see `specs/001-code-review-flow/quickstart.md`).
- On an instance that predates this feature, the evidence-log value is added automatically the first
  time the updated instance runs; pre-existing results simply have no log.

## Validation scenarios

### 1. Evidence log for a passing test (User Story 1)

1. Sign in as the seeded Reviewer and upload a small submission with a known issue (e.g. an unused
   variable).
2. Open the completed review; expand the lint test's entry.
3. **Expected**: the test shows its grade and weight plus an evidence log naming the concrete finding
   (e.g. `file:line` + rule). Other tests stay collapsed. Confirms FR-001, FR-003, FR-004, FR-011.

### 2. Evidence log for a failed/zero test (User Story 2)

1. Run an assessment where one test fails or times out (or upload a submission a test finds nothing to
   assess).
2. Expand that test's detail.
3. **Expected**: the log states the failure/timeout reason, or that no assessable input was found —
   never an empty, unexplained zero. Confirms FR-005.

### 3. Persistence across history (User Story 3)

1. Complete a review, then reopen it later from the history list and expand a test.
2. **Expected**: the same evidence log is shown, unchanged from the original run. Confirms FR-002,
   FR-010 (for new results), SC-003.

### 4. Large log stays usable (edge case)

1. Assess a submission that produces a large amount of evidence.
2. Expand the test's log.
3. **Expected**: the log is scrollable/bounded (and truncated with a marker if beyond the cap); the page
   remains navigable. Confirms FR-006, SC-005.

### 5. No-log and pre-feature indications (edge cases)

1. Expand a test that recorded no extra evidence → **Expected**: "No additional evidence".
2. Open a review whose results predate this feature → **Expected**: "No log available for this result".
   Confirms FR-007, FR-010.

### 6. Safe rendering (edge case, FR-009)

1. Assess a submission whose content includes markup/control characters that a test echoes into its log.
2. Expand the log.
3. **Expected**: content is shown as inert text; the page is not altered and nothing executes.

### 7. Authorization (SC-004)

1. As a reviewer, attempt to view another reviewer's review detail/log.
2. **Expected**: access is denied, consistent with existing review-access rules. Confirms FR-008.

## Constitution validation

- **Sandboxing (II)**: logs are produced inside the isolated execution boundary and returned via the
  existing result channel; no new host execution.
- **Measurable/Transparent (I, IV)**: every grade now links to the concrete evidence that produced it.
- **Portable (V)**: one optional evidence value + bounded text; no new services or dependencies.
