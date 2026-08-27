# Phase 1 Data Model: Single-Language (Python) Stack

This feature changes how the existing experience is delivered, not what data the system stores.

## Entities

**No new or changed data entities.** All existing entities are unchanged:

- User, Submission, Test, Review, Test Result, Weight Configuration, Evidence Log.

The server-rendered web interface reads exactly the same data and read models the current JSON endpoints
use; grading, persistence, and roles are untouched (spec FR-009).

## Presentation-only view models (not persisted)

The web layer assembles the same read models already produced for the API, rendered as HTML instead of
returned as JSON:

| View | Contents (unchanged data) |
|------|---------------------------|
| Review detail page | final grade + per-test breakdown (grade, weight, contribution), aggregated pros/cons, per-test evidence log |
| Grade fragment | the recomputed final grade + per-test contributions after a weight change |
| Evidence-log fragment | a single test's evidence log (present / empty / no-log-available states) |
| History page | list of prior reviews (candidate, date, final grade, status) |
| Admin test-config page | tests with enabled state and default weight |
| Admin users page | users with roles |
| Upload page / Login page | forms |

## State transitions

None introduced. Review/result/job lifecycles are unchanged.
