# Local model maintenance

The normal `ansible-playbook main.yml --ask-become-pass` run installs missing
components, starts a stopped Ollama service, checks the selected local model
tag and full manifest digest, and reports versions and actions. An unchanged
run does not contact the model registry, pull the model, update Pi or Ollama,
or restart a healthy Ollama service.

The default model is `qwen3.5:9b-q4_K_M` at 32,768 tokens. To select the 4B
alternative, set **both** `local_llm_model: qwen3.5:4b-q4_K_M` and its
independently verified, full 64-character `local_llm_expected_digest` in
`config.yml`. The role fails if the 4B tag still has the default 9B digest.
It never picks a fallback model or deletes previously downloaded tags.

Use a per-run extra variable when maintenance is intended:

```sh
ansible-playbook main.yml --ask-become-pass -e local_llm_upgrade=true
ansible-playbook main.yml --ask-become-pass -e local_llm_refresh_model=true
```

The first command asks `pi update` and Homebrew to update installed software;
the second pulls the selected tag even if it exists locally. Both default to
false and are not saved in the normal configuration. After a pull or an
upgrade request, the playbook makes a small inference request. Ollama
restarts only when its formula version or managed LaunchAgent settings change.

If installation, service startup, an upgrade, model pull, digest verification,
or inference fails, read the reported component and observed state, repair the
cause, and rerun the playbook. Keep the same `-e` flag when retrying an
explicit upgrade or refresh. An interrupted initial pull is retried when the
tag is absent. A failed refresh may leave the selected tag absent or changed;
inspect `curl -fsS http://127.0.0.1:11434/api/tags` and compare the full
`digest` field before retrying. A tag with
the wrong digest fails until you restore the expected model or independently
verify and explicitly change the pinned digest. The playbook never accepts a
new digest automatically.

The Ollama LaunchAgent is `com.macreset.ollama`; its log is
`~/Library/Logs/macreset-ollama.log`. The run checks that its own process is
the only listener on `127.0.0.1:11434`. If that check fails, stop any
competing Ollama app or Homebrew service and rerun. Do not expose port 11434
on a LAN interface.
