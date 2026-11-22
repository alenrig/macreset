# macreset

A project for fast Mac system reinstallation without TimeCapsule, but with most important things.

## mise bootstrap

The mise setup restores command-line tools and desktop apps and verifies CUE.
Use a native Apple Silicon macOS terminal with internet access and a writable
`~/.local/bin`. Install Apple's Command Line Tools (`xcode-select --install`)
for Git and tap formula setup. The installer uses macOS command-line
utilities and the [official mise installer](https://mise.jdx.dev/installing-mise.html).
The minimum tested mise release is `2026.11.11`.

Review [`mise.toml`](mise.toml), then run this command from the repository root:

```sh
./bootstrap
```

Bootstrap looks for mise in `~/.local/bin` and on `PATH`, and installs it if
absent. Approve mise's trust prompt to continue. Setup uses mise to install
packages into the standard Homebrew prefix and apps into `/Applications`.
Keep a terminal open for any macOS administrator prompt. Rerun `./bootstrap`
after resolving an error. See [package setup](docs/mise-packages.md) for the
manual installs, legacy removals, and package ownership.

The existing Ansible setup remains available through `./macreset.sh`.

## Herdr sandboxes

A normal `ansible-playbook main.yml` run configures **new** Herdr Docker
Sandboxes to launch Codex with `gpt-5.6-sol`, low reasoning, and YOLO permissions
(`--dangerously-bypass-approvals-and-sandbox`). The working repository is
bind-mounted read-write at the same path inside the sandbox, not copied or
cloned: agent edits immediately change the host checkout.

The launcher automatically trusts only the current repository root (or current
working directory outside Git) for that Codex invocation. It does not change
host Codex trust settings. Existing sandboxes and credentials remain in place.

Override `herdr_sbx_agent_kind`, `herdr_sbx_codex_model`, or
`herdr_sbx_codex_reasoning_effort` in `config.yml` to change these defaults.
The playbook still installs host Pi and Ollama and pulls `qwen3-coder:30b`.
Pi defaults to `openai/gpt-6.1-terra` with medium thinking on the host and low
thinking in new Pi sandboxes. Override `pi_default_provider`, `pi_default_model`,
`pi_default_thinking_level` (host), or `herdr_sbx_pi_thinking_level` (sandbox)
in `config.yml` if needed. Host Pi also loads the Ponytail package; override
`pi_packages` to change the managed package list. Pi installs missing packages
on startup. Authenticate with
OpenAI through Pi's `/login`; credentials are not managed by Ansible.
Set `herdr_sbx_agent_kind: pi` to opt into the Pi sandbox adapter.

For Codex sandboxes, the Herdr role now ensures a global sbx OpenAI credential
exists before writing the launcher configuration. Existing sbx OAuth or API-key
credentials are preserved. On first setup, it opens the host browser for OpenAI
OAuth; complete the login within five minutes. New sandboxes created through
Herdr then use sbx's host-managed authentication without an in-sandbox login.
No host Codex or Pi auth files are copied or mounted.

For headless setup, first run `sbx secret set openai --oauth` interactively on
the host, or provision an API key with `sbx secret set openai`. Set
`herdr_sbx_codex_authenticate: false` in `config.yml` to manage authentication
yourself (for example, with a non-OpenAI provider). Check mode inspects credential
presence but never starts login. The Pi adapter does not run this Codex setup.
See the [authentication research](docs/sandbox-auth-research.md) for sources,
alternatives, and credential-isolation tradeoffs.

Read the [local Pi checklist](docs/local-llm-rollout.md) before opting in.
The [maintenance guide](docs/local-llm-maintenance.md) covers local model
changes and recovery.
