# macreset

A project for fast Mac system reinstallation without TimeCapsule, but with most important things.

## Local Pi in Herdr sandboxes

A normal `ansible-playbook main.yml --ask-become-pass` run installs host Pi and
Ollama, pulls the pinned Qwen3.5 model, and configures Herdr to start Pi in
**new** Docker Sandboxes. Pi inside a sandbox uses the Mac's model through
`host.docker.internal:11434`; it does not download another model. Ollama is
bound to the Mac's loopback interface. Existing Codex sandboxes and their
credentials remain in place. Ansible provisions the sandbox Pi image before
Herdr selects it; the sandbox adapter does not run a setup script.

Read the [rollout and rollback checklist](docs/local-llm-rollout.md) before
switching the Herdr default. The [maintenance guide](docs/local-llm-maintenance.md)
covers the pinned digest, deliberate updates, model refreshes, and recovery.
