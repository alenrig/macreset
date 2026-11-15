# Source from mise-owned tasks; discovery candidates are not assumed prefixes.
if command -v brew >/dev/null 2>&1; then
  MACRESET_BREW=$(command -v brew)
elif [[ -x /opt/homebrew/bin/brew ]]; then
  MACRESET_BREW=/opt/homebrew/bin/brew
elif [[ -x /usr/local/bin/brew ]]; then
  MACRESET_BREW=/usr/local/bin/brew
else
  echo 'Homebrew is missing; run mise run prerequisites first.' >&2
  return 1
fi
HOMEBREW_PREFIX=$("$MACRESET_BREW" --prefix) || return
export MACRESET_BREW HOMEBREW_PREFIX
export PATH="$HOMEBREW_PREFIX/bin:$HOMEBREW_PREFIX/sbin:$PATH"
