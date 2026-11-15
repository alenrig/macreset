# Cutover inventory and limits

`./macreset.sh` delegates to `./bootstrap.sh`, which obtains mise independently
of Homebrew and runs `setup`. Installed `macreset` and `macupdate` wrappers use
`MACRESET_ROOT` (default `~/Developer/macreset`) and preserve exit status.
The installer temporary file is removed before the final exec. No obsolete
Ansible/Python runtime or existing nvm installation is uninstalled.

## Executable behavior accounting

| Former owner / operation | Current owner and behavior |
| --- | --- |
| Outer CLT / pipx / Ansible / Galaxy bootstrap | Outer script installs mise; `prerequisites` prepares CLT and Homebrew. CLT prompts then stops before packages until installation completes. pipx, Ansible and Galaxy bootstrap are retired. |
| Homebrew taps and formula inventory | `bootstrap.brew.taps` and `bootstrap.packages` retain the four tap sources and formula choices. Canonical go/kubernetes-cli/neovim replace aliases; flux-build keeps its qualified tap. Ansible/ansible-lint omitted; nvm replaced by mise Node LTS without deleting existing runtimes. mas/dockutil and verified Helm installation's gnupg are explicit prerequisites. |
| Optional private Brewfile | `packages` applies the user's existing `~/Brewfile` with Homebrew Bundle; `MACRESET_BREWFILE` selects another file. It remains Homebrew-owned. |
| Formula compatibility | Native apply on standard Apple Silicon; Homebrew CLI fallback for Intel/custom prefix or recognized unsupported formula features. Unknown errors, network/auth/checksum/ownership errors fail. |
| Casks and destination | Native declarations plus ownership-aware apps task; Homebrew-owned bundles remain owned by Homebrew. `/Applications` default, overridden by `MISE_BREW_CASK_OPT_APPDIR`. Intel/custom prefix and unsupported artifacts use CLI fallback. Legacy `docker` and `docker-desktop` names identify the same renamed cask and are represented once as docker-desktop. |
| Explicit unwanted apps | Apps task preserves the seven unwanted cask removals and GarageBand/iMovie MAS removals, with postconditions; no broad prune. |
| App Store inventory / upgrade-all | Native MAS declarations restore all configured IDs, then `mas upgrade` retains upgrade-all behavior (local override can disable). Account sign-in, ownership/purchases and indexing remain prerequisites. |
| Dock | dockutil task retains 21 selective removals and 13 ordered persistent apps, checks paths/positions, and preserves unrelated tiles. Apps run first. |
| Node | mise installs configured tools, selects Node LTS globally, and manages zsh activation through `.zshenv`. Existing private nvm hooks must be reviewed manually. |
| Private dotfiles and five home links | Native repo and symlink declarations preserve main branch/destinations. SSH credentials/host trust must already work; dirty checkouts and file conflicts stop safely. |
| Oh My Zsh, Vundle, 11 Vim plugins, Zsh plugins/themes | Guarded installer plus native repositories preserve refs and destinations. Only the two installer example themes are removed. Login-shell selection is manual. |
| Ghostty and custom bin files | Native managed copies from `assets/`; config 0644, utilities 0755. |
| Flux / Matt Pocock agent skills | Skills task preserves source/name inventories, global Codex/Cursor registrations, lock/content checks, repair, refresh and final verification. |
| Flux schema plugin | Plugins task preserves catalog/release validation, install/update distinction and final version verification. |
| helm-unittest (new) | Same task maintains registered `unittest`; upstream Git install for Helm 3, verified signed archive and isolated keyring for Helm 4. Replacement is staged with rollback. |
| Ollama | Local-model task retains com.macreset.ollama, loopback binding, context, logs, GUI login service, restart/recovery, bounded health checks and missing-model pull; no duplicate server. |
| Host Pi | Existing supported installs reused; missing npm install uses ignore-scripts. JSON settings preserve provider/model/thinking/Ponytail packages, backups and restrictive permissions. Credentials remain manual. |
| macupdate | Explicit maintenance task preserves Vim, Oh My Zsh, package upgrades/cleanup/outdated and Mole clean/optimize/purge, with nonzero failures propagated. |

## Maintenance ownership

`./bootstrap.sh maintenance` prepares CLT/Homebrew and configured tools; it does
not rerun private repository, app, Dock, skills or model setup. Run setup first:
maintenance expects its formula inventory, Vim, Mole and Oh My Zsh to exist.
It updates Homebrew metadata, then upgrades each configured formula through
native mise with the same narrow unsupported-feature CLI fallback as setup.
Intel/custom-prefix formulae go directly through Homebrew. Formula receipts are
shared between installers, so formula ownership is the configured inventory,
not the installer that first wrote a receipt.

Configured mise-owned casks upgrade through mise. Remaining outdated Homebrew
formulae/casks (including user/Brewfile extensions) upgrade individually, excluding
formulae and casks already assigned above. Homebrew skips mise-owned cask
receipts. Native unknown cask ownership stops maintenance for repair. No bulk
ownership transfer or reinstall occurs. MAS upgrade-all remains in setup's apps
task; maintenance does not add another MAS upgrade. Runtime and plugin/skills
updates retain their separate setup/task interfaces.

Homebrew cleanup and Mole clean/optimize/purge run only in explicit maintenance.
They may remove files and retain their interactive behavior. Disk verification is
enabled for Mole optimize. A failure stops the command; it never prints success
or exits zero unconditionally.

## Native gaps, overrides and recovery

Native mise has no matching behavior for CLT/Homebrew installation, exact Dock
selective editing, explicit cask/MAS removals and MAS upgrade-all, Oh My Zsh's
installer, skills integrity/repair, CLI plugin lifecycle, the existing Ollama
service label/health/model pull, Pi configuration, or Mole/Vim/Oh My Zsh
maintenance. Small mise-owned tasks cover these gaps. Native formula/cask
limitations and CLI fallback ownership are described above; native repository
and managed-file declarations own the cases they support.

Override maps/values in ignored `mise.local.toml`; mise merges native maps by key
and the guides explain whole-value replacements. Review `mise config ls` for
other contributing config. To stop managing a default map key, remove it in the
checkout; adding another key does not remove the original. Only present/latest
package requests are supported. Keep private `config.yml` as reference and
translate **every** choice before `MACRESET_CONFIG_MIGRATED=1 ./bootstrap.sh`.
The guard never parses/deletes YAML. See [bootstrap](mise-bootstrap.md),
[apps/Dock](mise-apps.md), [dotfiles](mise-dotfiles.md), [skills/plugins](mise-skills.md)
and [Ollama/Pi](local-llm-maintenance.md) for mappings and repair details.

Herdr launcher/OAuth settings formerly described in the README had no executable
implementation. Installing Herdr/sbx does not implement those claims; no new
sandbox provisioning or account automation is introduced.

Setup and maintenance are nontransactional. Earlier changes survive a failure;
repair the reported network, auth, receipt, file conflict or dirty checkout and
rerun. Never force clean a private repository or use broad prune to finish.
Unknown native error messages fail rather than silently choosing CLI fallback.
A partially applied native cask can require manual receipt repair. Existing
Homebrew-owned casks preserve their apps/macOS permissions; new ownership and
native update semantics differ from Homebrew. Fresh-Mac, Intel (Homebrew Tier 3),
current third-party packages/casks, App Store, signed Helm release availability,
GUI launchd and private Git compatibility remain unverified.

No tests, CLI-stub harness, setup execution or real-machine fresh/rerun acceptance
run were added or performed, per #41. Static syntax/configuration inspection is
not proof of machine parity.

References: [native formula receipts and upgrades](https://mise.jdx.dev/bootstrap/packages/brew.html),
[native cask ownership](https://mise.jdx.dev/bootstrap/packages/brew-cask.html),
[targeted native package upgrades](https://mise.jdx.dev/cli/bootstrap/packages/upgrade.html).
