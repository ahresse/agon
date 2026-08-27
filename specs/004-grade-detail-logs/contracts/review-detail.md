# Contract: Review Detail view (evidence log)

Extends the review-detail view (the per-review breakdown from feature 001). Each per-test result gains an
optional `log` value. Authorization is unchanged: only users authorized to view the review can see its
detail and logs (FR-008, SC-004).

## Per-test result (extended)

| Field | Type | Notes |
|-------|------|-------|
| test id | string | unchanged |
| test name | string | unchanged |
| grade | number | unchanged |
| status | success \| failed | unchanged |
| effective weight | number | unchanged |
| contribution | number | unchanged |
| pros | string[] | unchanged |
| cons | string[] | unchanged |
| **log** | **string \| absent** | **Evidence behind the grade. absent = no log captured (pre-feature result); empty = ran, no extra evidence; non-empty = evidence text.** |

## Example (abridged)

```json
{
  "id": "rev-1",
  "final_grade": 78.0,
  "results": [
    {
      "test_id": "t-lint",
      "test_name": "Lint",
      "grade": 77.78,
      "status": "SUCCESS",
      "effective_weight": 1.0,
      "contribution": 11.1,
      "pros": [],
      "cons": ["1 lint violation (unused local variable)."],
      "log": "main.py:6: unused local variable 'y'"
    }
  ],
  "pros": ["…"],
  "cons": ["…"]
}
```

## Behavior

- The field is **additive**; consumers that ignore `log` continue to work.
- Recomputing the grade on a weight change does **not** modify `log` (Principle IV — logs are evidence,
  not grading inputs).
- No new retrieval path is introduced; the log rides on the already-authorized review-detail view.
