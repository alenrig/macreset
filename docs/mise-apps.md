# Applications and Dock through mise

Run `./bootstrap.sh apps` to restore applications, or `./bootstrap.sh dock` to
restore applications then selectively edit the login user's Dock. Both tasks
run prerequisites, tools, packages and native resources first. The complete `setup`
task waits for apps and Dock in the same invocation.
Run in your logged-in graphical macOS session, without running mise as root.

The single mise inventory is `[bootstrap.packages]`: all 29 legacy cask tokens are accounted for by 28 declarations
and all 17 App Store IDs are retained. Homebrew renamed `docker` to
`docker-desktop`; those two original tokens represent one app, declared once
under the canonical name. `docker/tap/sbx` remains separately declared. The Docker tap URL remains in `[bootstrap.brew.taps]`.
Upstream renames, alias collisions or unavailable applications stop setup;
review those changes rather than using force or silently dropping a choice.
Ansible is retired. Private YAML is preserved as a reference behind the
bootstrap migration guard.

`packages` installs `mas` and `dockutil` before apps/Dock. Sign in to the App
Store with the Apple Account that owns the configured apps, and ensure their
folders are indexed by Spotlight. Setup cannot purchase apps or provision the
account. `mas` may request administrator or Apple Account authentication.
There is no reliable modern `mas account` preflight: inventory must succeed,
then installation/upgrade errors propagate with a prerequisite reminder.
Xcode installation does not accept its license or finish first launch.

## Native ownership and fallbacks

On standard Apple Silicon Homebrew, each cask uses native mise apply. Existing
Homebrew-owned casks remain owned by Homebrew and are not forcibly reinstalled
or adopted. Native apply repairs incomplete mise installs; status must report
installed afterward. Adoption is enabled for previously unmanaged bundles, so
mise only adopts identical builds (or supported self-updating apps); an adoption
conflict stops setup and preserves the app. Application upgrades can reset macOS
privacy permissions, which may require granting them again.

Mise uses `/opt/homebrew/Caskroom` even on Intel. Intel/custom-prefix casks use
`brew install --cask --adopt` instead, so existing Homebrew ownership is visible.
A native `unsupported artifact type`, unsupported-feature, or unsupported-formula
error also permits that CLI fallback. Other failures remain failures, including
network, authentication, checksum and ownership errors. An unknown native error
wording stops setup; inspect it before choosing a fallback. A partially applied
native cask may require manual receipt repair before Homebrew can take ownership.

The application destination is `/Applications`, shared by native and CLI paths
through `MISE_BREW_CASK_OPT_APPDIR`. It affects new installs; existing apps are not
moved. Use this common setting, rather than native per-cask `appdir` overrides,
when CLI fallbacks are needed. Cask-internal destinations (such as binaries or
installer-package paths) remain those chosen by upstream. Keep existing native
and Homebrew-owned inventories separate during maintenance: native upgrades
skip Homebrew-owned casks; `brew upgrade --cask` skips mise-owned receipts.
Do not enable `homebrew_metadata` ownership transfer without reviewing its
Homebrew version, third-party tap and application-directory restrictions.

Mise installs App Store IDs natively. Explicit CLI removals preserve the seven
unwanted Homebrew casks and GarageBand/iMovie IDs, with installed-state checks
before and after, followed by `mas upgrade` for **all** installed App Store apps.
Only that explicit removal list is acted on; no broad prune occurs. The removal
list migrates the Homebrew-owned legacy selection; if an unwanted app has instead
been installed independently through mise, remove that managed resource using
mise after reviewing its receipt, rather than erasing it with Homebrew.

Native Dock replacement would discard unrelated tiles, so `dockutil` applies the
21 selective removals and 13 ordered persistent apps. It checks every application
before editing, resolves old `/Applications` system-app locations to
`/System/Applications` where needed, replaces matching managed tiles, and verifies
positions and removals. Unrelated tiles remain after the managed positions. The
Dock restarts once after changes. Missing applications stop the Dock phase.

## Overrides and recovery

Use ignored `mise.local.toml`, which takes precedence over `mise.toml`; review
`mise config ls` for other contributing configuration. Native package maps merge
by key. Only present/latest requests are supported by this runner: remove a
package declaration in your checkout to stop managing it (that does not uninstall
it). Do not substitute absent requests or broad prune. `[env]` values replace the
corresponding complete value:

| Legacy setting | Replacement |
| --- | --- |
| `homebrew_cask_apps`, `mas_installed_apps` | Native `brew-cask:` / `mas:` package keys |
| `homebrew_cask_appdir` | `MISE_BREW_CASK_OPT_APPDIR` |
| `homebrew_cask_uninstalled_apps` | `MACRESET_CASK_REMOVE`, space-separated cask tokens |
| `mas_uninstalled_apps` | `MACRESET_MAS_REMOVE`, space-separated numeric IDs |
| `mas_upgrade_all_apps` | `MACRESET_MAS_UPGRADE_ALL`, `"true"` or `"false"` |
| `dockitems_remove` | `MACRESET_DOCK_REMOVE`, JSON array of names |
| `dockitems_persist` | `MACRESET_DOCK_ITEMS`, JSON array of `{name,path,pos}` objects |

For example:

```toml
[env]
MISE_BREW_CASK_OPT_APPDIR = "~/Applications"
MACRESET_MAS_UPGRADE_ALL = "false"
MACRESET_DOCK_ITEMS = '''[{"name":"Ghostty","path":"/Applications/Ghostty.app","pos":1}]'''
```

Update Dock paths yourself when changing the destination. Translate existing
`config.yml` choices before acknowledging `MACRESET_CONFIG_MIGRATED=1` as described
in [bootstrap configuration](mise-bootstrap.md); YAML is never deleted or silently
read as though it were TOML. Failed runs retain successful earlier changes. Fix
authentication, network, missing apps or conflicting ownership, then rerun the
same task; installed state is queried again. No tests, setup run or real-Mac
fresh-machine/rerun validation were performed for this migration. Intel, current
cask compatibility, App Store purchases and Dock behavior remain unverified.

Sources: [native casks and ownership](https://mise.jdx.dev/bootstrap/packages/brew-cask.html),
[native App Store prerequisites](https://mise.jdx.dev/bootstrap/packages/mas.html),
[mas commands and account requirements](https://github.com/mas-cli/mas),
[dockutil selective editing](https://github.com/kcrawford/dockutil).
