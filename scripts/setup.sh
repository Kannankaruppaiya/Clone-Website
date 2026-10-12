#!/usr/bin/env bash
# Installs the `pwc` CLI that the perfect-web-clone skill drives.
# Pinned to the upstream commit these skills were copied from (licenses/UPSTREAM.txt).
set -euo pipefail

PWC_COMMIT="c846c37937a70497d37d082c26c85aa1289a9fa5"

if command -v pwc >/dev/null 2>&1; then
  echo "pwc already installed: $(command -v pwc)"
  exit 0
fi

python3 -m pip install --quiet "git+https://github.com/ericshang98/Perfect-Web-Clone.git@${PWC_COMMIT}"

# Claude Code cloud containers ship Chromium at $PLAYWRIGHT_BROWSERS_PATH; elsewhere, fetch it.
if [ -z "${PLAYWRIGHT_BROWSERS_PATH:-}" ]; then
  python3 -m playwright install chromium
fi

echo "pwc installed: $(command -v pwc)"
