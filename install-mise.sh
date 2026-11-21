#!/bin/sh
set -eu

installer=$(mktemp)
trap 'rm -f "$installer"' EXIT
curl -fsSL https://mise.run -o "$installer"
install_path="$HOME/.local/bin/mise"
MISE_INSTALL_PATH="$install_path" MISE_INSTALL_HELP=0 sh "$installer"
test -x "$install_path"
printf 'mise executable: %s\n' "$install_path"
