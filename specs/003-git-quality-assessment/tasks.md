---
description: "Task list for Git Commit Quality Assessment"
---

# Tasks: Git Commit Quality Assessment

**Input**: Design documents from `/specs/003-git-quality-assessment/`

**Prerequisites**: plan.md, spec.md

**Tests**: Included (unit + real-repo), organized into clear topic subsections (pytest classes).

## Phase 1: Implementation

- [X] T001 Implement git_history plugin: git-log parsing, message/granularity/signing scoring (signing rewarded, not required), no-git penalty, corrupted-repo error, bounded inspection window in backend/src/tests_plugins/quality/git_history.py
- [X] T002 Register the git-quality plugin in the built-in set (auto-seeded as an enabled METRIC test) in backend/src/tests_plugins/quality/builtin.py
- [X] T003 Add the `git` binary to the metric container image in backend/src/runners/provision_image.sh
- [X] T004 [P] Document the git dependency for the metric image in backend/src/runners/metric_image.md

## Phase 2: Tests

- [X] T005 [P] Unit tests in topic subsections (parsing, message quality, granularity, signing, no-git penalty, malformed repo, determinism, real-repo end-to-end) in backend/tests/unit/test_git_quality.py
- [X] T006 [P] Include the git-quality plugin in the quality-plugin conformance parametrization in backend/tests/contract/test_quality_plugins.py

## Dependencies & Notes

- T001 blocks T002/T005; T003/T004 are independent image changes.
- The plugin folds into the existing weighted-grading model with no core changes (Constitution III).
- git executes only inside the disposable container (Constitution II); the image rebuild via
  provision_image.sh is required before real containerized runs include this test.
