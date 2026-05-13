---
name: requirement-writer
description: Expert requirements engineer. Writes atomic, RFC 2119-compliant, Doorstop-compatible YAML requirements with mandatory headers, traceability, evaluation protocols, and safety guardrails.
---

## What I do
- Write single-capability requirements that are verifiable and traceable
- Produce Doorstop-compatible YAML requirement files following solution conventions
- Distinguish deterministic requirements from probabilistic ones with explicit evaluation protocols
- Define guardrails, observability conditions, and human-in-the-loop escalation criteria for AI-agent interactions
- Enforce atomicity, taxonomy consistency, and normative vocabulary per RFC 2119

## When to use me
Use this skill when creating new requirements, decomposing compound requirements, refining existing ones, or converting user stories into formal specifications.
Always verify the requirement is specific, measurable, and traceable to a parent need or stakeholder request.

---

## 1. Requirement Lifecycle (always follow)

Before writing any YAML, answer these four questions in prose:

1. **What is the single capability or constraint?** (one sentence)
2. **Who or what is the actor?** (system, user, AI agent, CLI, container, …)
3. **Under what preconditions and postconditions?** (state before / state after)
4. **How do we know it is satisfied?** (testable, observable, or measurable criterion)

Only after answering all four may you generate the Doorstop YAML.

---

## 2. Mandatory YAML Schema

Every solution requirement file MUST contain these exact top-level keys. Never omit a key.

| Key | Type | Cardinality | Description |
|-----|------|-------------|-------------|
| `active` | bool | 1 | `true` for published requirements; `false` for drafts or retired requirements |
| `derived` | bool | 1 | `true` if derived from a lower-level design decision; `false` if originating from a stakeholder need |
| `header` | string | 1 | Human-readable summary (max 80 chars). Must NOT be empty. |
| `level` | string | 1 | Doorstop level string, e.g. `1.1`, `2.3.1` |
| `links` | list[str] | 0..* | Doorstop traceability links to parent requirements (`PREFIX###`). MUST NOT be empty for derived requirements. SHOULD contain at least one link for stakeholder-originated requirements when a parent need exists. |
| `normative` | bool | 1 | `true` for requirements that carry SHALL/SHALL NOT/SHOULD/MAY. `false` for informative notes or glossary entries |
| `ref` | string | 1 | External reference (Jira ticket, PR number, RFC, meeting minutes). Empty string if none. |
| `reviewed` | str / null | 1 | Doorstop review hash or `null` if unreviewed |
| `text` | str | 1 | The normative statement. Single capability only. |
| `evaluation` | dict | 0..1 | **Mandatory for probabilistic or AI-agent requirements.** Optional but recommended for deterministic requirements (see §6). |

### Evaluation sub-schema (when present)

```yaml
evaluation:
  type: deterministic | probabilistic
  method: <specific_method>
  success_criteria: <how_pass_is_defined>
  failure_mode: <what_happens_on_failure>
  guardrails: <list_of_safety_checks>
  human_escalation: <when_human_must_be_notified>
```

| Key | Type | Description |
|-----|------|-------------|
| `type` | enum | `deterministic` (exact, reproducible pass/fail) or `probabilistic` (statistical, model-based, subjective) |
| `method` | string | Concrete verification method: `unit_test`, `integration_test`, `exit_code_assertion`, `stdout_regex_match`, `model_inference_with_temperature`, `human_review`, `monte_carlo_sampling`, ... |
| `success_criteria` | string | Quantitative or qualitative pass threshold. MUST be unambiguous. |
| `failure_mode` | string | System behavior when the criterion is not met: `abort`, `degrade`, `escalate`, `retry_with_backoff`, `zero_grade`, ... |
| `guardrails` | string or list | Safety boundaries that apply during evaluation (timeouts, input sanitization, sandbox constraints). |
| `human_escalation` | string | Condition that triggers human review. Use `"never"` only if formally justified. |

---

## 3. Atomicity Rule

**One requirement = one capability or one constraint.**

If the `text` field contains:
- more than one actor performing more than one action,
- multiple symmetric capabilities joined with "and" or commas,
- both a functional behavior and a failure-handling behavior,
- both a user-facing CLI flag and an internal algorithm,

then the requirement is compound and MUST be split before publication.

### Decomposition examples

**Bad (compound):**
> SOLUTION V2 shall assess source archives inside ephemeral LXD containers, support the definition and execution of atomic tests with injection, assign grades on a 0-20 scale, aggregate grades with configurable weights, and produce a final summary grade.

**Good (decomposed into 5 requirements):**
- REQ-Archive-Sandbox: "SOLUTION V2 SHALL assess source archives inside ephemeral LXD containers."
- REQ-Atomic-Test-Def: "SOLUTION V2 SHALL support the definition and execution of atomic tests with injection."
- REQ-Grade-Scale: "SOLUTION V2 SHALL assign grades on a 0–20 scale."
- REQ-Grade-Aggregation: "SOLUTION V2 SHALL aggregate grades with configurable weights."
- REQ-Summary-Grade: "SOLUTION V2 SHALL produce a final summary grade."

---

## 4. Taxonomy & Naming

Use the solution project vocabulary consistently. Do not invent synonyms.

| Term | Definition | Never call it |
|------|------------|-------------|
| **SOLUTION V2** | The assessment framework/system as a whole. | "the tool", "the script" (in normative text) |
| **atomic test** | The smallest indivisible assessment unit. | "test case", "check", "sub-test" |
| **test-suite preset** | A named bundle of atomic tests with default weights. | "profile", "template", "preset" (inconsistently) |
| **deterministic test** | A test whose grade is computed by an exact evaluator function. | "objective test", "hard test" |
| **agent-based test** | A test whose grade is produced by an external AI Agent. | "subjective test", "AI test", "soft test" |
| **LXD container** | An ephemeral Ubuntu container launched for isolation. | "VM", "docker container", "sandbox" |
| **source archive** | A `.tar.gz`, `.zip`, or equivalent uploaded for assessment. | "zip file", "tarball", "upload" |
| **grade** | Numeric score on the 0–20 scale. | "score", "mark", "rating" |
| **weight** | Relative coefficient used during grade aggregation. | "multiplier", "factor" |
| **injection** | Dynamic insertion of auxiliary files into the container. | "patch", "injection mechanism" (vague) |
| **setup phase** | Pre-test steps (apt install, file upload, extraction) executed before atomic tests. | "bootstrap", "initialization" |

Always define a new term in an informative (non-normative) requirement or glossary entry before using it normatively.

---

## 5. RFC 2119 Normative Vocabulary

solution requirements MUST use only these four normative keywords. **Never use "must", "will", "should", "can", "may" except as defined below.**

| Keyword | Meaning | Usage in solution |
|---------|---------|---------------|
| **SHALL** / **SHALL NOT** | Absolute obligation / absolute prohibition. The system is non-compliant if violated. | Behavioral guarantees, safety invariants, data integrity. |
| **SHOULD** / **SHOULD NOT** | Strong recommendation. Implies a documented, justified exception path. | Defaults, conventions, optimizations. If an exception exists, it MUST be documented. |
| **MAY** | Truly optional. Interoperability must not be broken if the feature is absent. | Optional CLI flags, optional output formats, convenience features. |

### Strict usage rules

1. Every normative requirement (`normative: true`) MUST contain at least one keyword from the set {`SHALL`, `SHALL NOT`, `SHOULD`, `SHOULD NOT`, `MAY`}.
2. A single requirement SHOULD contain only ONE normative keyword to preserve atomicity. If two keywords are necessary, justify it in the `ref` field.
3. SHALL and SHOULD MUST NOT appear in the same requirement unless the scope is clearly partitioned (e.g., a main clause with an exception sub-clause).
4. "Must", "will", "can", "should" (lowercase), and "may" (lowercase) SHALL NOT be used as normative substitutes.
5. All keywords SHALL appear in ALL CAPS.

---

## 6. Deterministic vs Probabilistic Requirements

Every requirement that describes a verification or grading behavior MUST declare its evaluation nature.

### Deterministic
- Pass/fail is objectively reproducible.
- Same inputs → same output.
- Examples: exit-code checks, regex matches, file existence, deterministic algorithm results.

**Evaluation protocol (recommended):**
```yaml
evaluation:
  type: deterministic
  method: exit_code_assertion
  success_criteria: exit code is 0
  failure_mode: assign zero grade and log stderr
  guardrails: container timeout of 300s; input path validated with pathlib.Path.exists()
  human_escalation: container timeout exceeds 300s
```

### Probabilistic
- Pass/fail depends on a stochastic process, model inference, or subjective judgment.
- Examples: AI-agent grading, LLM-based reasoning, sampling-based checks, heuristic thresholds.

**Evaluation protocol (mandatory):**
```yaml
evaluation:
  type: probabilistic
  method: model_inference_with_temperature
  success_criteria: grade ∈ [0, 20] with textual reasoning attached
  failure_mode: escalate to human review if grade variance > 4 points across 3 runs
  guardrails:
    - max_tokens: 4096
    - temperature: 0.3
    - sandbox: LXD container with network egress blocked
  human_escalation: grade < 5 or grade > 18, or reasoning text is empty
```

**Rule:** If a requirement involves an AI agent (agent-based tests), the `evaluation` block is **mandatory**.

---

## 7. Guardrails, Observability, and Escalation

Any requirement that delegates judgment to an AI agent or performs destructive operations (container deletion, network access, file system mutation) MUST explicitly define:

1. **Guardrails** — hard limits that prevent harm:
   - Timeouts (e.g., max 300s per atomic test)
   - Resource ceilings (CPU, RAM, disk)
   - Network restrictions (egress blocked by default)
   - Input validation (archive format whitelist, path traversal checks)

2. **Observability** — signals emitted for monitoring:
   - Structured logs (JSON lines with identifier, timestamp, grade)
   - Exit codes for CI/CD integration
   - Container state snapshots before deletion (if `--keep-container` is absent)

3. **Human Escalation** — clear trigger conditions:
   - Grade variance above threshold across reruns
   - AI reasoning absent or contradictory
   - Container lifecycle anomaly (fail to start, fail to delete)
   - Any non-zero exit code during setup phase that is not explicitly handled

If a requirement does not involve AI agents or destructive operations, it MAY omit the `evaluation` block, but SHOULD still mention basic guardrails (timeouts, input validation) in the `text` field when relevant.

---

## 8. Traceability Rules

1. Every requirement SHOULD link to at least one parent need via `links`.
2. If a requirement is `derived: true`, `links` MUST contain at least one valid Doorstop link.
3. Link format: `PREFIX###` (e.g., `REQ001`, `STK042`). No file extensions.
4. If no parent exists because the requirement originates from a direct stakeholder request, set `derived: false` and document the source in `ref`.
5. When decomposing a compound requirement, every child MUST link to the parent.

---

## 9. Prohibited Patterns (Anti-Patterns)

Violating any of these patterns makes a requirement invalid for the solution catalog.

| # | Anti-Pattern | Example from solution catalog | Consequence |
|---|--------------|---------------------------|-------------|
| 1 | **Compound requirement** | REQ001 bundles archive assessment, test injection, grading, aggregation, and summary into one sentence. | Cannot be independently verified or traced. |
| 2 | **Empty header** | All existing REQs have `header: ''` | Impossible to browse or index requirements meaningfully. |
| 3 | **No traceability** | All `links: []` | No impact analysis possible when parent needs change. |
| 4 | **Ambiguous grading range** | REQ005 says "numeric score in the range [0, 20]" but does not specify integer vs float, precision, or inclusive boundaries. | Implementation divergence. |
| 5 | **Missing failure mode** | REQ010 describes automatic package installation but omits what happens when installation fails beyond "skip the test" — no timeout, no retry, no escalation. | Unpredictable system behavior under stress. |
| 6 | **No evaluation protocol for AI** | REQ006 describes agent-based tests without guardrails, temperature, or escalation. | Non-reproducible and unsafe AI grading. |
| 7 | **Informal vocabulary** | REQ012 uses "unless the user explicitly requests" instead of "unless the user specifies the `--keep-container` option". | Ambiguous contract between user and system. |
| 8 | **Mixed scopes** | REQ015 combines setup failure handling, grade assignment, and CLI crash avoidance in one requirement. | Hard to test and hard to trace. |

---

## 10. Editorial Checklist (before saving any YAML)

Run through this checklist before committing a requirement:

- [ ] `header` is non-empty and ≤ 80 characters.
- [ ] `text` describes exactly one capability or one constraint.
- [ ] At least one RFC 2119 keyword appears in ALL CAPS in `text`.
- [ ] All solution taxonomy terms are used consistently (see §4).
- [ ] `derived` and `links` are coherent: derived reqs have ≥ 1 link.
- [ ] If AI-agent or probabilistic: `evaluation` block is present and complete.
- [ ] If destructive operations: guardrails and human escalation are specified.
- [ ] `ref` contains a source trace (ticket, PR, meeting) or is `""` with justification.
- [ ] `level` follows the correct Doorstop hierarchy and does not duplicate existing levels.
- [ ] No informal normative words ("must", "will", "can") appear in `text`.

---

## Appendix A: YAML Template

```yaml
active: true
derived: false
header: 'Short imperative summary here'
level: '1.X'
links:
  - REQ001
normative: true
ref: ''
reviewed: null
text: |
  SOLUTION V2 SHALL <single capability> under <preconditions>.
evaluation:
  type: deterministic
  method: <method_name>
  success_criteria: <quantitative or qualitative threshold>
  failure_mode: <system behavior on failure>
  guardrails: <safety constraints>
  human_escalation: <trigger condition or "never">
```

---

## Appendix B: Refactored Examples

### Example B1 — Deterministic Requirement (based on REQ002, refactored)

**Before:**
```yaml
header: ''
text: |
  SOLUTION V2 shall accept an archive file (e.g. .tar.gz or .zip), upload it into a
  fresh LXD container, extract it, and make the source tree available for
  assessment.
```

**After:**
```yaml
active: true
derived: false
header: 'Archive upload and extraction to LXD container'
level: '1.2'
links:
  - REQ001
normative: true
ref: ''
reviewed: null
text: |
  SOLUTION V2 SHALL accept a source archive from the host filesystem, upload it into
  a fresh LXD container, extract it at the configured extraction path, and make
  the resulting source tree readable for subsequent atomic tests.
evaluation:
  type: deterministic
  method: integration_test
  success_criteria: |
    After execution, the container contains the extracted source tree at the
    configured path with at least one file and exit code 0 from the extraction
    command.
  failure_mode: abort assessment and log the extraction error
  guardrails:
    - supported archive formats limited to .tar.gz, .zip
    - extraction path validated against path traversal
    - container readiness confirmed via cloud-init status --wait
  human_escalation: container fails to reach ready state within 120s
```

### Example B2 — Probabilistic / AI-Agent Requirement (based on REQ006, refactored)

**Before:**
```yaml
header: ''
text: |
  SOLUTION V2 shall support agent-based tests for subjective criteria (e.g. comment
  quality or documentation clarity).  An external AI Agent shall receive the test
  prompt together with the extracted source tree (or relevant excerpts), produce a
  numeric grade in the range [0, 20], and append a textual reasoning explaining
  the awarded score.
```

**After (split into 3 atomic requirements):**

**REQ-Agent-Input:**
```yaml
active: true
derived: true
header: 'AI agent receives test prompt and source excerpts'
level: '1.6.1'
links:
  - REQ006
normative: true
ref: ''
reviewed: null
text: |
  SOLUTION V2 SHALL provide the AI agent with the test prompt and relevant excerpts
  from the extracted source tree before grading begins.
evaluation:
  type: deterministic
  method: stdout_assertion
  success_criteria: prompt and excerpts are present in the agent input context
  failure_mode: abort agent-based test with zero grade
  guardrails: excerpt size capped at 128 KiB; source tree path validated
  human_escalation: source tree read fails with permission denied
```

**REQ-Agent-Grade:**
```yaml
active: true
derived: true
header: 'AI agent produces numeric grade and reasoning'
level: '1.6.2'
links:
  - REQ006
normative: true
ref: ''
reviewed: null
text: |
  The AI agent SHALL produce a numeric grade in the closed interval [0, 20] and
  SHALL append a textual reasoning justifying the awarded grade.
evaluation:
  type: probabilistic
  method: model_inference_with_temperature
  success_criteria: |
    grade is a number in [0, 20] with ≤ 2 decimal places; reasoning text is
    non-empty and ≥ 20 characters.
  failure_mode: escalate to human review; do not persist grade
  guardrails:
    - temperature: 0.3
    - max_tokens: 4096
    - network egress blocked for the inference call
  human_escalation: |
    grade < 5 or grade > 18, reasoning missing, or grade variance > 4 points
    across 3 independent runs
```

**REQ-Agent-Aggregation:**
```yaml
active: true
derived: true
header: 'Agent-based grade included in weighted aggregation'
level: '1.6.3'
links:
  - REQ007
  - REQ-Agent-Grade
normative: true
ref: ''
reviewed: null
text: |
  SOLUTION V2 SHALL include every approved agent-based grade in the weighted final
  grade aggregation using the weight configured for that atomic test.
evaluation:
  type: deterministic
  method: unit_test
  success_criteria: |
    weighted final grade is recomputed correctly when an agent-based grade is
    added, removed, or modified.
  failure_mode: abort aggregation and emit structured error log
  guardrails: weight values validated as positive finite numbers
  human_escalation: aggregation result is NaN or infinite
```

### Example B3 — Guardrails-Only Requirement (based on REQ012, refactored)

**Before:**
```yaml
header: ''
text: |
  SOLUTION V2 shall delete the ephemeral LXD container after all assessments finish,
  unless the user explicitly requests to keep it for post-mortem inspection.
```

**After:**
```yaml
active: true
derived: false
header: 'Ephemeral LXD container is deleted after assessment'
level: '1.12'
links:
  - REQ001
normative: true
ref: ''
reviewed: null
text: |
  SOLUTION V2 SHALL delete the ephemeral LXD container after all atomic tests
  complete, unless the user specified the `--keep-container` CLI flag.
evaluation:
  type: deterministic
  method: integration_test
  success_criteria: |
    container name does not appear in `lxc list` within 30s of test completion
    when `--keep-container` is absent.
  failure_mode: emit critical warning log and retry deletion once with backoff
  guardrails:
    - deletion timeout: 30s
    - force flag forbidden (prevent data loss on mounted volumes)
    - pre-deletion snapshot captured if `--keep-container` is used
  human_escalation: deletion fails after retry or container enters ERROR state
```

---

## Appendix C: Mission Statement

> solution requirements exist so that every capability can be independently verified, traced to a need, and safely evaluated — whether by a deterministic script or a probabilistic AI agent. Ambiguity is a bug. Compound requirements are a debt. Safety is not optional.
