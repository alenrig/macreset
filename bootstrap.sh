#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
[[ $(uname -s) == Darwin ]] || { echo 'macreset requires macOS.' >&2; exit 1; }
[[ $EUID != 0 ]] || { echo 'Run macreset as your login user, not root.' >&2; exit 1; }
# This release documents the native bootstrap package and shell resources we use.
required=2026.11.8
mise_bin=$(command -v mise || true)
[[ -n $mise_bin ]] || mise_bin="$HOME/.local/bin/mise"
version=''
if [[ -x $mise_bin ]]; then
  version=$("$mise_bin" --version | awk 'NR == 1 { print $1 }')
fi
if [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] ||
   [[ $(printf '%s\n%s\n' "$required" "$version" | sort -t. -k1,1n -k2,2n -k3,3n | head -1) != "$required" ]]; then
  installer=$(mktemp)
  trap 'rm -f "$installer"' EXIT
  curl --fail --silent --show-error --location https://mise.run --output "$installer"
  MISE_VERSION="v$required" MISE_INSTALL_PATH="$HOME/.local/bin/mise" sh "$installer"
  mise_bin="$HOME/.local/bin/mise"
  rm -f "$installer"
  trap - EXIT
fi
"$mise_bin" --version
export MACRESET_MISE="$mise_bin"
export PATH="$(dirname "$mise_bin"):$PATH"
if [[ -e config.yml && ${MACRESET_CONFIG_MIGRATED:-} != 1 ]]; then
  echo 'config.yml exists. Translate its private overrides to mise.local.toml; see docs/mise-bootstrap.md.' >&2
  echo 'After reviewing every setting, run with MACRESET_CONFIG_MIGRATED=1 (config.yml is preserved).' >&2
  exit 1
fi
"$mise_bin" trust mise.toml
if [[ -f mise.local.toml ]]; then "$mise_bin" trust mise.local.toml; fi
if [[ $# == 0 ]]; then set -- setup; fi
exec "$mise_bin" run "$@"
