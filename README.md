# macreset

A project for fast Mac system reinstallation without TimeCapsule, but with most important things.

## Codex in Docker Sandboxes

The Herdr `sbx.sandbox` plugin is configured to launch Codex in every new sandbox. After installing `sbx` and signing in with `sbx login`, authenticate on the host with the OpenAI account that has your Codex subscription:

```sh
sbx secret set openai --oauth
```

The OAuth flow opens a browser and stores credentials in the host keychain, so it must be completed interactively. An OpenAI API key takes precedence over OAuth when both are present. If you previously stored an OpenAI API key, run `sbx secret rm openai` before the OAuth command. Remove any sandbox-scoped OpenAI API keys with `sbx secret rm openai --sandbox <name>` as well, and avoid `sbx secret import openai`. The managed plugin config is restored on each Ansible run.
