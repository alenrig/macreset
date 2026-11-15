#!/usr/bin/env bash
set -euo pipefail

omz="$HOME/.oh-my-zsh"
if [[ ! -e "$omz" && ! -L "$omz" ]]; then
  installer_dir=$(mktemp -d "${TMPDIR:-/tmp}/macreset-omz.XXXXXX")
  installer="$installer_dir/install.sh"
  trap 'rm -rf "$installer_dir"' EXIT
  curl --fail --silent --show-error --location \
    https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh \
    --output "$installer"
  # Preserve private startup files and do not replace the running setup with zsh.
  ZDOTDIR="$installer_dir" ZSH="$omz" KEEP_ZSHRC=yes RUNZSH=no CHSH=no sh "$installer"
fi
if [[ ! -f "$omz/oh-my-zsh.sh" || ! -x "$omz/tools/upgrade.sh" ]]; then
  echo "Incomplete Oh My Zsh installation at $omz; repair it before rerunning." >&2
  exit 1
fi

# OMZ's sample files otherwise prevent the native Dracula clone into this directory.
# Never modify an existing repository here: native repo apply must inspect its dirt.
themes="$omz/custom/themes"
if [[ ! -e "$themes/.git" ]]; then
  for example in example.zsh example.zsh-theme; do
    if [[ -f "$themes/$example" || -L "$themes/$example" ]]; then
      rm -- "$themes/$example"
    fi
  done
fi
