# Contributing to Agon

## Commit conventions

Agon's own git history is checked by repo-hygiene meta-tests
(`app/tests/meta/test_repo_commit_quality.py`). Please follow these rules so
those tests stay green.

### Enforced (tests fail otherwise)

- **Conventional subject**: `type(scope): summary`, where `type` is one of
  `feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert`.
  The scope is optional, e.g. `feat(app): add job queue`.
- **Subject length** ≤ 80 characters.
- **No empty subjects** and **no empty commits** (each commit must change files).
- **Atomic history**: split work into multiple coherent commits rather than one
  monolith.

### Report-only (informational, never fails)

- **Signing**: commit signing is reported as a ratio but not required. Signing is
  encouraged; if you sign, use your own key. Commits in this project are created
  unsigned by default.

## Running the checks

```bash
cd app && pytest tests/meta        # repo-hygiene + no-JavaScript guardrail
cd app && pytest                    # full app suite (incl. web interface)
```

The project is single-language (Python); there is no JavaScript to build or test.
The meta-tests are skipped automatically when not run inside a git repository
(e.g. shallow clones or tarball builds).

## Note on candidate git assessment

Separately from these repo-hygiene checks, Agon includes a **candidate-facing**
git-quality assessment (feature `003-git-quality-assessment`): when a candidate's
uploaded submission contains a `.git` history, a metric test grades their commit
message quality, granularity, and signing, folding into the weighted grade. That
is a product feature and is unrelated to the contribution rules above.
