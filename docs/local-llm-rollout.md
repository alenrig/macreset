# Local Pi rollout and rollback

The playbook installs Ollama and Pi on the Mac, downloads
`qwen3.5:9b-q4_K_M` with a 64K context window as an optional local model.
Pi defaults to `openai/gpt-6.1-sol` with medium thinking on the host and low
thinking in sandboxes. For the local-model
checks below, set these overrides in `config.yml`:

```yaml
pi_default_provider: ollama
pi_default_model: qwen3.5:9b-q4_K_M
pi_default_thinking_level: medium
```

Override `local_llm_model` and `local_llm_context_length` separately to change
the downloaded Ollama model and its context window. Without these Pi overrides,
use Pi's `/login` for OpenAI in each environment instead of the local checks.
Herdr defaults to Codex with GPT-6.1-Sol, low reasoning, YOLO permissions, and
a read-write workspace mount. To opt into local Pi for new sandboxes, set
`herdr_sbx_agent_kind: pi` in `config.yml` before running the playbook.
Pi sandboxes use the Mac's Ollama service; they do not download a second copy
of Qwen.

## Check a new setup

1. Start Docker Desktop and sign in to Docker and `sbx` if prompted. Run
   `ansible-playbook main.yml`.
2. Run `pi --print 'Reply with one word: ready'` on the Mac. Check that
   `~/.pi/agent/models.json` points to `127.0.0.1:11434` and
   `~/.pi/agent/settings.json` selects Qwen. The playbook keeps backups when
   replacing these files.
3. Start a **new** Pi sandbox from Herdr. Its first start installs Pi and
   copies the sandbox model settings and `~/.agents/skills` into the sandbox.
   Ask Pi for a response. Use the plugin's `open-shell` action to check
   `/home/agent/.pi/agent/models.json` and
   `/home/agent/.agents/skills` if needed. The sandbox endpoint is
   `http://host.docker.internal:11434/v1`.
4. Run the playbook again. It should leave Ollama, the downloaded model,
   and Pi configuration unchanged. Existing sandboxes keep their installed
   Pi, settings, and skills; create a new one to pick up changes.

Ollama is bound to the Mac's loopback interface. The playbook adds the
`localhost:11434` network rule to the local `sbx` policy so sandboxes can
reach the host service. Check access with
`sbx policy check network localhost:11434`.

## Restore the Codex default

Remove `herdr_sbx_agent_kind: pi` from `config.yml` (or set it to `codex`),
then run `ansible-playbook main.yml` again. New sandboxes use Codex with the
managed model and reasoning defaults. Existing sandboxes are not changed.
Older `config.codex-rollback.json` files are left untouched, but are no longer
created or required by the playbook.
