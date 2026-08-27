# Contract: Test Output Log Extension

Extends the existing test contract (weight-in / grade-out,
`specs/001-code-review-flow/contracts/test-plugin-contract.md`) with an optional evidence log. Backward
compatible — existing tests need no change.

## Test output (extended)

| Field | Type | Rules |
|-------|------|-------|
| grade | number | 0-100, required (unchanged) |
| pros | string[] | Structured positive findings (unchanged) |
| cons | string[] | Structured negative findings (unchanged) |
| **log** | **string** | **Optional (default empty). Human-readable evidence behind the grade. For a passing test: a focused excerpt of the concrete findings (with location) that drove the grade, not the tool's full raw output. For a failure: a sanitized reason first, then the full raw error output beneath. Plain text only.** |

Rules:

- `log` is **optional**; a test that omits it yields an empty log and is fully valid (Principle III).
- The framework caps the captured `log` at **256 KiB**, truncating with a trailing `… [log truncated]`
  marker if longer.
- `log` MUST be plain text; it is transported and presented as inert text (no embedded markup executes,
  FR-009). Control characters are preserved but shown safely.

## Result carried back from the execution boundary (extended)

The result returned from the isolated execution boundary already carries the grade and findings; it now
also carries `log`:

```json
{ "grade": 77.78, "pros": ["…"], "cons": ["…"], "log": "main.py:6: unused local variable 'y'\n…" }
```

- The log is read back alongside `grade`/`pros`/`cons` through the same channel.
- On crash/timeout the framework records a failed result with `grade = 0`, leading the `log` with a
  sanitized failure reason and appending the full raw error output beneath it (FR-005, FR-007).

## Failure and empty semantics

| Situation | `log` value | Reviewer sees |
|-----------|-------------|----------------|
| Test recorded findings | focused excerpt of findings | the text (preformatted) |
| Test ran, nothing to report | empty | "No additional evidence" |
| Test failed / timed out | sanitized reason + raw error | reason first, raw output beneath |
| No assessable input | "no assessable input" reason | the reason |
| Result predates this feature | absent | "No log available for this result" |
