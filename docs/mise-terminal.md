# Terminal and editor setup

On the Mac, register an SSH key with a GitHub account that can read
`alenrig/dotfiles`. Run `ssh -T git@github.com` and verify a first-use host
fingerprint against [GitHub's published fingerprints](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints)
before accepting it. GitHub prints your username on successful authentication.
Confirm repository access with:

```sh
git ls-remote ssh://git@github.com/alenrig/dotfiles.git refs/heads/main
```

From the macreset checkout, run `./bootstrap`. It restores the private
checkout at `~/Developer/dotfiles`, its home dotfiles, Oh My Zsh and its
plugins and theme, Vundle and the Vim plugins, and the Ghostty config and
Dracula theme in `~/.config/ghostty`. Ghostty itself is installed by the
workstation package step. If Ghostty already has settings under
`~/Library/Application Support/com.mitchellh.ghostty`, those settings can override
the restored values. [Ghostty configuration locations](https://ghostty.org/docs/config#file-location)

If setup stops, inspect the reported path. For a checkout, use
`git -C PATH status --short` and `git -C PATH remote -v`. Save any changes
you want to keep or move the conflicting checkout aside. For a file conflict,
compare the two files and move the conflicting home file to a backup path
before retrying. A legacy `~/.zshrc` needs this step because setup installs a
small loader that sources the private `.zshrc` and activates mise afterwards.
Carry custom shell changes into the private dotfiles separately. The Dracula
zsh theme is installed under `~/.oh-my-zsh/custom/dracula`. An older theme
checkout under `~/.oh-my-zsh/custom/themes` stays in place.
Rerun `./bootstrap` from the checkout once the prerequisite or conflict is
resolved. To retry just this portion after trusting the configuration, run
`mise run terminal:restore` from the checkout.

## Node in zsh

Setup adds the moving `node@lts` request to the global mise configuration if
you have no global Node request. If you already have one, setup installs its
requested version and reports the request it kept. Project mise declarations
take precedence over the global default. The zsh loader lets the private
configuration initialize nvm before activation and disables Oh My Zsh's nvm
lazy loading and directory autoloading. If your private files define their own
nvm auto-switch hooks, disable those so mise can select Node as you change
projects. To keep using `.nvmrc` for project selection, enable [mise's Node
version file support](https://mise.jdx.dev/lang/node.html#version-files).

From outside the macreset checkout, verify the default in a fresh login shell:

```sh
cd ~
zsh -lic 'command -v node && mise which node && node --version'
```

The two paths should agree. Repeat from a project with a mise Node request to
verify its override. From outside a project, run `mise upgrade node` to
upgrade within the configured request. To switch an existing global pin to the
moving LTS request, run `mise use --global --fuzzy node@lts`.
