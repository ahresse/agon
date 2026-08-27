# Quickstart: Live Review Status with Progress Bar and ETA

Validation guide proving live status, a progress bar, and an ETA appear on the review page and update
automatically. Maps to acceptance criteria in [spec.md](./spec.md); see
[contracts/progress-fragment.md](./contracts/progress-fragment.md) and [data-model.md](./data-model.md).

## Prerequisites

- A running Agon instance (single Python service; server-rendered UI per feature 005).
- To observe a real multi-second run, use containerized execution (provision the test image) so tests
  take long enough to watch progress advance. For fast local checks, the automated tests simulate
  partial completion directly.

## Validation scenarios

### 1. Live status + progress bar while running (User Story 1)

1. Sign in as a reviewer and upload a submission that runs several tests.
2. Stay on the review page (do not refresh).
3. **Expected**: the status and progress bar update automatically about every 2 seconds as tests finish;
   the bar fill matches completed/total. Confirms FR-001, FR-002, SC-001, SC-002.

### 2. Estimated time remaining (User Story 1 & 2)

1. While the assessment runs, watch the estimated time remaining.
2. **Expected**: before any test finishes it shows "estimating…"; once tests complete it shows a
   non-negative duration that trends toward zero as work finishes. Confirms FR-003, FR-004, SC-003,
   SC-004.

### 3. Auto-finalize on completion (User Story 1)

1. Let the assessment finish.
2. **Expected**: the page automatically shows the final status, final grade, and per-test breakdown; the
   progress bar and ETA disappear and polling stops. Confirms FR-005, SC-005.

### 4. Failure keeps progress advancing (edge case)

1. Run an assessment where a test fails or times out.
2. **Expected**: the failed test counts as completed so the bar keeps advancing; on all-fail the status
   becomes failed and the indicator reaches its end state (not stuck). Confirms FR-007, SC-007.

### 5. Resume on reopen (User Story 3)

1. Start an assessment, navigate away, then reopen the review while it is still running.
2. **Expected**: current status/progress/ETA show immediately and keep updating. Reopening an
   already-finished review shows the final result directly with no progress bar/ETA. Confirms FR-006,
   FR-010, SC-006.

### 6. Transient interruption (edge case)

1. Briefly interrupt connectivity during a run, then restore it.
2. **Expected**: the next 2-second poll resumes updates; the indicator is not left frozen. Confirms
   FR-008.

### 7. Access control (FR-009)

1. As a different reviewer, request another reviewer's progress fragment.
2. **Expected**: progress is not exposed (denied/not-found), consistent with existing review access.

## Constitution validation

- **Portable (V)**: derived reads + a light 2-second poll of a small fragment; no new services/deps.
- **No authored JavaScript (feature 005)**: live updates are htmx attributes on a server-rendered
  fragment.
- **Transparent Grading (IV)**: the final breakdown still appears; progress adds transparency during the
  wait.
