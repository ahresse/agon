# Feature Specification: One-Command, Host-Safe Deployment with Local Web Access

**Feature Branch**: `002-one-command-deploy`

**Created**: 2026-08-27

**Status**: Draft

**Input**: User description: "the solution should be deployable without impact to the host system in one command line. Then, the web interface should be accessible locally"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Operator deploys Agon in a single command (Priority: P1)

An operator with a fresh, supported host obtains the Agon project and runs a single command
to bring the whole solution up. The command provisions everything Agon needs inside isolated,
disposable boundaries so that nothing is installed into, or left behind on, the host beyond the
project's own directory. When the command finishes, it reports that Agon is running and prints the
local address where the web interface can be reached.

**Why this priority**: A frictionless, host-safe bring-up is the entry point to every other Agon
capability. Without a reliable one-command deploy, self-hosting on modest hardware is impractical
and the tool cannot be adopted. It is the minimum viable outcome of this feature on its own.

**Independent Test**: On a clean supported host, run the single deploy command and confirm it
completes successfully, reports the running status, and prints a reachable local web address —
without the operator running any additional setup steps.

**Acceptance Scenarios**:

1. **Given** a clean supported host with the prerequisites present, **When** the operator runs the
   single deploy command, **Then** the full solution (web interface and its backing services) starts
   and the command reports success with the local web address to open.
2. **Given** the deploy command is running, **When** it provisions Agon's runtime, **Then** all
   components run inside isolated, disposable boundaries and nothing is installed onto the host
   system outside the project directory.
3. **Given** a first-ever deployment on a host, **When** the command completes, **Then** initial
   data (default accounts and the built-in assessment set) is present so the operator can sign in and
   use Agon immediately.

---

### User Story 2 - Reviewer/Admin reaches the web interface locally (Priority: P1)

After deployment, a user on the same machine (or on the local network per configuration) opens the
web interface at the printed local address and reaches the Agon sign-in screen, then proceeds to use
the application normally.

**Why this priority**: Deployment only delivers value if the interface is actually reachable.
Local accessibility is the immediate, observable proof that the deployment succeeded and is the
gateway to all reviewer and admin workflows.

**Independent Test**: With Agon deployed, open the printed local address in a browser on the host and
confirm the Agon web interface loads and the sign-in screen is presented.

**Acceptance Scenarios**:

1. **Given** Agon has been deployed successfully, **When** a user opens the printed local address in a
   browser on the host, **Then** the Agon web interface loads and presents the sign-in screen.
2. **Given** the web interface is loaded, **When** the user signs in with a valid default account,
   **Then** they reach the appropriate home view for their role.
3. **Given** the deployment is configured for local-only access, **When** the address is requested,
   **Then** it is served on the local machine and not unintentionally exposed to the public internet.

---

### User Story 3 - Operator stops and cleanly removes the deployment (Priority: P2)

An operator stops the running deployment and removes it, confirming that the host is returned to its
prior state with no residual services, packages, or system changes left behind (persisted Agon data
is removed or retained according to an explicit choice).

**Why this priority**: "No impact to the host" is only credible if teardown is equally clean. Clean
removal protects the host and lets operators trust repeated deploy/redeploy cycles, but it follows a
successful deploy rather than preceding it.

**Independent Test**: Deploy Agon, then run the stop/remove action and confirm no Agon services keep
running and no host-level changes persist outside the project directory.

**Acceptance Scenarios**:

1. **Given** a running deployment, **When** the operator issues the stop action, **Then** all Agon
   components stop and the local web address is no longer served.
2. **Given** a stopped deployment, **When** the operator issues the remove action, **Then** the
   isolated runtime is destroyed and the host retains no Agon-installed services or system changes
   outside the project directory.
3. **Given** removal is requested, **When** the operator chooses to keep data, **Then** persisted
   reviews and configuration survive for a later redeploy; **and when** they choose a full clean,
   **Then** persisted data is also removed.

---

### Edge Cases

- A required prerequisite is missing on the host: the deploy command stops early with a clear message
  naming what is missing and how to provide it, and makes no partial changes to the host.
- The default local port/address is already in use: the command reports the conflict clearly and
  either selects an available alternative or instructs the operator how to choose one, rather than
  failing silently.
- The deploy command is interrupted midway: re-running it converges to a healthy running state
  (idempotent) without requiring manual cleanup of half-created resources.
- The web interface is opened before the backing services are fully ready: the user sees a clear
  "starting up" indication rather than a broken page, and the interface becomes usable once ready.
- The host is rebooted while Agon is deployed: the operator can restore the running state with the
  same single command (or a documented equivalent) without reconfiguring from scratch.
- Deployment is attempted on an unsupported host or architecture: the command detects this and refuses
  with a clear explanation rather than proceeding in a degraded or unsafe way.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The solution MUST be deployable to a running state with a single command-line invocation,
  requiring no additional manual setup steps for a first successful start.
- **FR-002**: Deployment MUST NOT install software into, modify, or leave residual changes on the host
  system outside the project's own directory; all runtime components MUST run inside isolated,
  disposable boundaries.
- **FR-003**: On completion, the deploy command MUST report whether the solution started successfully
  and MUST print the local address at which the web interface can be reached.
- **FR-004**: The web interface MUST be reachable locally at the reported address immediately after a
  successful deployment, presenting the Agon sign-in screen.
- **FR-005**: A first-ever deployment MUST provision initial data (default accounts and the built-in
  assessment set) so the operator can sign in and use Agon without further configuration.
- **FR-006**: The deploy command MUST verify required prerequisites before making changes and, if any
  are missing or the host/architecture is unsupported, MUST stop with a clear message and make no
  partial host changes.
- **FR-007**: Deployment MUST be idempotent: re-running the command MUST converge to a healthy running
  state without manual cleanup, whether starting fresh or recovering from an interrupted attempt.
- **FR-008**: The solution MUST provide a single-action way to stop the running deployment such that no
  Agon components keep running and the local address is no longer served.
- **FR-009**: The solution MUST provide a way to remove the deployment that destroys the isolated
  runtime and leaves no Agon-installed services or host changes outside the project directory.
- **FR-010**: Removal MUST offer an explicit choice to either retain persisted Agon data (reviews and
  configuration) for a later redeploy or remove it entirely.
- **FR-011**: When the default local address or port is unavailable, the deploy command MUST detect the
  conflict and either select an available alternative or clearly instruct the operator how to choose
  one, rather than failing silently.
- **FR-012**: Deployment MUST be configurable to restrict the web interface to local-only access so it
  is not unintentionally exposed beyond the intended local scope.
- **FR-013**: The deployment MUST expose a health indication so that a user opening the interface
  before services are ready sees a clear "starting up" state rather than a broken page.
- **FR-014**: After a host reboot, the operator MUST be able to restore the running deployment using the
  same single command (or a documented equivalent) without reconfiguring from scratch.

### Key Entities *(include if data involved)*

- **Deployment**: A running instance of the whole Agon solution created by the single command; has a
  status (starting, running, stopped) and an associated local access address.
- **Local Access Endpoint**: The local address/port at which the web interface is served, together with
  its access scope (local-only vs. local network).
- **Persisted Data Set**: The Agon data that can survive redeploys (reviews, configuration, accounts),
  distinct from the disposable runtime, and subject to the retain-or-remove choice at teardown.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can go from a clean supported host to a running Agon with a reachable web
  interface using exactly one command and no additional manual setup steps.
- **SC-002**: 100% of deployments leave the host with no installed services or system changes outside
  the project directory, verifiable by comparing host state before and after deploy-then-remove.
- **SC-003**: After a successful deploy, the printed local address serves the Agon sign-in screen on
  the host on the first attempt in 100% of successful deployments.
- **SC-004**: The single deploy command reaches a running, reachable state within 10 minutes on the
  target hardware for a first-ever deployment.
- **SC-005**: Re-running the deploy command on an already-deployed or partially-deployed host converges
  to a healthy running state in 100% of cases without manual cleanup.
- **SC-006**: A stop-and-remove action returns the host to a state with no Agon components running and
  no residual host changes in 100% of cases, with persisted data retained or removed exactly as the
  operator chose.
- **SC-007**: When the default local port is occupied, the deploy command surfaces the conflict and a
  clear resolution path in 100% of such cases rather than failing without explanation.

## Assumptions

- The deployment target is the constitution's supported environment: a single self-hosted instance on
  a Raspberry Pi running Ubuntu (arm64). Broader OS/architecture support is out of scope for this
  feature.
- "One command line" means a single documented command the operator runs from the project directory;
  the operator has already obtained the project (e.g., cloned it) and has the documented prerequisites
  available on the host.
- "No impact to the host system" means no persistent, host-wide installation or configuration changes
  outside the project directory; using the host's already-required isolation capability (per the
  constitution's containerized-execution mandate) to run disposable components is expected and in scope.
- Isolation and disposability of runtime components rely on the same container mechanism the
  constitution already mandates for code execution; standing up that mechanism itself, if absent, is a
  documented prerequisite rather than something this command silently installs onto the host.
- "Accessible locally" means reachable from a browser on the host by default, with an explicit option
  to broaden to the local network; public-internet exposure is out of scope and intentionally avoided.
- Default sign-in accounts and the built-in assessment set from the existing review-flow feature are
  reused as the initial data provisioned on first deploy.
- Secure production hardening beyond local/self-hosted use (e.g., public TLS, external identity
  providers) is out of scope for this feature.
