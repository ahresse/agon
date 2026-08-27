# Phase 1 Data Model: End-to-End Candidate Code Review Flow

Derived from the Key Entities and Functional Requirements in [spec.md](./spec.md). Attributes are
described conceptually; concrete column types are an implementation detail.

## Entities

### User

Represents a person who signs in.

| Field | Description | Rules |
|-------|-------------|-------|
| id | Unique identifier | Required, unique |
| username | Sign-in identity | Required, unique |
| role | `REVIEWER` or `ADMIN` | Required; governs permissions (FR-014, FR-015) |
| created_at | Creation timestamp | Required |

- Admin-only actions (test config, global weights, user management) are denied to Reviewers.

### Test

A self-contained assessment plugin (Principle III). Configured by admins.

| Field | Description | Rules |
|-------|-------------|-------|
| id | Unique identifier | Required, unique |
| key | Stable plugin key | Required, unique; maps to a registered plugin |
| name | Human-readable name | Required |
| type | `METRIC` or `AI_AGENT` | Required |
| theme | Focus area (esp. for AI-agent tests) | Required for `AI_AGENT` |
| enabled | Whether it runs in new assessments | Required; default true |
| default_weight | Global default weight | Required; ≥ 0 (FR-008) |

- Only enabled tests execute in a new Review (FR-008).
- At least one `AI_AGENT` test exists in the configured set (FR-013).

### Submission

An uploaded candidate code package.

| Field | Description | Rules |
|-------|-------------|-------|
| id | Unique identifier | Required, unique |
| candidate_label | Reviewer-provided candidate identity | Required |
| detected_language | Auto-detected language | Required; must be `python` to proceed (FR-002) |
| storage_path | Location of stored archive/files | Required |
| uploaded_by | User id (Reviewer) | Required |
| uploaded_at | Upload timestamp | Required |

- Non-Python, empty, corrupted, or source-less uploads are rejected before a Review is created
  (FR-002, FR-016). Each upload is a distinct Submission even for the same candidate.

### Review

One assessment of a Submission by/for a reviewer.

| Field | Description | Rules |
|-------|-------------|-------|
| id | Unique identifier | Required, unique |
| submission_id | The assessed Submission | Required |
| reviewer_id | Owning Reviewer | Required |
| status | `PENDING`, `RUNNING`, `COMPLETED`, `FAILED` | Required |
| final_grade | Weighted mean (0-100) | Computed; null until at least one result exists |
| created_at | Creation timestamp | Required |
| completed_at | Completion timestamp | Set when all results finalize |

- `final_grade` is a pure function of this Review's `TestResult`s and effective weights (FR-006).
- Different Reviewers assessing the same Submission hold independent Reviews (FR-009, SC-007).

**Status transitions**:
`PENDING → RUNNING → COMPLETED`
`RUNNING → FAILED` (only if every test fails; final_grade = 0 with all results flagged, per edge
cases). Grade may recompute at any point after the first result completes.

### TestResult

Outcome of one Test within a Review.

| Field | Description | Rules |
|-------|-------------|-------|
| id | Unique identifier | Required, unique |
| review_id | Parent Review | Required |
| test_id | The executed Test | Required |
| grade | 0-100 score | Required; 0 if failed/timed-out (FR-005, FR-007) |
| status | `SUCCESS` or `FAILED` | Required; `FAILED` covers crash/timeout (FR-007) |
| pros | Structured positive findings | Derived from the test result |
| cons | Structured negative findings | Derived from the test result |
| ran_at | Execution timestamp | Required |

- A `FAILED` result keeps grade 0 but retains its weight in the mean (FR-007).

### WeightConfiguration

Effective weights = global defaults overlaid with per-review reviewer overrides.

| Field | Description | Rules |
|-------|-------------|-------|
| review_id | Review the override applies to | Required for overrides |
| test_id | Test being weighted | Required |
| weight | Override weight | ≥ 0 (FR-009) |

- Global defaults live on `Test.default_weight`; a `WeightConfiguration` row overrides that value for
  a single Review only, never affecting defaults or other reviews (FR-009).
- The effective weight for a test in a review = override weight if present, else `Test.default_weight`.
- Finalizing a grade requires at least one enabled test with a positive effective weight (FR-017).

## Relationships

```text
User (Reviewer) 1───* Submission
User (Reviewer) 1───* Review
Submission      1───* Review
Review          1───* TestResult
Test            1───* TestResult
Review          1───* WeightConfiguration
Test            1───* WeightConfiguration
```

## Derived computations

- **Effective weight(review, test)** = override in `WeightConfiguration` if present, else
  `Test.default_weight`.
- **Final grade(review)** = Σ(grade_i × effective_weight_i) / Σ(effective_weight_i) over the review's
  test results, computed only when Σ(effective_weight_i) > 0 (else undefined → blocked per FR-017).
- Recomputation reads persisted `TestResult`s only; it never triggers re-execution (FR-010, SC-003).
