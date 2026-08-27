#!/usr/bin/env bash
# Provision the Agon metric container image (Constitution II / T019).
#
# Builds a local LXD image aliased ${AGON_LXD_PROFILE:-agon-python} containing
# Python 3.11 and the pinned quality toolchain, so metric tests run in a fresh,
# disposable container per run. Idempotent: re-running refreshes the image.
#
# Usage:  ./provision_image.sh
# Requires: lxc (LXD) installed and initialized on the host.
set -euo pipefail

ALIAS="${AGON_LXD_PROFILE:-agon-python}"
BASE_IMAGE="${AGON_LXD_BASE_IMAGE:-ubuntu:24.04}"
BUILD_NAME="agon-image-build-$$"

if ! command -v lxc >/dev/null 2>&1; then
  echo "ERROR: 'lxc' not found. Install and initialize LXD first (lxd init)." >&2
  exit 1
fi

echo "==> Launching build container from ${BASE_IMAGE}"
lxc launch "${BASE_IMAGE}" "${BUILD_NAME}"

cleanup() { lxc delete "${BUILD_NAME}" --force >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "==> Waiting for network readiness"
for _ in $(seq 1 30); do
  if lxc exec "${BUILD_NAME}" -- getent hosts archive.ubuntu.com >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "==> Installing Python and pinned toolchain"
lxc exec "${BUILD_NAME}" -- bash -eux <<'IN'
export DEBIAN_FRONTEND=noninteractive
apt-get update
# Use the distro's default python3 (>=3.11 on supported Ubuntu releases:
# 3.11 on 22.04/jammy, 3.12 on 24.04/noble). Both satisfy requires-python>=3.11.
apt-get install -y python3 python3-pip
python3 -m pip install --break-system-packages \
    ruff==0.6.9 radon==6.0.1 mypy==1.11.2 bandit==1.7.10 black==24.8.0
python3 --version
IN

echo "==> Stopping and publishing image as alias '${ALIAS}'"
lxc stop "${BUILD_NAME}"
lxc image delete "${ALIAS}" >/dev/null 2>&1 || true
lxc publish "${BUILD_NAME}" --alias "${ALIAS}"

echo "==> Done. Image '${ALIAS}' is ready."
echo "    Set AGON_LXD_PROFILE=${ALIAS} (default) so the runner uses it."
