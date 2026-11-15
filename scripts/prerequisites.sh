#!/bin/bash
set -euo pipefail
[[ $(uname -s) == Darwin && $EUID != 0 ]] || { echo 'Requires macOS and a non-root login user.' >&2; exit 1; }
if ! xcode-select -p >/dev/null 2>&1 || ! xcrun --find clang >/dev/null 2>&1; then
  xcode-select --install || true
  echo 'Complete the Command Line Tools installer, then rerun bootstrap. No packages were started.' >&2
  exit 1
fi
if ! command -v brew >/dev/null 2>&1 && [[ ! -x /opt/homebrew/bin/brew && ! -x /usr/local/bin/brew ]]; then
  installer=$(mktemp)
  trap 'rm -f "$installer"' EXIT
  curl --fail --silent --show-error --location https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh --output "$installer"
  /bin/bash "$installer"
fi
source scripts/brew-env.sh
"$MACRESET_BREW" --version
