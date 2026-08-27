# Implementation Plan: Git Commit Quality Assessment

**Branch**: `003-git-quality-assessment` | **Date**: 2026-08-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-git-quality-assessment/spec.md`

## Summary

Add a built-in metric test that grades a candidate submission's git history on message quality,
commit granularity, and signing (signing rewarded, not required). It reuses the existing test-plugin
contract and weighted-grading model: the plugin runs inside the disposable LXD container against the
extracted `.git`, emits a 0-100 grade with pros/cons, and folds into the final weighted mean like any
other test. Submissions without a git history are penalized with a low grade; corrupted repositories
isolate to a FAILED result without aborting the review.

## Technical Context

**Language/Version**: Python 3.11 (backend)

**Primary Dependencies**: existing stack (FastAPI, SQLAlchemy); the `git` binary inside the metric
container image (added to `provision_image.sh` / `metric_image.md`)

**Storage**: unchanged — the git-quality outcome is an ordinary `TestResult`

**Testing**: pytest — pure scoring/parsing unit tests plus end-to-end tests against tiny real repos

**Target Platform**: Raspberry Pi / Ubuntu (arm64), single self-hosted instance

**Project Type**: Web application (backend plugin addition; no frontend change — the admin test-config
page lists tests dynamically)

**Constraints**: git execution happens inside the container (Constitution II); inspection is bounded
to a recent commit window to respect the per-test timeout

## Constitution Check

| Principle | Gate | Status |
|-----------|------|--------|
| I. Measurable Assessment | Deterministic 0-100 grade from measurable commit signals | PASS — pure scoring over parsed commits; determinism test |
| II. Sandboxed Execution | git runs only inside the disposable container | PASS — plugin invokes git inside the runner; image provides git |
| III. Extensible Test Framework | New test is a plugin, no core change | PASS — registered via the plugin registry/builtin list |
| IV. Weighted, Transparent Grading | Folds into weighted mean with pros/cons evidence | PASS — standard PluginOutput |
| V. Portable & Self-Hostable | Only adds the `git` package to the image | PASS — git is a small, native dependency |

## Project Structure

```text
backend/src/tests_plugins/quality/git_history.py   # the plugin (parse + score + git invocation)
backend/tests/unit/test_git_quality.py             # topic-organized unit + real-repo tests
backend/src/runners/provision_image.sh             # + git in the image
backend/src/runners/metric_image.md                # documents git dependency
```

**Structure Decision**: Extend the existing `tests_plugins/quality/` package with one new plugin,
registered in `builtin.py` (auto-seeded). Scoring and parsing are pure functions, separated from the
git subprocess call, so they are unit-testable without a repository.

## Complexity Tracking

> No constitution violations. Table intentionally empty.
