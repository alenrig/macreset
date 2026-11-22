# Package setup

Run `./bootstrap` on Apple Silicon macOS as your login user. The `packages`
task uses mise's native Homebrew formula and cask managers. It uses Ruby 3.4
from mise to read the third-party taps and Apple's Command Line Tools for tap
formulae with no bottles. On a clean Mac, mise may ask for administrator
permission to create `/opt/homebrew` or to install cask artifacts. Homebrew
itself is optional for the automatic setup.

Add `/opt/homebrew/bin` to PATH in your shell to use the linked commands.
`openjdk` is keg-only. Point your IDE to
`/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home` if it needs
a JDK path.

## Inventory

| Legacy item | mise setup |
| --- | --- |
| `cmake`, `cue`, `glab`, `glow`, `gopls`, `helm`, `herdr`, `krew`, `kustomize`, `llmfit`, `minikube`, `mole`, `ollama`, `openjdk`, `opentofu`, `pdm`, `uv`, `virtctl` | Native formulae with those names. CUE now uses the shared Homebrew prefix. Any CUE installed by the initial Aqua setup can remain in mise's tool cache. |
| `golang`, `kubectl`, `nvim` | Native formulae `go`, `kubernetes-cli`, `neovim`. |
| `flux-build` | The `doodlescheduling/flux-build` tap now publishes a binary cask. Install `doodlescheduling/flux-build/flux-build` with the native cask manager. An older keg can remain installed. If its CLI link conflicts, inspect the existing link and decide which installation should own it before rerunning. |
| `fluxcd/tap/flux`, `hashicorp/tap/terraform`, `hashicorp/tap/terraform-ls` | Native tap formulae. These three use the vendors' Apple Silicon release archives through the tap definitions. |
| `ansible`, `ansible-lint` | Retire as mise bootstrap dependencies. Keep existing installations for the legacy setup and development workflow. |
| `nvm` | Node LTS moves to mise through the terminal setup work. A previous `nvm` installation and its versions can stay installed. |
| `docker`, `docker-desktop` | Both names refer to Docker Desktop. Setup declares the canonical `docker-desktop` cask once. Finish first-launch setup in Docker Desktop. |
| `stablyai/orca/orca` | Native tap cask with the Apple Silicon DMG and bundled CLI. |
| `anydesk`, `balenaetcher`, `bruno`, `chatgpt`, `codex`, `cursor`, `dbeaver-community`, `firefox`, `freelens`, `ghostty`, `herdr-app`, `hiddenbar`, `home-assistant`, `monitorcontrol`, `musescore`, `obs`, `obsidian`, `openlogi`, `shottr`, `transmission`, `visual-studio-code`, `voov-meeting` | Native casks. The Codex cask installs the CLI. |

The four legacy taps are recorded in `[bootstrap.brew.taps]`. The
`stablyai/orca` tap is also recorded for Orca. These URLs tell mise where to
read definitions and metadata. If GitHub rate-limits tap lookups, configure
mise's GitHub authentication and rerun setup. [GitHub authentication](https://mise.jdx.dev/dev-tools/github-tokens.html)

## Manual installs

Keep an existing working copy under its current owner. For a missing item,
use the corresponding procedure below.

| Item | Reason and procedure |
| --- | --- |
| `docker/tap/sbx` | mise 2026.11.11 cannot evaluate the tap's `uninstall_preflight_steps`. On a Mac with Homebrew, run `brew install --cask docker/tap/sbx` and verify with `sbx --version`. Homebrew manages the CLI, completions, and daemon cleanup. [Docker tap definition](https://github.com/docker/homebrew-tap/blob/HEAD/Casks/sbx.rb) |
| `google-drive` | The privileged pkg can install over a vendor-managed copy without a Homebrew cask record. If Drive is absent, use Google's macOS installer or `brew install --cask google-drive`. [Cask metadata](https://formulae.brew.sh/cask/google-drive) |
| `omnissa-horizon-client` | The privileged pkg installs system helpers and can replace an unmanaged copy. If Horizon Client is absent, use the macOS installer supplied by your organization or `brew install --cask omnissa-horizon-client`. [Cask metadata](https://formulae.brew.sh/cask/omnissa-horizon-client) |
| `zoom` | The privileged pkg can replace an unmanaged copy and launch the app. If Zoom is absent, use its Apple Silicon macOS installer or `brew install --cask zoom`. [Cask metadata](https://formulae.brew.sh/cask/zoom) |
| `ollama-app` | Its cask also links `bin/ollama`, which belongs to the `ollama` formula used for the local-model service. If you need the GUI, copy the vendor's Ollama.app to `/Applications`. Decline any CLI-link prompt and coordinate GUI startup with the local Ollama service. [Ollama download](https://ollama.com/download/mac) |

If a supported cask reports an artifact or link conflict on your machine,
check the existing installation before retrying. For a cask that requires the
vendor installer or Homebrew on your machine, keep that copy under its owner.
Homebrew installs can satisfy the native cask declaration through their cask
receipts. If a vendor-managed copy cannot be adopted, omit its declaration
from your local checkout before retrying.

## Existing installs and removals

Mise recognizes formulae in the existing `/opt/homebrew` Cellar. For a
third-party formula, a same-named existing keg may satisfy apply even when it
came from a different tap. Check its receipt before migrating it manually.
Mise preserves Homebrew-owned casks and leaves their upgrades to Homebrew.
Mise records its own casks separately. Keep each cask with its existing
manager during maintenance.

Mise checks Docker Desktop ownership under the canonical `docker-desktop`
token. If setup detects a legacy `Caskroom/docker` record, it pauses before
applying packages. For a Homebrew-owned cask, preview the rename with
`brew migrate --dry-run --cask docker`, then run
`brew migrate --cask docker` and retry setup. If the record is stale or belongs
to another installer, resolve it with its owner first.

For app bundles without a cask record, mise can adopt a matching bundle in
place or keep an existing self-updating app in place while recording it as
adopted. A different bundle that cannot be adopted causes an error and stays
in place. This preserves the existing app and its privacy permissions during
setup. An explicit upgrade can still replace the app and require new grants.
[Formula ownership](https://mise.jdx.dev/bootstrap/packages/brew.html#coexistence-with-a-real-homebrew)
[Cask ownership and adoption](https://mise.jdx.dev/bootstrap/packages/brew-cask.html#adopt-an-existing-app)

Setup applies the configured packages without pruning. The legacy cask
removal list is manual. Review `1password`, `claude-code`, `google-chrome`,
`iterm2`, `logitune`, `t3-code`, and `utm` individually. To remove a
Homebrew-owned item, confirm it with `brew list --cask` and run
`brew uninstall --cask <token>` for that item. Use the vendor's uninstall
procedure for a vendor-managed copy. Keep app data unless you separately
choose to delete it.

To adjust package choices, use the `[bootstrap.packages]` and
`[bootstrap.brew.taps]` tables in the reviewed mise config. Additions and
changes to keys can be made in `mise.local.toml`. Add that file to your local
Git excludes before saving private choices. To omit a
checked-in package, remove its key from your local checkout's `mise.toml`.
The Ansible variables `homebrew_installed_packages`, `homebrew_taps`,
`homebrew_cask_apps`, `homebrew_cask_appdir`, and
`homebrew_cask_uninstalled_apps` remain inputs to the legacy workflow.
