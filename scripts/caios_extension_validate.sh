#!/usr/bin/env bash
# Local-only CAIOS Chrome extension validation. Does not use GitHub Actions.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required; use the existing Node installation on Nexus Forge." >&2
  exit 1
fi
echo "CAIOS extension local validation: no GitHub Actions runner will be started."
npm ci
npm run build
npm run test-extension
