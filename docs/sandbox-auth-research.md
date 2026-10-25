# Sandbox authentication research

## Scope and evidence

Question: can Herdr's `sbx` sandbox start Codex already authenticated using a
host Codex login, or would using Pi reuse the host Pi login?

Checked official Docker and OpenAI documentation, Pi documentation installed
with this host, Docker's Pi kit, and Herdr plugin source. Local CLI versions:
`sbx v0.49.2`, `codex-cli 0.164.0`. This is documentation/source research, not
an end-to-end authentication test. No credentials were read, copied, or changed.
`sbx secret ls --global --service openai` reported no stored global secret.

## Conclusion

**Use sbx's host-side OpenAI OAuth login once, then create new Codex sandboxes.**
Docker explicitly supports this: the browser flow runs on the host, tokens are
stored in its OS keychain, and credentials are not exposed inside the sandbox.
This is different from importing an existing host `codex login`. Docker says
sandboxes do not pick up host `~/.codex` configuration. [1]

Run on the host, before creating the sandbox:

```console
sbx secret set openai --oauth
```

The browser may reuse the current browser session, but whether it skips account
selection or consent was not verified. Do not promise a zero-interaction login.
The command and its `--oauth` flag were also confirmed with the installed CLI's
`sbx secret set --help`. Docker's documented automatic login prompt is for
`sbx run codex`; Herdr creates and launches sandboxes separately, so preparing
the secret explicitly avoids relying on that prompt. [1][5]

An API-key alternative is `sbx secret set openai`. If the key is already in the
host environment, `sbx secret import openai` imports `OPENAI_API_KEY`; that
command documents environment-variable import, not Codex/Pi OAuth-cache import.
Do not substitute a ChatGPT access token for an API key. [1][2]

## Existing host Codex login

OpenAI explicitly supports copying `~/.codex/auth.json` from a logged-in machine
to a headless machine or container. Thus reuse is technically possible when
file-based credentials are available, but it is **not automatic sandbox login**.
If the host uses an OS credential store, a usable auth file might not exist.
OpenAI documents the `cli_auth_credentials_store` setting and warns that the
file contains access tokens and must be treated like a password. [3]

Copying the cache into a sandbox gives the agent and its commands access to
real credentials, unlike sbx's proxy-managed path. Avoid mounting all of
`~/.codex`, and do not add credential copying to this playbook by default.
Refresh/persistence also needs consideration: OpenAI's automation guidance
notes that Codex can refresh the auth file and that updated credentials must
be retained for subsequent runs. A read-only mount should not be assumed to
support the complete credential lifecycle. [1][3]

No supported automatic import of the host Codex OAuth cache into sbx's secret
store was found in the checked documentation or installed CLI help. This is a
limit of the evidence, not proof that no future or custom integration can do it.

## Would switching to Pi help?

**Not by itself.** Pi stores `/login` credentials in its own `auth.json`; its
agent-directory default is `~/.pi/agent`, with `PI_CODING_AGENT_DIR` available
as an override. Mounting that directory exposes credentials as well as other
host Pi state. Pi's Docker documentation explicitly cautions against doing so
unless that exposure is intended. [4]

The current project adapter installs Pi in a `shell` sandbox and copies only
Ansible-managed model/settings files and host skills. It does not copy
`~/.pi/agent/auth.json`, mount the host agent directory, or configure Docker's
Pi kit. Therefore opting into `herdr_sbx_agent_kind: pi` does not implement
host-login reuse. See `roles/herdr/templates/sbx-config.json.j2`.

Pi supports proxy-managed Docker Sandboxes credentials, and Docker publishes a
Pi kit. However, the checked kit's documented OAuth integration is specifically
Anthropic: sbx materializes Pi-shaped sentinel credentials, and the proxy
handles real tokens and refresh. That is not evidence that this project's
OpenAI Pi adapter automatically shares a Codex or Pi host login. OpenAI support
would need its own verified kit/binding and request-routing configuration.
Pi's containerization documentation recommends configuring credentials before
sandbox creation rather than running `/login` inside the sandbox. [4][6]

## Project recommendation and remaining validation

- Keep Codex as the default sandbox adapter, now using `gpt-5.6-sol`, low
  reasoning, and the existing permissions. Host Pi model defaults are unchanged.
- The Herdr role now prepares the host sbx OpenAI OAuth credential when Codex
  is selected and no global OpenAI secret exists. It preserves existing sbx
  credentials, verifies presence after login, and skips login in check mode.
  Set `herdr_sbx_codex_authenticate: false` to manage authentication separately.
  It does not export/copy host Codex or Pi credentials.
- Create a fresh Herdr Codex sandbox and verify it can make a model request
  without a sandbox-side login. Neither that live test nor model entitlement
  for `gpt-5.6-sol` was verified in this research.
- Existing sandboxes, credentials, and generated host configuration were not
  changed by this repository edit. Run the playbook to deploy the new default;
  any `config.yml` override still takes precedence.

## Primary sources

1. [Docker: Codex sandbox authentication and configuration](https://docs.docker.com/ai/sandboxes/agents/codex/).
2. [Docker: sbx secret import](https://docs.docker.com/reference/cli/sbx/secret/import/)
   and [sbx secret set](https://docs.docker.com/reference/cli/sbx/secret/set/).
   Cross-checked against installed `sbx secret import --help` and
   `sbx secret set --help`.
3. [OpenAI: Codex authentication](https://developers.openai.com/codex/auth),
   especially Credential storage and Login on headless devices.
4. Pi first-party documentation: [providers](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/providers.md),
   [environment variables](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/environment-variables.md),
   and [containerization](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/containerization.md).
   Read from the installed package's `docs/` directory on this host.
5. Herdr plugin source at `369c420ed49a918513766dd2d804560bcc023948`:
   [sbx command construction](https://github.com/dirien/herdr-sbx-plugin/blob/369c420ed49a918513766dd2d804560bcc023948/src/sbx.mjs)
   and [sandbox lifecycle](https://github.com/dirien/herdr-sbx-plugin/blob/369c420ed49a918513766dd2d804560bcc023948/src/lifecycle.mjs).
6. [Docker's Pi kit README](https://github.com/docker/sbx-kits-contrib/blob/b5e2012b4419a518f7dc9d9ea35c05303b65e2d6/pi/README.md),
   especially How auth works and the warnings about `/login` and bindings at
   sandbox creation. This is a separate integration from this project's adapter.
