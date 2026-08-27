# Contract: Server-Rendered Web UI Routes

The web interface is delivered as server-rendered HTML pages plus HTML **fragments** for interactive
actions (swapped in place by the vendored htmx helper). All routes reuse existing services, session
auth, and access rules. The JSON API from prior features is unchanged and may coexist.

## Conventions

- **Pages** return a full HTML document (rendered from a shared base template).
- **Fragments** return an HTML partial (no `<html>` wrapper) for in-place swapping.
- Auth: unauthenticated page requests redirect to the login page; admin-only routes enforce the existing
  admin guard (non-admins receive a forbidden response / redirect).
- The vendored helper is served as a static asset and is the only browser-delivered script; the project
  authors no JavaScript.

## Page routes

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | `/` | Redirect to review history (or login) | session |
| GET | `/login` | Login form | public |
| POST | `/login` | Establish session, then redirect | public |
| POST | `/logout` | Clear session, redirect to login | session |
| GET | `/ui/upload` | Upload form (candidate label + archive) | reviewer |
| POST | `/ui/upload` | Accept upload, create review, redirect to its detail | reviewer |
| GET | `/ui/reviews` | Review history list | reviewer |
| GET | `/ui/reviews/{id}` | Review detail: final grade + per-test breakdown + pros/cons + evidence logs | owner |
| GET | `/ui/admin/tests` | Admin: test configuration (enable/disable, default weight) | admin |
| POST | `/ui/admin/tests/{id}` | Apply test config change | admin |
| GET | `/ui/admin/users` | Admin: user management | admin |
| POST | `/ui/admin/users` | Create user | admin |
| POST | `/ui/admin/users/{id}` | Update user role | admin |

## Fragment routes (in-place updates)

| Method | Path | Returns | Behavior |
|--------|------|---------|----------|
| POST | `/ui/reviews/{id}/weights` | Grade fragment | Apply weight override, recompute from stored results, swap the updated grade/breakdown area in place (no full-page navigation). Rejects all-zero weights with an inline message. |
| GET | `/ui/reviews/{id}/tests/{test_id}/log` | Evidence-log fragment | Return the test's evidence log (present / "No additional evidence" / "No log available"), expanded in place. |

## Static asset

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/static/vendor/htmx.min.js` | Vendored, non-authored helper enabling background requests + fragment swapping |

## Behavioral parity requirements

- The review-detail page MUST present the same structured breakdown (per-test grade, weight,
  contribution), aggregated pros/cons, and expandable evidence logs as the prior client (Principle IV,
  spec FR-004).
- Weight change MUST update the grade in place without full-page navigation (spec FR-005, clarified).
- Rejection messaging for invalid uploads and all-zero weights MUST match prior behavior.
- Access control MUST match prior rules: reviewers see only their own reviews; admin routes are
  admin-only (spec FR-004/FR-008).
