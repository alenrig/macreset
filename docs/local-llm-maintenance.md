# Local model maintenance

## mise setup

After trusting the repository and restoring its packages, run
`mise run local-llm` from a GUI login session. This task uses the Ollama
formula declared in `mise.toml` and the mise-selected Node LTS. It keeps
the legacy `com.macreset.ollama` LaunchAgent label, listens at
`127.0.0.1:11434` and writes to `~/Library/Logs/macreset-ollama.log`.
The task verifies the listener belongs to that job before checking the
model inventory. A healthy job with matching settings stays running and
Ollama downloads the configured model only when its tag is missing.

If setup reports a competing listener or service, use the reported process
or job label to identify its owner and stop it through its own service
manager, then retry. For an unrecognized `com.macreset.ollama` plist or job,
inspect it before moving the file or unloading the job. If readiness fails,
check the Ollama log. To inspect a healthy installation locally, use
`launchctl print "gui/$(id -u)/com.macreset.ollama"`,
`lsof -nP -iTCP:11434 -sTCP:LISTEN`, and
`curl --noproxy '*' http://127.0.0.1:11434/api/tags`.

Copy any overrides you want to carry over from Ansible's `config.yml` into
the `[vars]` table of your ignored `mise.local.toml`. The defaults are:

```toml
[vars]
local_llm_model = "qwen3-coder:30b"
local_llm_context_length = "65536"
pi_default_provider = "openai"
pi_default_model = "gpt-6.2-sol"
pi_default_thinking_level = "medium"
pi_packages = '["git:github.com/DietrichGebert/ponytail"]'
```

Encode `pi_packages` as a JSON array of package source strings. Use `[]`
for an empty list. To start Pi with the local model, set `pi_default_provider`
to `ollama` and `pi_default_model` to the same value as `local_llm_model`.
Pi connects to `http://127.0.0.1:11434/v1`. For OpenAI and other providers
that need credentials, open Pi and use `/login` interactively.

The task preserves executable Pi installations at `~/.pi/agent/bin/pi`,
`~/.local/bin/pi`, and `/opt/homebrew/bin/pi`. If Pi is missing, the task
installs `@earendil-works/pi-coding-agent` into `~/.local` with npm's
`--ignore-scripts`. Ensure `~/.local/bin` is on your PATH when using that
installation. Pi installs missing configured packages when it starts.
The task preserves unrelated settings and providers and writes `0600`
backups alongside modified `settings.json` and `models.json`. Resolve
malformed files or path conflicts before rerunning the task.

## Ansible setup

The normal playbook run installs missing Ollama and Pi packages, starts the
Ollama LaunchAgent, and pulls the selected model only if its tag is absent.
It writes the host and sandbox Pi model settings and updates Herdr's default
adapter. Run `ansible-playbook main.yml` again after changing
`local_llm_model` or `local_llm_context_length` in `config.yml`. These select
the optional Ollama model, not Pi's startup model. Pi defaults to
`openai/gpt-6.1-terra` with medium thinking on the host and low in sandboxes;
override `pi_default_provider`, `pi_default_model`, `pi_default_thinking_level`
(host), and `herdr_sbx_pi_thinking_level` (sandbox) to change its defaults.
The host package list is managed by `pi_packages` and defaults to Ponytail; Pi
installs missing packages on startup.

The Ollama LaunchAgent is `com.macreset.ollama`; its log is
`~/Library/Logs/macreset-ollama.log`. When selected with
`pi_default_provider: ollama`, Pi uses
`http://127.0.0.1:11434/v1` on the Mac and
`http://host.docker.internal:11434/v1` in new sandboxes. Existing sandboxes
keep their first-start copies of Pi, model settings, and skills.

To refresh an already downloaded model or upgrade Pi, use the corresponding
`ollama pull`, `pi update`, or Homebrew command explicitly, then rerun the
playbook. The playbook does not update installed packages or redownload a
present model on an ordinary run.
