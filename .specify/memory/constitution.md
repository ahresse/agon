<!--
SYNC IMPACT REPORT
Version change: template (unversioned) → 1.0.0
Bump rationale: Initial ratification of the Agon project constitution.
Modified principles:
  - [PRINCIPLE_1_NAME] → I. Measurable Assessment
  - [PRINCIPLE_2_NAME] → II. Sandboxed Execution (NON-NEGOTIABLE)
  - [PRINCIPLE_3_NAME] → III. Extensible Test Framework
  - [PRINCIPLE_4_NAME] → IV. Weighted, Transparent Grading
  - [PRINCIPLE_5_NAME] → V. Portable & Self-Hostable
Added sections:
  - Additional Constraints
  - Development Workflow
  - Governance (populated)
Removed sections: none
Deferred TODOs: none
-->

# Agon Constitution

## Core Principles

### I. Measurable Assessment
Every test MUST produce an objective, reproducible numeric grade derived from measurable
metrics. Each test MUST declare a weight and MUST emit supporting evidence for the grade it
returns. Subjective-only or non-reproducible scoring is prohibited; any judgment-based signal
MUST be reduced to a quantified, repeatable metric before it can contribute to a grade.
Rationale: Candidate assessments must be fair, defensible, and comparable across runs, which is
only possible when grades trace back to deterministic measurements.

### II. Sandboxed Execution (NON-NEGOTIABLE)
All candidate code and all AI agents MUST execute inside LXC/LXD containers. No candidate code
or agent process MAY run directly on the host. Each execution context MUST be isolated and
disposable so that one assessment cannot affect another or the host environment.
Rationale: Assessed code and AI agents are untrusted; containerization is the only acceptable
boundary protecting host integrity, reviewer safety, and result isolation.

### III. Extensible Test Framework
Tests MUST be self-contained plugins that conform to a stable contract: they receive a weight
and produce a grade with evidence. Adding, removing, or modifying a test MUST NOT require
changes to the framework core. Support for additional assessed languages (Python is the first
supported language) MUST be added through this same contract rather than through special cases.
Rationale: A stable plugin contract keeps the framework maintainable and lets the supported test
and language set grow without destabilizing existing assessments.

### IV. Weighted, Transparent Grading
The final grade MUST be computed as the weighted mean of individual test grades. Reviewers MAY
assign custom weights per test. The frontend MUST present a structured breakdown, including a
list of pros and cons and the per-test contribution, so that every final grade is explainable
from its inputs.
Rationale: Reviewers and candidates must be able to understand and trust how a final grade was
reached; opaque aggregation undermines the tool's credibility.

### V. Portable & Self-Hostable
The full stack (web frontend and backend) MUST be deployable on a Raspberry Pi running Ubuntu
(arm64). Resource footprint is a first-class design constraint: features MUST NOT assume
hardware beyond this target. Portability regressions MUST be treated as defects.
Rationale: Self-hosting on modest, affordable hardware is a core promise of the tool and must
remain viable as the system evolves.

## Additional Constraints

- Architecture MUST separate a backend service from a web-based frontend.
- The deployment target is a Raspberry Pi running Ubuntu (arm64); all components MUST run there.
- Containerization via LXC/LXD is mandatory for every code-execution and AI-agent path.
- Python is the initially supported assessed language; additional languages MUST integrate
  through the test contract defined in Principle III.
- AI-agent tests are scoped to specific, well-defined themes, MUST always run containerized, and
  MUST feed their results into the same weighted grading model as metric-based tests.

## Development Workflow

- New tests MUST declare their weight, grading scale, and evidence format, and MUST produce
  reproducible output, before they can be merged.
- Any change introducing or altering an execution path (candidate code or AI agent) MUST have
  its container isolation verified during review.
- Frontend changes MUST preserve the structured breakdown and the pros/cons contract.
- Every change MUST be checked for Raspberry Pi / Ubuntu (arm64) portability; changes that break
  self-hosting MUST NOT be merged.

## Governance

This constitution supersedes other development practices where they conflict. Amendments MUST be
documented with rationale, approved by project maintainers, and accompanied by a version bump.

Versioning follows semantic versioning: MAJOR for backward-incompatible removal or redefinition
of a principle or governance rule; MINOR for a newly added principle or section or materially
expanded guidance; PATCH for clarifications and non-semantic refinements.

Compliance is enforced at review time: every pull request review MUST verify adherence to the
Sandboxed Execution, Measurable Assessment, and Portable & Self-Hostable principles, and MUST
justify any added complexity.

**Version**: 1.0.0 | **Ratified**: 2026-08-26 | **Last Amended**: 2026-08-26
