# Feature Specification: Single-Language (Python) Stack — Eliminate JavaScript

**Feature Branch**: `005-python-only-stack`

**Created**: 2026-08-27

**Status**: Draft

**Input**: User description: "avoid using javascript. Everythings should be done in one langage only. Python is prefered"

## Clarifications

### Session 2026-08-27

- Q: Does the "no JavaScript" rule forbid all browser-delivered JavaScript, or only JavaScript the project authors, builds, or maintains? → A: Forbid only project-authored/built/maintained JavaScript and its toolchain; a single vendored, non-authored helper library (served as a static asset, no build step) is allowed.
- Q: For preserving "instant re-grade" on a weight change, is a partial server-driven in-place update acceptable, or must it avoid any full-page navigation like today? → A: Partial, server-driven in-place update (the grade area re-renders without full-page navigation).
- Q: Should the existing separate web client and its JavaScript tooling be deleted entirely, or archived/kept out of the build? → A: Deleted entirely (rely on git history if ever needed).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Maintainer works in a single language across the whole system (Priority: P1)

A maintainer of Agon can read, change, test, and run every part of the system — including the web
interface a reviewer uses — using one implementation language (Python), without needing to learn,
build, or maintain a separate JavaScript/TypeScript toolchain. All existing reviewer- and admin-facing
behavior (upload, weighted grade with per-test breakdown and pros/cons, weight overrides, history,
admin configuration, evidence logs) continues to work exactly as before.

**Why this priority**: A single-language codebase is the whole point of this change. It lowers the
barrier to contribution, shrinks the build/runtime toolchain on the self-hosted target, and removes an
entire class of duplicated concepts (types, models, validation) split across two languages. Without it,
none of the other benefits materialize. It is the minimum viable outcome.

**Independent Test**: Check out the project, and confirm every buildable/runnable/testable part of the
system — backend and the web interface alike — is implemented in the single chosen language, with no
JavaScript/TypeScript source or JavaScript package/build tooling required to run the whole application.

**Acceptance Scenarios**:

1. **Given** the whole project, **When** a maintainer inventories its source and build/run tooling,
   **Then** the web interface and backend are implemented in one language and no JavaScript/TypeScript
   source files or JavaScript package/build toolchain are required to build or run the application.
2. **Given** a running deployment produced by the single-language stack, **When** a reviewer performs
   the existing end-to-end flow (sign in, upload, view weighted grade + per-test breakdown + pros/cons +
   evidence logs, override weights, browse history), **Then** every step works with the same outcomes as
   before this change.
3. **Given** an admin using the deployment, **When** they configure tests/weights and manage users,
   **Then** those capabilities work as before.

---

### User Story 2 - Reviewer uses the web interface with no behavioral regression (Priority: P1)

A reviewer interacts with the web interface exactly as they do today — the pages, actions, and displayed
information are equivalent — even though the interface is now delivered by the single-language stack
rather than a separate JavaScript application.

**Why this priority**: The language consolidation must be invisible to end users. If any reviewer- or
admin-facing capability regresses, the change has failed regardless of internal cleanliness. This is
co-critical with User Story 1.

**Independent Test**: Run the pre-change acceptance scenarios for uploading, grading, weight override,
history, admin config, and evidence-log viewing against the single-language deployment and confirm
identical outcomes.

**Acceptance Scenarios**:

1. **Given** the single-language deployment, **When** the reviewer uploads a submission and opens the
   completed review, **Then** the final weighted grade, per-test breakdown (grade, weight, contribution),
   aggregated pros/cons, and expandable evidence logs are all presented as before.
2. **Given** a completed review, **When** the reviewer changes a test's weight, **Then** the final grade
   recomputes and the grade area updates in place (a partial, server-driven update) without a full-page
   navigation, as it does today.
3. **Given** a non-Python or unsafe submission, **When** the reviewer uploads it, **Then** it is rejected
   with the same clear messaging as before.

---

### User Story 3 - Operator deploys the single-language stack with a smaller toolchain (Priority: P2)

An operator deploys and runs the whole application on the self-hosted target without installing or
building a JavaScript runtime or JavaScript package ecosystem, reducing the number of tools and steps
required to stand the system up.

**Why this priority**: A key benefit of one language is a lighter deployment footprint on modest
hardware. It depends on the consolidation (User Story 1) being complete first.

**Independent Test**: On a clean supported host, deploy and run the application and confirm no JavaScript
runtime or JavaScript package/build tooling is needed at any point.

**Acceptance Scenarios**:

1. **Given** a clean supported host, **When** the operator builds and runs the application, **Then** no
   JavaScript runtime or JavaScript package/build tool is required to complete the process.
2. **Given** the running application, **When** the operator inspects what is installed to serve the web
   interface, **Then** it is served by the single-language stack without a separate JavaScript build
   artifact.

---

### Edge Cases

- A part of the current experience relied on rich in-browser interactivity (e.g. instant weight re-grade
  without a full page change): the single-language interface MUST preserve the *observable behavior* by
  re-rendering the affected area in place via a partial, server-driven update (no full-page navigation),
  using server rendering and/or the single vendored non-authored helper — with no JavaScript authored,
  built, or maintained by the project.
- Third-party components historically pulled in as JavaScript dependencies: the feature MUST NOT
  reintroduce a JavaScript toolchain to satisfy them; equivalent single-language capabilities are used
  instead, or the capability is delivered without client-side scripting.
- Existing automated checks that targeted the separate JavaScript interface: these MUST be replaced by
  equivalent checks in the single language so the web interface remains covered.
- Any generated or vendored JavaScript that ships incidentally with a platform component: it MUST NOT
  require the project to author, build, or maintain JavaScript, and MUST NOT be counted as project
  source in the single-language guarantee.
- A future contributor attempts to add JavaScript/TypeScript: the project's guardrails make this an
  explicit, reviewable deviation rather than something that slips in unnoticed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST be implemented in a single implementation language across both the backend
  and the web interface, with Python as that language.
- **FR-002**: The project MUST NOT contain any JavaScript or TypeScript **authored, built, or maintained
  by the project**, nor require a JavaScript package manager or JavaScript build toolchain, to build or
  run the whole application. A single **vendored, non-authored** helper library MAY be served as a static
  asset (no build step) to enable interactivity; it is not counted as project source.
- **FR-003**: The web interface MUST be delivered by the single-language stack (server-rendered) rather
  than by a separately built JavaScript client application.
- **FR-004**: All existing reviewer- and admin-facing capabilities MUST be preserved with equivalent
  observable behavior: authentication and roles; submission upload with language/format validation and
  safe extraction; asynchronous assessment; final weighted grade with per-test breakdown (grade, weight,
  contribution) and aggregated pros/cons; per-test evidence logs (including failure/no-input reasons);
  per-review weight override with grade recomputation; review history; and admin test/weight/user
  configuration.
- **FR-005**: Interactivity that previously depended on authored JavaScript (e.g. instant re-grade on
  weight change, expanding a test's evidence log) MUST remain available to the reviewer with equivalent
  observable outcomes, delivered without JavaScript authored, built, or maintained by the project — using
  server-driven updates and/or a single vendored, non-authored helper library served as a static asset.
- **FR-006**: Automated test coverage MUST exist in the single language for the web interface's behavior,
  replacing any coverage that previously targeted the separate JavaScript interface, so no covered
  behavior becomes uncovered by this change.
- **FR-007**: The deployment/run process MUST NOT depend on a JavaScript runtime or JavaScript package/
  build ecosystem at any step.
- **FR-008**: The project MUST include a guardrail that surfaces any newly introduced JavaScript/
  TypeScript source or JavaScript build tooling as an explicit, reviewable deviation.
- **FR-009**: The migration MUST NOT change the grading model, the test set/plugin contract, the data
  retained for reviews, or user roles; it changes only the delivery language of the interface and removes
  the JavaScript toolchain.
- **FR-010**: Incidentally generated or vendored JavaScript that ships as part of a reused platform
  component MUST NOT require the project to author, build, or maintain JavaScript, and MUST be excluded
  from the single-language source guarantee.
- **FR-011**: The existing separate web client and its JavaScript build/test tooling MUST be removed from
  the project entirely (relying on version-control history if ever needed), so nothing JavaScript-based
  remains to build, run, or maintain.

### Key Entities *(include if data involved)*

No new data entities. This feature changes how the existing experience is delivered, not what data the
system stores. Existing entities (User, Submission, Test, Review, Test Result, Weight Configuration,
Evidence Log) are unchanged.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the project's build-, run-, and test-relevant **project-authored** source is in the
  single chosen language; the count of project-authored JavaScript/TypeScript source files is zero (a
  vendored, non-authored helper asset, if present, is excluded from this count).
- **SC-002**: The whole application can be built and run with zero JavaScript runtime or JavaScript
  package/build tools installed.
- **SC-003**: 100% of the pre-change reviewer- and admin-facing acceptance scenarios pass unchanged
  against the single-language deployment (no behavioral regression).
- **SC-004**: Every web-interface behavior that had automated coverage before the change has equivalent
  automated coverage in the single language after the change (no net loss of covered behaviors).
- **SC-005**: The number of distinct tool ecosystems required to build and run the system is reduced
  (the JavaScript ecosystem is fully removed), measurable as one fewer package/build toolchain.
- **SC-006**: An attempt to introduce JavaScript/TypeScript into the project is flagged by the guardrail
  in 100% of cases before it is accepted.

## Assumptions

- "One language" refers to the language the project authors and maintains. Incidental, non-authored
  assets that a reused platform component may ship (and that require no JavaScript toolchain from the
  project) do not violate the single-language guarantee.
- The project constitution's requirement to "separate a backend service from a web-based frontend" is
  satisfied by a server-rendered web interface delivered by the single-language stack; "web-based
  frontend" is not read as mandating JavaScript.
- Python is the chosen single language, consistent with the rest of the system and the assessed domain.
- The visual layout and content of the web interface remain equivalent; pixel-perfect fidelity is not
  required, but no reviewer- or admin-facing capability may be lost.
- Minimal interactivity may be achieved with platform-provided, non-authored mechanisms (e.g. standard
  form submissions or lightweight server-driven updates) so long as the project neither authors nor
  builds JavaScript.
- Removing the separate JavaScript interface and its toolchain is in scope; the existing web client and
  its JavaScript tooling are deleted entirely (recoverable from version-control history). Redesigning the
  user experience beyond preserving existing behavior is out of scope for this feature.
- This change is compatible with, and does not alter the intent of, the one-command deployment and the
  self-hosted (Raspberry Pi / Ubuntu) target.
