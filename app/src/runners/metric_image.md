# Metric Test Container Image (T019)

Every metric-based test executes inside a fresh, disposable LXC/LXD container
(Constitution Principle II — NON-NEGOTIABLE). This document defines the toolchain
image/profile the metric plugins expect. Tool versions are pinned so grades are
reproducible (Constitution Principle I).

## Base

- LXD system container from an Ubuntu (arm64) image, e.g. `ubuntu:24.04`.
- Python 3.11 available inside the container.

## Provisioned tooling (pinned)

Installed via `pip` into the container's Python environment:

| Tool | Pinned version | Used by plugin |
|------|----------------|----------------|
| ruff | 0.6.9 | `lint_ruff` |
| radon | 6.0.1 | `complexity_radon` |
| mypy | 1.11.2 | `type_check_mypy` |
| bandit | 1.7.10 | `security_bandit` |
| black | 24.8.0 | `formatting_black` |

`stdlib_idioms` uses only the standard library `ast` module (no external tool).
`git_history` (feature 003) requires the `git` binary, installed via `apt`.

## Provisioning

```bash
lxc launch ubuntu:24.04 agon-python
lxc exec agon-python -- apt-get update
lxc exec agon-python -- apt-get install -y python3.11 python3-pip git
lxc exec agon-python -- python3.11 -m pip install \
    ruff==0.6.9 radon==6.0.1 mypy==1.11.2 bandit==1.7.10 black==24.8.0
```

Or, equivalently, run the provided script which performs the steps above and
publishes the image under the `AGON_LXD_PROFILE` alias (default `agon-python`):

```bash
./app/src/runners/provision_image.sh
```

The runner performs an availability preflight and, if the image is missing or
`lxc` is unavailable, raises an actionable error telling the operator to run the
provisioning script (or to set `AGON_USE_LOCAL_RUNNER=1` for a non-isolating dev
fallback).

The profile name is read from `settings.lxd_image_profile` (`AGON_LXD_PROFILE`).
Candidate source is injected read-only; only the structured `{grade, pros, cons}`
result is read back over the LXD API before the container is destroyed.
