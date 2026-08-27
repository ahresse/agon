# Feature Specification: Per-Grade Detail and Evidence Logs in the UI

**Feature Branch**: `004-grade-detail-logs`

**Created**: 2026-08-27

**Status**: Draft

**Input**: User description: "the tool should give the details of each grade in the user interface. It should enable the reviewer to see the logs that give the grade"

## Clarifications

### Session 2026-08-27

- Q: What maximum stored size should each test's evidence log be capped at before it is truncated? → A: 256 KiB per test-result log (truncate beyond, with a marker)
- Q: When a test fails or crashes, should its evidence log show the raw underlying error output, or a sanitized human-readable reason? → A: Sanitized reason first, with the full raw error included below it
- Q: For a test that passes, should its evidence log include the tool's full raw output, or a focused excerpt of the relevant findings? → A: Focused excerpt: the concrete findings/locations that drove the grade

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reviewer inspects how a single test's grade was derived (Priority: P1)

A reviewer opens a completed review and, for any individual test, expands its entry to see the
details behind its grade: the concrete findings and the captured log/evidence the test produced while
running. The reviewer can read exactly what the test observed (e.g. the specific violations, offending
lines, or tool output) that led to the numeric score, rather than only seeing the score and a summary.

**Why this priority**: Explainability is the core promise of Agon — a grade is only trustworthy if the
reviewer can trace it to concrete evidence. Today reviewers see a grade plus short pros/cons but cannot
see the underlying log that justifies it. This is the minimum viable slice: it makes every existing
grade auditable on its own.

**Independent Test**: Open a completed review, expand one test, and confirm the detailed findings and
the test's captured log are shown and clearly correspond to that test's grade.

**Acceptance Scenarios**:

1. **Given** a completed review with per-test results, **When** the reviewer expands a single test,
   **Then** the interface reveals that test's detailed findings and its captured evidence log alongside
   its grade and weight.
2. **Given** a test's detail is expanded, **When** the reviewer reads the log, **Then** the content
   shown is the evidence that test recorded during its run (the observations that produced the grade),
   not a generic or empty placeholder.
3. **Given** a review with several tests, **When** the reviewer expands one test's detail, **Then**
   other tests' details remain collapsed so the view stays focused and readable.

---

### User Story 2 - Reviewer reviews logs for a failed or zero-scored test (Priority: P2)

A reviewer opens a test that failed, timed out, or scored zero and views its captured log to understand
why it did not produce a normal grade — for example, an error message, a timeout notice, or the absence
of assessable input.

**Why this priority**: Failures are exactly when reviewers most need the log. Without it, a failed test
is an unexplained zero. This depends on the same detail/log surface as User Story 1 but focuses on the
failure path.

**Independent Test**: Produce a review containing a failed/zero-scored test, open its detail, and confirm
the log explains the failure reason (error/timeout/no-input) clearly.

**Acceptance Scenarios**:

1. **Given** a test recorded as failed or timed out, **When** the reviewer opens its detail, **Then**
   the log shows a sanitized reason first, followed by the full raw error output, rather than an empty
   or misleading result.
2. **Given** a test that scored zero because it found nothing to assess, **When** the reviewer opens its
   detail, **Then** the log states that no assessable input was found.

---

### User Story 3 - Reviewer retains access to grade details for past reviews (Priority: P3)

A reviewer reopens a previously completed review from history and can still see the same per-test details
and evidence logs exactly as they were when the assessment ran.

**Why this priority**: Auditability must persist over time, not just immediately after a run. It builds on
User Story 1 by guaranteeing the captured evidence is stored and retrievable later.

**Independent Test**: Complete a review, reopen it later from history, expand a test, and confirm the same
detailed findings and log are shown as at assessment time.

**Acceptance Scenarios**:

1. **Given** a completed review viewed earlier, **When** the reviewer reopens it from history and expands a
   test, **Then** the stored details and log are shown identically to the original run.

---

### Edge Cases

- A test produces a very large log: the interface presents it without breaking the page layout (e.g.
  scrollable and/or truncated with a way to view the full content), so the reviewer can still read it.
- A test produces no meaningful log (e.g. a trivially clean result): the interface clearly indicates there
  is no additional evidence rather than showing a blank area with no explanation.
- A log contains sensitive-looking content from the candidate's own code: the log reflects what the test
  observed and is shown only to authorized reviewers of that review.
- Reviews created before this feature existed have no captured log: the interface indicates that no log is
  available for that older result rather than appearing broken.
- A log contains non-text or control characters: the interface displays it safely without corrupting the
  page or executing anything.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST capture, for each test run, an evidence log recording the observations that
  produced the test's grade. For a passing test the log MUST be a focused excerpt of the concrete
  findings that drove the grade (e.g. specific findings with their locations), not the tool's full raw
  output.
- **FR-002**: System MUST persist each test's evidence log together with its result so it can be retrieved
  whenever the review is viewed later.
- **FR-003**: System MUST let a reviewer expand any individual test within a completed review to view its
  detailed findings and its captured evidence log alongside the test's grade and weight.
- **FR-004**: System MUST present the detailed findings and log for one test independently, so expanding
  one test does not force all details open and the view remains readable.
- **FR-005**: For a failed, timed-out, or zero-scored test, the system MUST present a log that leads with
  a sanitized, human-readable reason (error type and message, timeout, or "no assessable input") and MUST
  include the full raw underlying error output beneath that reason, rather than an empty result.
- **FR-006**: System MUST cap each stored evidence log at 256 KiB, truncating anything beyond that with
  a clear marker, and MUST display large logs without breaking the page, providing a scrollable and/or
  truncated view with a means to access the retained content.
- **FR-007**: System MUST clearly indicate when a test has no additional log/evidence, distinct from a log
  that simply has not loaded.
- **FR-008**: System MUST restrict viewing a review's grade details and logs to users authorized to view
  that review.
- **FR-009**: System MUST render log content safely as text, without allowing embedded content to alter the
  page or execute.
- **FR-010**: For results created before evidence logs were captured, the system MUST indicate that no log
  is available rather than presenting a broken or misleading view.
- **FR-011**: The detailed grade breakdown MUST make each test's contribution to the final grade traceable,
  connecting the per-test grade, weight, and evidence to the overall weighted result.

### Key Entities *(include if data involved)*

- **Evidence Log**: The captured record of what a single test observed during its run — the findings,
  locations, tool output, or failure reason that justify its grade. Associated one-to-one with a test's
  result within a review and retained for later viewing.
- **Test Result Detail**: The reviewer-facing view of a single test's outcome — its grade, weight,
  contribution, structured findings (pros/cons), and evidence log.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For 100% of test results in a newly completed review, a reviewer can open the test's detail and
  see an evidence log that corresponds to that test's grade (including a failure reason for failed tests).
- **SC-002**: A reviewer can go from a review's grade breakdown to the underlying log for any single test in
  no more than two interactions (e.g. expand the test, view its log).
- **SC-003**: 100% of captured evidence logs remain retrievable and unchanged when the review is reopened
  later from history.
- **SC-004**: Reviewers can view logs only for reviews they are authorized to see; unauthorized access is
  prevented in 100% of attempts.
- **SC-005**: Evidence logs up to the 256 KiB cap are viewable without the reviewer losing the ability
  to navigate the page; logs exceeding the cap are truncated with a marker and still viewable.

## Assumptions

- "Logs that give the grade" means the evidence a test itself records while assessing the submission (its
  findings and, where applicable, raw tool output or failure reason), not low-level system/infrastructure
  logs of the platform.
- Evidence logs are derived automatically from each test's run; reviewers do not author them.
- This feature extends the existing per-test breakdown already shown for completed reviews; the weighted
  grading model, test set, and roles are unchanged.
- Evidence logs are captured going forward; historical results assessed before this feature simply have no
  log and are labeled as such.
- Log visibility follows existing review-access rules; no new sharing or export mechanism is introduced in
  this version.
- Each per-test log is retained up to a 256 KiB cap; larger outputs are truncated at capture time with
  a marker, and the truncated-but-retained content remains viewable. This cap is a fixed default for the
  self-hosted target.
