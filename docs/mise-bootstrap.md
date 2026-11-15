# Mise bootstrap migration

From the checkout, run `./bootstrap.sh` or `./macreset.sh`. The outer script
installs or reuses mise 2026.11.8 or newer, then delegates the complete setup to
mise. Ansible is retired. See [cutover parity and native gaps](mise-cutover.md)
for the operation inventory and maintenance ownership.

Run as your login user on macOS. CLT installation is interactive: if missing,
setup starts Apple's installer and stops before package work. Complete it and
rerun. Homebrew may request an administrator password. Downloads, unavailable
packages and permission failures stop the run; prior successful work remains.
No formulae or existing nvm/Node installations are uninstalled. Existing shell
configuration may still activate nvm; remove that activation yourself after
reviewing your private dotfiles so it cannot shadow mise's Node.

## Private overrides

`mise.local.toml` is ignored and loaded after `mise.toml` by mise. Use that one
local file consistently; review `mise config ls` to see any global, parent or
environment-specific configuration that also participates. Native maps merge
by key; overriding a package's value changes its request, adding a key adds a
package. This formula runner supports `latest`/present only and fails on other
requests rather than silently skipping them. To stop managing a default
formula, remove its declaration in your checkout; that does not uninstall it.
Do not use prune to migrate the inventory.

For example:

```toml
[bootstrap.packages]
"brew:jq" = "latest"

[tools]
node = "lts"
```

The tools task installs configured tools, refreshes Node to the latest version
matching the configured LTS request on every run, and selects Node LTS globally
so it works outside this checkout. It preserves previously installed runtimes
and leaves other tools at their configured install behavior. For a different
global Node policy, override the `tools` task in your local config as well as
`[tools]`. Native line entries in `.zshenv`
add `~/.local/bin` and activate mise for interactive zsh without editing the
private linked startup files. Open a new shell to pick up startup changes. Setup tasks already
use the known mise executable and its runtime environment without a new shell.

`config.yml` is preserved and blocks the new entrypoint until you have reviewed
and translated **every** private choice. `MACRESET_CONFIG_MIGRATED=1
./bootstrap.sh` explicitly acknowledges that review; it does not parse YAML.
Keep the YAML as a private reference; it is never parsed or deleted.
The same guard applies to explicit maintenance through the public bootstrap.

| Legacy setting | New owner |
| --- | --- |
| `homebrew_taps` | `[bootstrap.brew.taps]`, tap name to Git URL |
| `homebrew_installed_packages` | `[bootstrap.packages]` `brew:` entries |
| `golang`, `kubectl`, `nvim` | Canonical formula names `go`, `kubernetes-cli`, `neovim` |
| `flux-build` | Fully qualified `doodlescheduling/flux-build/flux-build` |
| nvm role/runtime choice | `[tools] node = "lts"`, global selection and native shell activation |
| Ansible / ansible-lint | Omitted; installed copies remain untouched |
| `homebrew_brewfile_dir` | `[env] MACRESET_BREWFILE` (full path); defaults to `~/Brewfile` |
| Other YAML settings | See the apps, dotfiles, skills and local-model guides linked in mise-cutover.md |

## Task interface and ordering

Automatic task tool installation is disabled so prerequisites run first.
The shared chain is `prerequisites` → `tools` → `packages` → `terminal` → `native`.
`apps` follows native resources and `dock` follows apps. `local-llm` follows
native resources, `skills` follows tools, and `plugins` follows packages.
`setup` waits for dock, skills, plugins and local-llm; independent branches may
run concurrently. Every dependent operation runs in the first invocation.
`./bootstrap.sh packages` can run a phase with its dependencies. Scripts source
`scripts/brew-env.sh` after prerequisites to obtain `MACRESET_BREW`,
`HOMEBREW_PREFIX`, and prefix-based PATH. The two conventional brew locations
are discovery candidates only; the actual prefix comes from `brew --prefix`.
`MACRESET_MISE` identifies the executable chosen by the outer bootstrap.

Apps depend on packages (including mas); Dock follows apps; skills/Pi depend
on tools; service/model readiness follows Ollama installation. Native resource application
is `mise bootstrap --skip packages,tools,task`: package work and tools have
already run, avoiding recursive orchestration. Do not invoke plain `mise
bootstrap` as a substitute for the ordered `setup` task.

## Native gaps and unverified compatibility

- Homebrew itself and CLT require mise-owned prerequisite tasks.
- Native formula management skips Intel Macs. The package runner reads mise's
  merged native package status inventory and uses `brew install --formula` for
  every declared formula on Intel or with a nonstandard Homebrew prefix. This includes prerequisites mas and dockutil.
- On Apple Silicon each formula uses native apply first. Only a documented
  unsupported formula-feature error permits Homebrew CLI fallback; other errors
  remain failures. Fully qualified names retain tap provenance and Homebrew
  auto-taps them when needed. Declared tap URLs retain all four legacy sources.
- Source-build DSL and post-install support differ from Homebrew. A new native
  error wording may require extending the narrow fallback recognition; do not
  convert arbitrary failures into fallback. Unknown failure messages stop setup.
- The legacy Homebrew role also applied a user-owned `~/Brewfile` when present.
  The packages task retains that optional extension using `brew bundle --file`;
  set `MACRESET_BREWFILE` in local `[env]` for a different path. Its dependencies
  and behavior remain Homebrew-owned. This is not a repository Brewfile inventory.
- Native receipts are Homebrew-compatible. Formula verification uses `brew list`
  after each install. No formula cleanup, uninstall or broad prune occurs during setup. Explicit
app removals and MAS upgrade-all retain the prior setup behavior; package and
Mole cleanup belong only to `maintenance`.
- Intel Homebrew is upstream Tier 3. Current bottles, third-party formula
  availability, shell edits and first-run/rerun parity have not been verified on
  a real Mac. No tests or machine acceptance run are required or added by #41.

Sources: [mise installation](https://mise.jdx.dev/installing-mise.html),
[bootstrap phases](https://mise.jdx.dev/bootstrap.html),
[native formula support and gaps](https://mise.jdx.dev/bootstrap/packages/brew.html),
[shell activation](https://mise.jdx.dev/bootstrap/shell.html),
[package status](https://mise.jdx.dev/cli/bootstrap/packages/status.html),
[Homebrew installation](https://docs.brew.sh/Installation).
