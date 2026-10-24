# Local model maintenance

The normal playbook run installs missing Ollama and Pi packages, starts the
Ollama LaunchAgent, and pulls the selected model only if its tag is absent.
It writes the host and sandbox Pi model settings and updates Herdr's default
adapter. Run `ansible-playbook main.yml` again after changing
`local_llm_model` or `local_llm_context_length` in `config.yml`.

The Ollama LaunchAgent is `com.macreset.ollama`; its log is
`~/Library/Logs/macreset-ollama.log`. Pi uses
`http://127.0.0.1:11434/v1` on the Mac and
`http://host.docker.internal:11434/v1` in new sandboxes. Existing sandboxes
keep their first-start copies of Pi, model settings, and skills.

To refresh an already downloaded model or upgrade Pi, use the corresponding
`ollama pull`, `pi update`, or Homebrew command explicitly, then rerun the
playbook. The playbook does not update installed packages or redownload a
present model on an ordinary run.
