# Feature Specification: End-to-End Candidate Code Review Flow

**Feature Branch**: `001-code-review-flow`

**Created**: 2026-08-26

**Status**: Draft

**Input**: User description: "End-to-end candidate code review flow for Agon. Roles: Reviewer (uploads submissions, assesses, overrides weights per-review) and Admin (configures tests, default weights, and users). Reviewers upload a candidate code archive/files via the web UI; the system auto-detects language and rejects non-Python submissions with a clear message. On upload, tests run asynchronously as background jobs; every test (metric-based and AI-agent) runs in an isolated container. Each test outputs a grade 0-100 and contributes structured pros/cons derived from its result. If a test crashes or times out, it scores 0, is flagged, and remaining tests still count. The final grade is the weighted mean (0-100) of test grades. Admin sets global default weights; reviewers override weights per-review. Changing weights on an already-assessed submission recomputes the final grade instantly from stored test results without re-running tests. At least one containerized AI-agent test is included, feeding the same weighted grading model. Completed reviews, grades, and per-test breakdowns are persisted and browsable later. The frontend shows a structured view with per-test contributions and aggregated pros/cons."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reviewer submits code and receives a weighted grade (Priority: P1)

A reviewer signs in, uploads a candidate's Python code archive through the web
interface, and starts an assessment. The system runs the configured tests in the
background. When the assessment finishes, the reviewer sees a final grade (0-100)
together with a per-test breakdown and an aggregated list of pros and cons.

**Why this priority**: This is the core value of Agon — turning a candidate submission
into an explainable, measurable grade. Without it, no other capability is useful. It is
the minimum viable product on its own.

**Independent Test**: Upload a known Python submission, wait for the assessment to
complete, and confirm a final weighted grade plus a per-test breakdown and pros/cons are
displayed. Delivers immediate value even without weight customization or history.

**Acceptance Scenarios**:

1. **Given** a signed-in reviewer on the upload screen, **When** they upload a valid
   Python archive and start the assessment, **Then** the system accepts it and shows the
   assessment as in progress.
2. **Given** an assessment is running, **When** all tests complete, **Then** the reviewer
   sees a final grade between 0 and 100 computed as the weighted mean of the test grades.
3. **Given** a completed assessment, **When** the reviewer opens the result, **Then** they
   see each test's individual grade, its weight, its contribution to the final grade, and
   an aggregated pros/cons list derived from the test results.
4. **Given** a submission that is not Python, **When** the reviewer uploads it, **Then**
   the system rejects it with a clear message explaining that only Python is supported.

---

### User Story 2 - Reviewer overrides weights and re-grades instantly (Priority: P2)

A reviewer views a completed assessment and decides that certain qualities matter more for
this particular candidate. They adjust the weight of one or more tests for this review.
The final grade updates immediately from the already-stored test results, without re-running
any tests.

**Why this priority**: Custom weighting per reviewer is a defining feature of Agon and is
mandated by the project constitution, but it depends on User Story 1 producing test results
first.

**Independent Test**: Open a completed assessment, change one test's weight, and confirm the
final grade recomputes instantly and correctly without any test re-execution.

**Acceptance Scenarios**:

1. **Given** a completed assessment with stored test results, **When** the reviewer changes a
   test's weight for this review, **Then** the final grade is recomputed from the stored
   results without re-running tests.
2. **Given** a reviewer has overridden weights on a review, **When** they view the review
   again, **Then** their custom weights and the resulting grade are preserved.
3. **Given** a reviewer overrides weights on their review, **When** a different reviewer opens
   the same submission, **Then** the first reviewer's overrides do not affect the second
   reviewer's view.

---

### User Story 3 - Admin configures tests and default weights (Priority: P2)

An admin manages the set of available tests and assigns a global default weight to each. These
defaults apply to every new assessment unless a reviewer overrides them.

**Why this priority**: Admins establish the baseline assessment model that reviewers rely on.
Reviewers can still function with system defaults, so this ranks alongside weight override
rather than above the core flow.

**Independent Test**: As an admin, enable a test and set its default weight, then start a new
assessment as a reviewer and confirm the new default weight is applied.

**Acceptance Scenarios**:

1. **Given** an admin on the configuration screen, **When** they set a default weight for a
   test, **Then** new assessments use that weight as the starting value.
2. **Given** an admin enables or disables a test, **When** a reviewer starts a new assessment,
   **Then** only enabled tests are executed.
3. **Given** a reviewer without admin rights, **When** they attempt to change global test
   configuration, **Then** the system denies the action.

---

### User Story 4 - Reviewer browses past reviews (Priority: P3)

A reviewer opens a history view listing previously completed assessments and reopens any one to
see its stored grade, per-test breakdown, and pros/cons.

**Why this priority**: History adds significant convenience and auditability but is not required
for a single assessment to deliver value.

**Independent Test**: Complete two assessments, open the history list, and confirm both appear
and can be reopened with their full stored breakdowns intact.

**Acceptance Scenarios**:

1. **Given** completed assessments exist, **When** a reviewer opens the history view, **Then**
   they see a list of prior reviews with candidate identity, date, and final grade.
2. **Given** a prior review in the list, **When** the reviewer opens it, **Then** the stored
   grade, per-test breakdown, and pros/cons are shown exactly as recorded.

---

### User Story 5 - AI-agent test contributes to the grade (Priority: P3)

Among the executed tests is at least one AI-agent test scoped to a specific theme. It runs in
isolation like any other test and contributes a 0-100 grade and pros/cons to the same weighted
model.

**Why this priority**: AI-agent assessment is a differentiator but builds on the same execution
and grading mechanics as metric-based tests, so it can follow the core flow.

**Independent Test**: Run an assessment that includes the AI-agent test and confirm it produces a
0-100 grade and pros/cons that are folded into the final weighted grade like any other test.

**Acceptance Scenarios**:

1. **Given** an assessment configured with an AI-agent test, **When** the assessment runs,
   **Then** the AI-agent test executes in isolation and returns a 0-100 grade with pros/cons.
2. **Given** the AI-agent test has completed, **When** the final grade is computed, **Then** its
   grade is included in the weighted mean using its assigned weight.

---

### Edge Cases

- A test crashes or exceeds its time limit: it is recorded as grade 0, flagged as failed to the
  reviewer, and the remaining tests still contribute to the final grade.
- Every test in an assessment fails: the review transitions to a FAILED status with a final grade
  of 0 and all tests clearly flagged as failed, rather than an ambiguous or missing result. The
  failed review remains retrievable in history like any other review.
- An uploaded archive is empty, corrupted, or contains no detectable source code: the system
  rejects it with a clear message and does not start an assessment.
- An uploaded archive contains a member that would escape the extraction directory (a `../` path,
  an absolute path, or a symlink): the system rejects the whole archive with a clear message and
  does not extract or start an assessment, protecting the host.
- An uploaded archive contains a hardlink, device, or FIFO member, or its declared format does not
  match its actual content (e.g. tar bytes named `.zip`): the system detects the real format from
  content and rejects unsafe non-regular members with a clear message, without extracting them.
- An uploaded archive is a decompression bomb (excessive member count or total uncompressed size):
  the system refuses it before writing the excess to disk and informs the reviewer, protecting the
  host from resource exhaustion.
- All enabled tests carry a weight of 0: the system prevents computing an undefined grade and
  informs the reviewer that at least one positive weight is required.
- A reviewer changes weights while an assessment is still running: the grade recomputes only from
  results that have completed and finalizes once all tests finish.
- The same candidate submission is uploaded more than once: each upload is treated as a distinct,
  independently graded review.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST let a signed-in reviewer upload candidate code as an archive through the
  web interface, accepting both zip (`.zip`) and gzip-compressed tar (`.tar.gz`/`.tgz`) archives (and
  plain `.tar`), and MUST reject archives whose members escape the extraction directory (path
  traversal, absolute paths, or symlinks) with a clear message and without starting an assessment.
- **FR-002**: System MUST automatically detect the submission's programming language and reject any
  submission that is not Python with a clear, human-readable message.
- **FR-003**: System MUST run all enabled tests for a submission asynchronously as background work,
  allowing the reviewer to leave the page and return for results.
- **FR-004**: System MUST execute every test — metric-based and AI-agent — in an isolated
  container so that no candidate code or agent runs on the host and tests cannot affect one another.
- **FR-005**: System MUST require each test to output a grade on a 0-100 scale and a set of
  structured pros and cons derived from its result.
- **FR-006**: System MUST compute the final grade as the weighted mean (0-100) of the individual
  test grades using their assigned weights.
- **FR-007**: System MUST record a test that crashes or times out as grade 0, flag it as failed to
  the reviewer, and continue counting the remaining tests toward the final grade.
- **FR-008**: System MUST let an admin enable or disable tests and assign a global default weight to
  each enabled test.
- **FR-009**: System MUST let a reviewer override test weights for an individual review, without
  changing global defaults or other reviewers' views.
- **FR-010**: System MUST recompute the final grade instantly from stored test results when a
  reviewer changes weights, without re-running any tests.
- **FR-011**: System MUST persist completed reviews, including final grade, per-test grades and
  weights, and pros/cons, and make them browsable later.
- **FR-012**: System MUST present, for each completed review, a structured breakdown showing each
  test's grade, weight, and contribution alongside an aggregated pros/cons list.
- **FR-013**: System MUST include at least one AI-agent test, scoped to a specific theme, that runs
  in isolation and feeds the same weighted grading model as metric-based tests.
- **FR-014**: System MUST restrict test and weight configuration and user management to admins, and
  restrict administrative actions from reviewers.
- **FR-015**: System MUST authenticate users and distinguish the Reviewer and Admin roles.
- **FR-016**: System MUST reject empty, corrupted, or source-less submissions, and MUST refuse
  unsafe archives — those with path-traversal, absolute-path, symlink, hardlink, or device members,
  or that exceed member-count / total-uncompressed-size limits (decompression bombs) — with a clear
  message and without starting an assessment or writing unsafe content to the host.
- **FR-017**: System MUST prevent finalizing a grade when no enabled test carries a positive weight
  and inform the reviewer of the requirement.

### Key Entities *(include if feature involves data)*

- **User**: A person who signs in; holds a role of Reviewer or Admin, which governs permitted
  actions.
- **Submission**: An uploaded candidate code package under assessment; has a detected language and
  an upload identity/date.
- **Test**: A self-contained assessment unit; enabled or disabled, of type metric-based or AI-agent,
  scoped to a theme, with a default weight; produces a grade and pros/cons.
- **Review**: One assessment of a Submission; holds the set of test results, the effective weights
  (defaults plus reviewer overrides), and the computed final grade.
- **Test Result**: The outcome of one Test within a Review; includes a 0-100 grade, a failed/success
  flag, and structured pros/cons.
- **Weight Configuration**: The global default weights set by an admin and the per-review overrides
  set by a reviewer.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer can go from uploading a valid Python submission to viewing a final grade
  and breakdown without manual intervention beyond starting the assessment.
- **SC-002**: 100% of non-Python or unusable submissions are rejected with a clear explanatory
  message and never start an assessment.
- **SC-003**: Changing a test's weight on a completed review updates the displayed final grade in
  under 2 seconds, with no test re-execution.
- **SC-004**: A single failed or timed-out test never prevents the remaining tests from producing a
  final grade; the review still completes in 100% of such cases.
- **SC-005**: Every completed review remains retrievable later with its final grade, per-test
  breakdown, and pros/cons identical to when it was first produced.
- **SC-006**: 100% of test executions, including AI-agent tests, occur in isolated containers with
  no execution on the host.
- **SC-007**: Reviewers can independently apply different weights to the same submission and see
  different final grades without affecting each other.

## Assumptions

- The deployment target is a single self-hosted instance (Raspberry Pi running Ubuntu, per the
  constitution); large-scale concurrent load is out of scope for this first feature.
- Only Python submissions are assessed in this version; support for additional languages is deferred
  to a later feature.
- Authentication uses a standard session-based sign-in with two roles (Reviewer, Admin). Admin user
  management (creating users and assigning roles) is in scope for this feature; password recovery and
  external identity provider integration are assumed to follow standard practice and are not
  elaborated here.
- The initial set of tests and at least one AI-agent test are provided by admins; authoring new
  tests is governed by the existing test-plugin contract and is out of scope for this feature.
- Candidate identity is captured at upload time by the reviewer; formal candidate records or
  external HR system integration are out of scope.
- Pros and cons are derived automatically from test results only; manual reviewer annotations are
  out of scope for this version.
