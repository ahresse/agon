# Feature Specification: Git Commit Quality Assessment

**Feature Branch**: `003-git-quality-assessment`

**Created**: 2026-08-27

**Status**: Draft

**Input**: User description: "assess the quality of the commits, git commit messages, and whether commits are signed — as a candidate assessment test folded into the weighted grade."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reviewer sees a git-quality grade for a submission with history (Priority: P1)

A reviewer uploads a candidate archive that contains a git history (`.git`). Among the executed
tests is a git-quality test that assesses the candidate's commit practices — message quality, commit
granularity, and commit signing — and contributes a 0-100 grade with pros/cons to the same weighted
model as every other test.

**Why this priority**: Commit hygiene is a strong signal of engineering discipline that the existing
static-analysis tests do not capture. It reuses the established plugin + weighted-grading mechanics,
so it delivers new assessment value without new infrastructure.

**Independent Test**: Upload an archive whose `.git` contains a known history; confirm the git-quality
test returns a 0-100 grade with pros/cons that fold into the final weighted grade.

**Acceptance Scenarios**:

1. **Given** a submission archive containing a git history, **When** the assessment runs, **Then** the
   git-quality test executes in isolation and returns a 0-100 grade with structured pros/cons.
2. **Given** the git-quality test has completed, **When** the final grade is computed, **Then** its
   grade is included in the weighted mean using its assigned weight, like any other test.
3. **Given** two submissions with identical histories except that one has signed commits, **When**
   both are assessed, **Then** the signed submission receives a higher git-quality grade.

---

### User Story 2 - Submission without git history is scored low on git quality (Priority: P2)

A reviewer uploads a candidate archive that contains no git history. The git-quality test still runs
and reports a low grade with a clear reason, so the absence of version-control practice is reflected
rather than silently ignored.

**Why this priority**: Candidates are expected to deliver work under version control; treating a
missing history as neutral would hide a meaningful signal. It depends on User Story 1's mechanics.

**Independent Test**: Upload an archive with no `.git`; confirm the git-quality test returns a low
grade and a con explaining that no git history was found.

**Acceptance Scenarios**:

1. **Given** a submission archive with no git history, **When** the assessment runs, **Then** the
   git-quality test returns a low grade (not a crash) and a con stating no git history was found.
2. **Given** a low git-quality grade for a missing history, **When** the final grade is computed,
   **Then** it participates in the weighted mean like any other test result.

---

### Edge Cases

- The archive contains a corrupted or unreadable git repository: the test is recorded as failed
  (grade 0, flagged), the remaining tests still contribute, and the review still completes.
- The history contains a single commit: the test still produces a grade and notes limited granularity
  rather than erroring.
- Commits have empty or whitespace-only messages: these are flagged as low message quality.
- Signing information is unavailable or unverifiable for the environment: signing is reported as
  unsigned and lowers (but does not zero) the grade, and never crashes the test.
- A very large history: the test bounds how many commits it inspects so it stays within the per-test
  time limit, and notes that only a recent window was assessed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST include a git-quality assessment test that, when a submission contains a git
  history, produces a 0-100 grade with structured pros/cons and feeds the same weighted grading model
  as other tests.
- **FR-002**: The git-quality test MUST assess **commit message quality**, considering at least:
  non-empty messages, adequate subject length (neither empty nor excessively long), a concise subject
  line, and absence of placeholder/noise messages (e.g. "wip", "fix", "asdf").
- **FR-003**: The git-quality test MUST assess **commit granularity**, rewarding a history composed of
  multiple coherent commits and penalizing a single monolithic commit or a history of trivial/empty
  commits.
- **FR-004**: The git-quality test MUST assess **commit signing**, rewarding signed commits with a
  higher grade while NOT requiring signing; unsigned histories receive a lower (non-zero) grade, and
  the signing ratio is reported as evidence.
- **FR-005**: System MUST penalize a submission that contains no git history with a low git-quality
  grade and a clear explanatory con, rather than treating it as neutral or skipping the test.
- **FR-006**: The git-quality test MUST execute inside an isolated, disposable container (never on the
  host), consistent with the sandboxed-execution mandate.
- **FR-007**: If the git repository is corrupted or unreadable, the test MUST be recorded as failed
  (grade 0, flagged) without aborting the surrounding review.
- **FR-008**: The git-quality test MUST bound the number of commits it inspects to remain within the
  per-test time limit, and MUST report when only a recent window was assessed.
- **FR-009**: The git-quality grade MUST be reproducible: the same history yields the same grade.
- **FR-010**: An admin MUST be able to enable/disable the git-quality test and set its default weight,
  like any other test.

### Key Entities *(include if data involved)*

- **Commit Record**: A single commit inspected by the test — its subject, body presence, and signing
  status — derived from the submission's git history; not persisted beyond the test result.
- **Git-Quality Result**: The test's 0-100 grade plus pros/cons (message-quality, granularity, and
  signing evidence), stored as an ordinary Test Result within the Review.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a fixed git history, the git-quality test yields the same grade on every run
  (deterministic).
- **SC-002**: Given two histories identical except for signing, the all-signed history scores strictly
  higher than the unsigned one.
- **SC-003**: A submission with no git history receives a git-quality grade in the lowest quartile
  (≤ 25/100) with an explanatory con, in 100% of such cases.
- **SC-004**: A corrupted git repository never prevents the remaining tests from producing a final
  grade; the review still completes in 100% of such cases.
- **SC-005**: The git-quality test completes within the standard per-test time limit for histories up
  to the inspection bound, without host execution.

## Assumptions

- The git-quality test reads the submission's history using the git tooling available inside the
  assessment container (the container image provides `git`); no host git execution occurs.
- "Signed" means a commit carries a verifiable signature as reported by the git tooling; verifying the
  signer's identity against a trust store is out of scope — presence of a good signature suffices to
  reward it.
- Message-quality heuristics use conventional, language-agnostic rules (length, emptiness, noise
  words); enforcing a specific commit-message convention (e.g. Conventional Commits) is out of scope
  for the grade but MAY appear as non-scoring evidence.
- The default set of built-in tests from the code-review feature is reused; this feature adds one new
  metric test to that set.
- Only the committed history is assessed; working-tree state, branches, and remote metadata are out of
  scope for this version.
