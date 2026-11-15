# macreset

Restore a Mac through mise, native resources and small tasks for unsupported operations.

From this checkout, run `./macreset.sh` (equivalently `./bootstrap.sh`). It installs
mise first, then prepares CLT/Homebrew, Node LTS, packages, dotfiles, apps, Dock,
agent skills, Flux/Helm plugins and host Ollama/Pi in dependency order.
Run as your desktop login user. Complete Apple’s CLT installer and rerun if prompted.
Homebrew may request administrator access; sign in to the App Store with existing
purchases, and provision private Git SSH access before setup.

Review [bootstrap and private configuration](docs/mise-bootstrap.md) first.
Private overrides belong in ignored `mise.local.toml`. Existing `config.yml` is
preserved and blocks setup until its choices have been translated and explicitly
acknowledged. Ansible, Python/pipx bootstrap and Galaxy are no longer required.

Installed `~/bin/macreset` runs setup; `~/bin/macupdate` runs **explicit maintenance**:
Vim/Oh My Zsh updates, package upgrades/cleanup, and Mole clean/optimize/purge.
The wrappers use `~/Developer/macreset`; set `MACRESET_ROOT` for another checkout.
From the checkout, use `./bootstrap.sh maintenance`. Mole maintenance can remove
files and is never part of normal setup. All entrypoints propagate failures.

See the [native gaps and parity inventory](docs/mise-cutover.md),
[apps and Dock](docs/mise-apps.md), [dotfiles](docs/mise-dotfiles.md),
[skills and plugins](docs/mise-skills.md), and
[local model maintenance](docs/local-llm-maintenance.md).
Pi authentication remains manual through `/login`; credentials are unmanaged.

Herdr and sbx packages are installed, but this repository does **not** implement
sandbox launcher provisioning or OAuth automation. Older README claims described
unimplemented behavior. [Authentication research](docs/sandbox-auth-research.md)
is background research, not executable setup.

Setup is nontransactional: earlier successful changes remain after a failure.
Resolve the reported account, network, ownership or dirty-checkout issue and rerun.
No tests or real-Mac setup runs were performed for this migration; fresh-machine,
Intel and repeat-run compatibility remain unverified.
