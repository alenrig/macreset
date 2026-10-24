# Local Pi rollout and rollback

The playbook selects `qwen3.5:9b-q4_K_M` with a pinned full Ollama manifest
digest and a 32,768-token context by default. `config.yml` can select a
different model only with a matching, independently verified expected digest.
The explicit smaller option is `qwen3.5:4b-q4_K_M`; the playbook never switches
to it on its own. See [maintenance](local-llm-maintenance.md) for per-run
upgrade and model refresh commands and failure recovery.

Run these checks on the target Mac during rollout. They are manual acceptance
checks, not claims that a live sandbox has been tested in CI. Keep an existing
Codex sandbox for the preservation check and note the current `sbx policy`
preset before the first playbook run.

## First run and unchanged rerun

1. Start Docker Desktop, sign in to Docker and `sbx` if prompted, and inspect
   the existing policy with `sbx policy ls --wide --type network`. Record its
   preset and existing rules. If there is no local preset, the playbook
   initializes `balanced`; an existing preset must remain unchanged.
2. Run `ansible-playbook main.yml --ask-become-pass`. Confirm it reports host
   Pi and Ollama versions, the selected model tag, observed full digest, and
   whether installation, download, or service start occurred. On first setup,
   expect one model pull, a small inference check, and an Ansible-provisioned
   Pi sandbox image loaded into `sbx`. Compare the observed
   digest with `local_llm_expected_digest` in `default.config.yml` or the
   explicit value in `config.yml`.
3. Run the same playbook command again. Confirm there is no repeated model
   pull, Pi or Ollama upgrade, sandbox image rebuild, or healthy-service
   restart. The service, selected tag, and full digest are still checked.
4. Check `sbx policy check network localhost:11434` and inspect the preset
   again. The allow rule is global so dynamically named Herdr sandboxes can
   reach the host model. Existing policy choices should still be present.

## Host and sandbox behavior

1. Run `pi --print --provider ollama --model qwen3.5:9b-q4_K_M 'Reply with one word: ready'`
   on the host, substituting the configured model tag if needed. Confirm a
   Qwen response. Inspect `~/.pi/agent/models.json` and `settings.json` if Pi
   cannot select it; other Pi providers and preferences should remain intact.
2. Run `lsof -nP -iTCP:11434 -sTCP:LISTEN` on the Mac. Confirm only
   `127.0.0.1:11434` is listening, and test from another LAN machine that
   the Mac's LAN address on port 11434 is unreachable. The sandbox's Docker
   host gateway can still reach the loopback service.
3. Use Herdr's sbx plugin to start a **new** agent. Its plugin `info` action
   should identify the Pi adapter and `shell` workload. The plugin's
   `config.json` should name the managed `macreset-pi` template and contain
   no setup script. Ask Pi for a simple
   response, then disconnect and use the plugin `reconnect` action. Confirm
   Herdr reconnects to the same sandbox and Pi can answer through host
   Ollama. If startup fails, use the plugin `open-shell` action to inspect
   `~/.pi/agent/models.json`, run `pi --version`, and query
   `http://host.docker.internal:11434/api/tags`.
4. Temporarily stop host Ollama and ask the new Pi sandbox for a response.
   Confirm the connection failure is visible in Pi/Herdr, with no switch to
   Codex or another model. Restart the service or rerun the playbook. A
   missing or mismatched selected model must also fail visibly.
5. Open the pre-existing Codex sandbox and confirm it remains usable with its
   existing settings and credentials. The default change does not migrate or
   delete it.

## Adapter changes and rollback

The playbook builds the Pi template through Ansible and loads it into Docker
Sandboxes before switching the Herdr default. New sandboxes use that image,
so their Pi version is the one packaged when the image was built. The host
and sandbox Pi versions may differ. After changing the managed adapter,
model, context, or sandbox policy, run the playbook, create a new Pi sandbox,
and repeat the relevant checks above. Existing sandboxes are not updated in
place. To refresh Pi in the sandbox image, remove the old managed image from
Docker and `sbx template`, then rerun the playbook before creating new
sandboxes. A host Pi version change also selects a new managed image tag.

Before the playbook first switches the default, it saves the current
Codex-selecting sbx plugin configuration at
`~/.config/herdr/plugins/config/sbx.sandbox/config.codex-rollback.json`.
The playbook leaves this copy untouched on later runs. To restore the old
default, copy that saved file over the managed config and then create a
**new** Codex sandbox:

```sh
cp ~/.config/herdr/plugins/config/sbx.sandbox/config.codex-rollback.json \
   ~/.config/herdr/plugins/config/sbx.sandbox/config.json
```

Confirm the restored `config.json` selects `"agentKind": "codex"`, then use
Herdr to start and reconnect to a new Codex sandbox. Existing Codex
sandboxes are unchanged. A later macreset playbook run sets the managed
default back to Pi; repeat the copy after that run if you are keeping the
manual rollback in effect. Do not remove existing sandbox credentials or
delete model tags as part of rollback.
