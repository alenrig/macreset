# Dotfiles and terminal migration

The mise `native` task now depends on `terminal`, which follows packages and
runs the guarded Oh My Zsh installer before native repositories and dotfiles.
`./bootstrap.sh native` applies this slice and its prerequisites; the complete setup task includes this phase. Do not run machine setup just
to validate a checkout. Ansible has been retired; reusable Ghostty and bin sources live in `assets/`.

`[bootstrap.repos]` in `mise.toml` owns the private dotfiles checkout (main),
Vundle and all eleven Vim plugins (master), both Zsh plugins and Dracula Zsh
(master), and Dracula Ghostty (main). Destinations preserve the former YAML defaults.
SSH access to `git@github.com` and verified GitHub host trust must already work;
setup does not provision credentials or automatically accept a host key.
Native apply rejects dirty/untracked worktrees, wrong origins and nonempty
non-repository destinations. Commit, stash or move your own changes deliberately
before retrying; do not force, reset or skip dirty repositories to finish setup.
Branches fast-forward on apply. Network/auth failures remain failures.

The five explicit home links are `.gitconfig`, `.gitignore`, `.vimrc`, `.zshrc`
and `.zprofile`. Ghostty config is copied as 0644, and both bin utilities as
0755. Native dotfile conflict handling remains enabled; no force flag is used.
Existing real files at symlink destinations cause a conflict even when their
contents match; back them up or adopt their content yourself before retrying.
Mise does not automatically back up those untracked files. Review conflicting existing files and mise's proposed changes rather than
removing your own files. Copy mode intentionally manages the Ghostty config;
move private customizations into its source or an override before applying.
The utility scripts delegate to the setup and explicit maintenance mise tasks,
using exec so failures propagate.

Oh My Zsh needs its upstream installer, including its checkout and permissions,
rather than a bare clone. The task downloads it to a unique temporary directory,
checks download/install failures and removes that directory on exit. Its generated
startup template goes into this temporary ZDOTDIR so a fresh install does not
create a real `.zshrc` that would block the private symlink. It preserves the
user’s existing startup files, does not launch a new shell, and deliberately leaves login-shell
selection to the user (`chsh -s /bin/zsh` if desired). A partial existing install
fails with a repair message instead of being overwritten. The two configured
example themes are absent-managed; before a new Dracula clone the task removes
only those installer samples. Other custom theme files block cloning safely.
Existing theme repositories are never cleaned before native dirty inspection.

Native shell activation normally edits `.zshrc`, which would dirty the private
checkout through its symlink and prevent the next repository update. Instead,
managed line entries in `.zshenv` add `~/.local/bin` and activate mise only for
interactive zsh. No private checkout file is edited. Review an existing linked
`.zshenv` yourself before applying. If mise was installed elsewhere, put that
executable on PATH in your private configuration. Open a new terminal afterward.
Remove private nvm sourcing and competing Node/PATH setup yourself; later
`.zprofile`/`.zshrc` hooks can shadow mise. Do not enable native zsh activation
alongside these links. Private dotfiles must not source mise a second time.

## Overrides and recovery

Use ignored `mise.local.toml`, loaded after the project configuration. Native
maps merge by destination. For a different private URL/ref at the same path:

```toml
[bootstrap.repos]
"~/Developer/dotfiles" = { url = "ssh://git@github.com/me/dotfiles.git", ref = "main" }
```

For a different destination, remove/change the original declaration in your
checkout and update all five `[dotfiles]` sources together; adding a new key alone
retains the default checkout. Map `dotfiles_repo`, `dotfiles_repo_version` and
`dotfiles_repo_local_destination` to that repository entry; map `dotfiles_home`
and `dotfiles_files` to explicit dotfile destinations/sources. Map `vim_plugins`
and `zsh_plugins` to repository entries, preserving each intended ref. Native SSH
host verification replaces `dotfiles_repo_accept_hostkey`; manage known_hosts
outside setup. For a custom Oh My Zsh location override the terminal task and
all dependent destinations together. Existing `config.yml` must be explicitly
reviewed as described in [mise-bootstrap.md](mise-bootstrap.md).

Failures leave earlier successful changes in place. Repair the reported state
and rerun `./bootstrap.sh native`. No tests, acceptance runs, private-repository
access, installer execution, or macOS parity verification were performed for
this migration. Native resource behavior is based on the documented mise
2026.11.8 interface; full fresh-machine and repeat-run parity remains unverified.

Sources: [native repositories](https://mise.jdx.dev/bootstrap/repos.html),
[managed files](https://mise.jdx.dev/dotfiles/managed.html),
[Oh My Zsh installer options](https://github.com/ohmyzsh/ohmyzsh/blob/master/tools/install.sh).
