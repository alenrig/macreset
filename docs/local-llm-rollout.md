# Local Pi rollout and rollback

`./bootstrap.sh local-llm` installs/configures host Ollama and Pi. By default,
Ollama provides optional `qwen3-coder:30b` with a 65536-token context, while Pi
starts with `openai/gpt-6.1-terra`, medium thinking and the Ponytail package.
Use Pi's `/login` for OpenAI authentication; setup never manages credentials.

To select local inference, add these overrides to ignored `mise.local.toml`:

```toml
[vars]
pi_default_provider = "ollama"
pi_default_model = "qwen3-coder:30b"
pi_default_thinking_level = "medium"
```

Run `./bootstrap.sh local-llm` again. Its dependency chain also applies other
configured native machine resources; it is not a service-only command. After
setup, optional manual checks are `pi --print 'Reply with one word: ready'`,
`launchctl print gui/$(id -u)/com.macreset.ollama`, and reviewing
`~/Library/Logs/macreset-ollama.log`. The host model endpoint in
`~/.pi/agent/models.json` is `http://127.0.0.1:11434/v1`.

To restore the default provider, remove those overrides (or select your desired
provider/model), then rerun the task. Replaced Pi JSON files have restrictive
backup files beside them. To restore an older file manually, first stop Pi,
review the selected backup, copy it over its matching JSON file and retain mode
0600. Reapplying setup restores the configured choices. Failed Ollama settings
replacement restores the previous plist and previously loaded service; inspect
logs and fix the cause before rerunning.

Setup configures only the host. There is no implemented sandbox creation,
Herdr adapter editing, network-policy provisioning or OAuth automation here.
Existing sandboxes and credentials are unchanged. See
[maintenance](local-llm-maintenance.md) for service ownership, overrides,
permissions and compatibility limits. No tests or machine acceptance run were
requested or performed for this migration.
