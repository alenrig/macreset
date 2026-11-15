# Local model maintenance

Run `./bootstrap.sh local-llm` from the checkout as your desktop login user.
Its dependencies prepare Homebrew, Node, formulae (including Ollama) and native
resources first. The final setup workflow also calls this task. Failures stop
setup; rerun after resolving them. No setup or machine acceptance run was
performed as part of this migration.

The task keeps the existing `com.macreset.ollama` LaunchAgent, bound to
`127.0.0.1:11434`, with run-at-login, keep-alive and
`~/Library/Logs/macreset-ollama.log`. It discovers Homebrew's actual prefix,
validates the model/context, repairs a loaded but stopped job, and waits for
both a running managed job and a valid model inventory (12 attempts, five-second
request timeout, two-second retry delay). It pulls only an absent model tag.
Changed service settings are validated with `plutil`; replacement failures
restore the previous plist and reload a previously loaded job.

Native mise LaunchAgents use a different label (`dev.mise.ollama`). Retaining
the original label is an explicit native-resource gap: a managed plist and
`launchctl` task avoid a second server or removal of the old job before its
replacement works. Loaded Homebrew/mise Ollama jobs or an independently
responding server on port 11434 cause a useful failure; resolve that service's
ownership before retrying. The task does not stop unrelated jobs. launchd needs
an active GUI login session.

Override these values in ignored `mise.local.toml`, which mise loads after
`mise.toml`; all names map directly from the former YAML settings:

```toml
[vars]
local_llm_model = "qwen3-coder:30b"
local_llm_context_length = "65536"
pi_default_provider = "openai"
pi_default_model = "gpt-6.1-terra"
pi_default_thinking_level = "medium"
pi_packages = '["git:github.com/DietrichGebert/ponytail"]'
```

`pi_packages` is a JSON array encoded as a TOML string. JSON serialization
preserves quotes and special characters in model/provider/package values.
Review all former private `config.yml` choices before acknowledging migration
as described in [mise bootstrap](mise-bootstrap.md). The Ollama model/context
and Pi's startup provider/model are independent choices.

Pi is reused if present at `~/.pi/agent/bin/pi`, `~/.local/bin/pi` or
`<actual Homebrew prefix>/bin/pi`. Only when all three are absent does npm
install `@earendil-works/pi-coding-agent` globally into `~/.local`, with
`--ignore-scripts`. Existing Pi installations are not upgraded. Pi's host
`~/.pi/agent` directory is mode 0700; managed `models.json`, `settings.json`
and replacement backups are mode 0600. Changed JSON files are backed up before
atomic replacement. Settings retain the configured provider, model, thinking
level and package list; Pi installs missing packages on startup. Credentials
remain unmanaged: use Pi's `/login` for providers needing authentication.

To refresh an existing model or upgrade Pi, explicitly run `ollama pull` with
`OLLAMA_HOST=127.0.0.1:11434`, `pi update` or the owning package manager, then
rerun setup. JSON backup files remain beside the originals for manual recovery.
No executable sandbox provisioning or OAuth flow exists in this repository;
older documentation describing Herdr sandbox setup overstated the implementation.
Actual service recovery, private overrides and fresh-machine/rerun parity remain
unverified on a Mac. No tests were added or run, per #41.
