# Local Pi rollout and rollback

The playbook installs Ollama and Pi on the Mac, downloads
`qwen3.5:9b-q4_K_M` with a 64K context window, and selects it as Pi's default model. Override
`local_llm_model` and `local_llm_context_length` in `config.yml` if needed.
New Herdr sandboxes install Pi and use the Mac's Ollama service; they do not
download a second copy of Qwen.

## Check a new setup

1. Start Docker Desktop and sign in to Docker and `sbx` if prompted. Run
   `ansible-playbook main.yml --ask-become-pass`.
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

## Restore the previous Herdr default

Before selecting Pi, the playbook saves a Codex-selecting configuration as
`~/.config/herdr/plugins/config/sbx.sandbox/config.codex-rollback.json`.
To use Codex for new sandboxes again:

```sh
cp ~/.config/herdr/plugins/config/sbx.sandbox/config.codex-rollback.json \
   ~/.config/herdr/plugins/config/sbx.sandbox/config.json
```

Existing sandboxes are not changed. A later playbook run selects Pi again.
