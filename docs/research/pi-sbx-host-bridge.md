# Pi in a Herdr Docker Sandbox using a Mac-hosted model

Researched 2026-10-24 for the [Pi/sbx/Herdr integration decision](https://github.com/alenrig/macreset/issues/26). This is a source review. No Pi sandbox or local model server was started.

## Supported path

1. Install Pi on macOS and in the Linux sandbox. Pi's current installer is `curl -fsSL https://pi.dev/install.sh | sh`; the alternative npm package is `@earendil-works/pi-coding-agent` and requires Node.js **22.19+**. The installer pins dependencies and can install Node when needed; npm does not pin transitive dependencies. Verify each environment with `pi --version`. [Pi quickstart](https://pi.dev/docs/latest/quickstart), [Pi upstream README](https://github.com/earendil-works/pi#install-pi)
2. Run `llama-server` on the Mac. Pi's built-in llama.cpp integration speaks to its router, which discovers GGUF files in `--models-dir`. Pi's documented example uses `--jinja` for tool-call templates, `-ngl 999` for GPU offload, a bounded `-c` context, and `--host 127.0.0.1 --port 8080`. The loopback bind is expressly recommended for local-only access. [Pi local-model guide](https://pi.dev/docs/latest/llama-cpp); [Homebrew llama.cpp formula](https://formulae.brew.sh/formula/llama.cpp)
3. Configure host Pi with `LLAMA_BASE_URL=http://127.0.0.1:8080`. Pi accepts this environment variable instead of interactive `/login llama.cpp`. The chosen model must be visible in the router. With `--no-models-autoload`, it must first be loaded using `/llama`; with router autoload enabled, unloaded preset models can appear in `/model` and load when selected. Pi can select an exact model through `--provider llama.cpp --model <router-model-id>`, but the model ID should be verified against the installed router's `/models` response. [Pi local-model guide](https://pi.dev/docs/latest/llama-cpp); [Pi CLI models](https://pi.dev/docs/latest/cli)
4. For Pi **inside sbx**, use `LLAMA_BASE_URL=http://host.docker.internal:8080`. Docker says the sandbox proxy maps that hostname to host `localhost`; allow `localhost:8080` in the sbx network policy, for example `sbx policy allow network localhost:8080`. Requests to sandbox `127.0.0.1` or the Mac's LAN IP do not reach the host service. This is the documented way to keep a host service loopback-bound while allowing sandboxes to call it. The rule is global by default; `--sandbox <name>` narrows it to one sandbox, which needs a design decision because Herdr creates sandboxes dynamically. [Docker host-service access](https://docs.docker.com/ai/sandboxes/workflows/development/); [Docker local policy](https://docs.docker.com/ai/sandboxes/governance/access-controls/local/)
5. The Herdr plugin accepts a `customAgents.pi` adapter using `sbxAgent: "shell"`, `command: ["pi"]`, and a `setupScript` to install Pi the first time it prepares a sandbox. Set top-level `agentKind: "pi"` to make it the default and top-level `agentEnv: ["LLAMA_BASE_URL=http://host.docker.internal:8080"]` to pass the sandbox URL at launch. `agentArgs.pi` or `defaultArgs` can select the intended model; `agentArgs` replaces defaults in full. The shell workload ships without an agent binary. [Plugin configuration](https://github.com/dirien/herdr-sbx-plugin#configuration); [plugin adapter validation source](https://github.com/dirien/herdr-sbx-plugin/blob/main/src/agents.mjs); [Docker shell workload](https://docs.docker.com/ai/sandboxes/agents/shell/)

## Candidate plugin shape

This is an **inferred, untested** combination of documented plugin fields and Pi's CLI. Replace `<router-model-id>` after the model/runtime decision and verify Pi's installed path inside the sandbox.

```json
{
  "agentKind": "pi",
  "agentEnv": ["LLAMA_BASE_URL=http://host.docker.internal:8080"],
  "customAgents": {
    "pi": {
      "title": "Pi",
      "sbxAgent": "shell",
      "command": ["pi"],
      "defaultArgs": ["--provider", "llama.cpp", "--model", "<router-model-id>"],
      "herdrDetectionKind": "pi",
      "setupScript": "curl -fsSL https://pi.dev/install.sh | sh"
    }
  }
}
```

Pi is a known Herdr agent label, and Herdr's wrapper guidance explicitly says `HERDR_AGENT=<agent>` should be on the **host-visible** wrapper when the real agent is in a VM. The plugin's adapter code accepts any nonempty `herdrDetectionKind` string and its bridge sets `HERDR_AGENT` on the pane command. Thus `"pi"` is a plausible detection kind with working/waiting state, rather than `null`; verify it in an actual pane. Herdr also offers `herdr integration install pi` for host Pi, which reports state and session information, but an extension inside the VM should not be assumed to reach the host Herdr service. [Herdr agent and wrapper docs](https://herdr.dev/docs/agents/); [Herdr Pi integration](https://herdr.dev/docs/integrations/); [plugin adapter source](https://github.com/dirien/herdr-sbx-plugin/blob/main/src/agents.mjs); [plugin README](https://github.com/dirien/herdr-sbx-plugin#agents)

## Implications for the Ansible design

- `main.yml` currently runs Homebrew before `herdr`; `default.config.yml` holds its Homebrew package list. `roles/herdr/files/sbx-config.json` contains only `{"agentKind":"codex"}`, and `roles/herdr/tasks/main.yml` copies it to Herdr's plugin config. The new role and the revised file need a defined run order so the Mac server and Pi exist before Herdr launches Pi. [Repo playbook](../../main.yml), [defaults](../../default.config.yml), [Herdr config](../../roles/herdr/files/sbx-config.json), [Herdr tasks](../../roles/herdr/tasks/main.yml)
- Pi's installer and the plugin's `setupScript` serve different environments: the role installs host Pi; the setup script or a reusable sbx kit installs Linux Pi. The plugin's setup scripts run when it first prepares a sandbox and have a documented 30-minute timeout. The install network destinations must be allowed by sbx policy; a blocked setup should be diagnosed with `sbx policy log` and plugin `open-shell`. A prebuilt kit is an alternative if per-sandbox installs are too slow. [Plugin README](https://github.com/dirien/herdr-sbx-plugin#agents), [plugin troubleshooting](https://github.com/dirien/herdr-sbx-plugin#troubleshooting), [Docker shell workload](https://docs.docker.com/ai/sandboxes/agents/shell/)
- Pi's interactive `/llama` download is user-driven. For automatic Ansible download, a specific GGUF URL/revision and checksum would let `ansible.builtin.get_url` verify and avoid needless replacement; multiple shards need placement in one model subdirectory per Pi's guide. This is an implementation inference pending model selection. [Pi model layout/download](https://pi.dev/docs/latest/llama-cpp); [Ansible get_url](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/get_url_module.html)
- macOS can install `llama.cpp` through Homebrew, which provides `llama-server`. A persistent server could be managed by `community.general.launchd`, whose `started` state is idempotent; the service definition and restart-on-configuration-change still require design. [Homebrew formula](https://formulae.brew.sh/formula/llama.cpp); [Ansible launchd module](https://docs.ansible.com/ansible/latest/collections/community/general/launchd_module.html)

## Checks before implementation is considered complete

Check `pi --version` on host and inside shell sbx; `curl http://127.0.0.1:8080/health` and `/models` on host; `curl http://host.docker.internal:8080/health` in sandbox after the allow rule; `pi --list-models` or a small prompt with the selected model in both environments; and the plugin's `info`, `start-agent`, and `reconnect` actions with a visible Pi status in Herdr. These checks follow the tools each project documents; they have **not** been run here. [Pi troubleshooting](https://pi.dev/docs/latest/llama-cpp); [Pi CLI](https://pi.dev/docs/latest/cli); [Docker host-service access](https://docs.docker.com/ai/sandboxes/workflows/development/); [plugin actions](https://github.com/dirien/herdr-sbx-plugin#actions)
