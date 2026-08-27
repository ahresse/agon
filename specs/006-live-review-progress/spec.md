# Feature Specification: Live Review Status with Progress Bar and ETA

**Feature Branch**: `006-live-review-progress`

**Created**: 2026-08-27

**Status**: Draft

**Input**: User description: "the status of the review should be updated live and there should also be progress bar with an estimated time for completion"

## Clarifications

### Session 2026-08-27

- Q: How should the page receive live progress updates given the no-authored-JavaScript rule — automatic re-polling on a short interval, or a server-pushed live stream? → A: The page automatically re-polls a server-rendered progress fragment on a short interval (no authored JavaScript); polling stops when the review is done.
- Q: How often should the page re-poll for progress while an assessment is running? → A: Every 2 seconds.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reviewer watches an assessment progress live (Priority: P1)

A reviewer starts an assessment and stays on the review page. Without manually refreshing, they see the
review's status update as it advances (pending → running → completed/failed), a progress bar that fills
as individual tests finish, and an estimated time remaining until the assessment completes. When the
assessment finishes, the page shows the final grade and per-test breakdown automatically.

**Why this priority**: Assessments run asynchronously and can take a noticeable amount of time
(container start + per-test runtime). Today the reviewer must refresh to learn whether anything has
happened, which is opaque and frustrating. Live status, a progress bar, and an ETA turn an uncertain
wait into a transparent, trustworthy experience. This is the core of the feature and delivers value on
its own.

**Independent Test**: Start an assessment, remain on the review page without refreshing, and confirm the
status text, the progress bar fill, and the estimated time remaining all update as tests complete, and
that the final result appears automatically when done.

**Acceptance Scenarios**:

1. **Given** a reviewer on a review that is pending or running, **When** tests begin and complete over
   time, **Then** the displayed status and progress bar update on the page without a manual refresh.
2. **Given** an assessment in progress, **When** some tests have finished and others have not, **Then**
   the progress bar reflects the proportion completed and an estimated time remaining is shown.
3. **Given** an assessment that reaches completion, **When** the last test finishes, **Then** the page
   automatically shows the final status, the final grade, and the per-test breakdown without a refresh.
4. **Given** an assessment that ends in failure (all tests failed), **When** it finishes, **Then** the
   status updates to failed and the progress indicator reaches its end state rather than appearing stuck.

---

### User Story 2 - Reviewer sees an accurate, stabilizing estimate (Priority: P2)

While an assessment runs, the reviewer sees an estimated time to completion that becomes more accurate as
more tests finish, and never shows misleading values (e.g. a negative time, or a time that keeps growing
without explanation).

**Why this priority**: An ETA is only useful if it is trustworthy. A wildly wrong or erratic estimate is
worse than none. This refines User Story 1's estimate but depends on the live-update mechanism existing
first.

**Independent Test**: Run an assessment with several tests and observe that the estimated time remaining
is presented sensibly (non-negative, decreasing overall as work completes) and resolves to "finishing"/
zero as the last tests complete.

**Acceptance Scenarios**:

1. **Given** an assessment with multiple tests, **When** the first test completes, **Then** an estimated
   time remaining is shown based on observed progress so far.
2. **Given** more tests complete, **When** the estimate updates, **Then** it trends toward zero as work
   finishes and is never shown as a negative duration.
3. **Given** the system cannot yet form a meaningful estimate (e.g. no test has finished), **When** the
   reviewer views progress, **Then** a clear "estimating…" indication is shown rather than a misleading
   number.

---

### User Story 3 - Reviewer returns to a still-running review and resumes live updates (Priority: P3)

A reviewer navigates away and later reopens a review that is still running; the page immediately shows the
current status, current progress, and current estimate, and continues updating live from that point.

**Why this priority**: Reviewers routinely leave and come back. Resuming live updates on reopen makes the
feature reliable across navigation, but it builds on the core live-update behavior.

**Independent Test**: Start an assessment, leave the page, reopen the review while it is still running,
and confirm the current progress/ETA are shown immediately and continue updating live.

**Acceptance Scenarios**:

1. **Given** a running assessment, **When** the reviewer reopens its review page, **Then** the current
   status, progress, and estimate are shown immediately and keep updating live.
2. **Given** a review that already completed while the reviewer was away, **When** they reopen it, **Then**
   the final result is shown directly (no progress bar or estimate for finished work).

---

### Edge Cases

- A test crashes or times out mid-assessment: it counts as a completed (failed) unit of work so the
  progress bar continues to advance and the estimate remains sensible, rather than stalling.
- All tests finish nearly simultaneously: the progress bar reaches 100% and the final result appears
  without flicker or a stuck intermediate state.
- An assessment with only one test: the progress bar and status still behave correctly (from starting to
  done) even though there is little basis for a mid-run estimate.
- The live connection is briefly interrupted (e.g. transient network hiccup): updates resume
  automatically when possible, and the reviewer is not left with a permanently frozen indicator.
- The reviewer keeps the page open long after completion: no further updates are attempted and the final
  result remains displayed.
- An unusually long-running test makes the estimate grow: the estimate adjusts rather than showing a
  clearly wrong fixed value, and never displays a negative time.
- The reviewer opens a review they are not authorized to see: live progress is not exposed, consistent
  with existing access rules.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST display the current status of a review (e.g. pending, running,
  completed, failed) on the review page and update it live as the assessment advances, without requiring
  the reviewer to manually refresh. Live updates are delivered by the page automatically re-polling a
  server-rendered progress fragment every 2 seconds (no authored JavaScript), and polling MUST stop
  once the review reaches a terminal status.
- **FR-002**: The system MUST display a progress bar for an in-progress assessment that reflects the
  proportion of the review's tests that have completed (both successful and failed tests count as
  completed units of work).
- **FR-003**: The system MUST display an estimated time remaining until the assessment completes, based
  on observed progress, and update it live as tests finish.
- **FR-004**: The estimated time remaining MUST never be shown as a negative value and MUST trend toward
  zero as the assessment nears completion; when no meaningful estimate can yet be formed, the system MUST
  show a clear "estimating…" (or equivalent) indication instead of a misleading number.
- **FR-005**: When an assessment completes (successfully or in failure), the review page MUST
  automatically reflect the final status, the final grade, and the per-test breakdown without a manual
  refresh, and MUST stop showing the in-progress progress bar and estimate.
- **FR-006**: When a reviewer reopens a review that is still running, the system MUST immediately present
  the current status, progress, and estimate, and continue updating them live.
- **FR-007**: The system MUST continue to advance progress when a test fails or times out, treating it as
  a completed unit of work so the indicator does not stall.
- **FR-008**: If a live update (poll) is briefly interrupted, the system MUST resume updates on the next
  interval automatically and MUST NOT leave the reviewer with a permanently frozen or misleading
  indicator.
- **FR-009**: Live progress and status MUST be visible only to reviewers authorized to view that review,
  consistent with existing review-access rules.
- **FR-010**: For a review that is already complete when opened, the system MUST show the final result
  directly and MUST NOT display an in-progress progress bar or estimate.

### Key Entities *(include if data involved)*

- **Assessment Progress**: The live, derived view of a running review's advancement — total tests to run,
  number completed (success or failure), current status, and an estimated time remaining. Derived from the
  review and its accumulating test results; not necessarily stored beyond what is needed to compute it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: While an assessment runs, the displayed status and progress bar reflect each test's
  completion within 3 seconds of it finishing (using a 2-second poll interval), without the reviewer
  refreshing the page.
- **SC-002**: In 100% of in-progress assessments, the progress bar's fill equals the proportion of the
  review's tests that have completed (completed / total), within one test's granularity.
- **SC-003**: The estimated time remaining is never displayed as a negative value, in 100% of observed
  states.
- **SC-004**: For an assessment with at least three tests, the estimated time remaining decreases overall
  as tests complete and resolves to zero/"finishing" as the final test completes.
- **SC-005**: When an assessment completes, the final grade and breakdown appear automatically within 3
  seconds of the last test finishing, without a manual refresh.
- **SC-006**: Reopening a still-running review shows the current progress and estimate immediately (on
  first render) and resumes live updates.
- **SC-007**: A failed or timed-out test never causes the progress indicator to stall; progress continues
  to advance in 100% of such cases.

## Assumptions

- "Live" means the reviewer sees updates automatically while viewing the review, within a few seconds of
  each test completing, without manually refreshing; near-real-time (not sub-second) is acceptable for the
  self-hosted target. Updates are delivered by re-polling a server-rendered progress fragment every 2
  seconds, consistent with the project's server-rendered, no-authored-JavaScript web interface.
- Progress is measured at the granularity of whole tests (completed tests / total enabled tests for the
  review), which is the unit the reviewer already understands from the breakdown.
- The estimated time remaining is derived from observed per-test completion so far (e.g. average time per
  completed test applied to the remaining tests); it is an estimate and may adjust as work proceeds.
- The feature surfaces existing assessment progress; it does not change the grading model, the set of
  tests, the isolation of test execution, or user roles.
- Live updates follow existing review-access rules; no new sharing or notification mechanism (e.g. email)
  is introduced.
- Progress and estimates apply only while a review is pending/running; completed and failed reviews show
  their stored final result without an in-progress indicator.
