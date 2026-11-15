# Coding standards

These standards apply to changed setup behavior. During the #41 migration,
`bootstrap.sh` and mise own the migrated setup; `macreset.sh`, `main.yml`, and
roles remain available for capabilities that have not cut over yet.

## Setup ownership

- Keep the outer bootstrap limited to locating/installing a documented mise
  version and invoking it, preserving failures and private overrides.
- Prefer native mise package, repository, dotfile and service declarations.
  Keep one inventory per concern. Use small mise-owned scripts for behavior
  native resources cannot express; document each gap and its fallback.
- Encode ordering through task dependencies or bootstrap phases. Prerequisites
  must finish before dependent operations on the first run.
- Inspect actual state on rerun. Preserve validation, useful errors, file
  permissions, backups, dirty checkout protection and service health checks.
- Never treat network/authentication errors as missing state. Propagate failures.
  Do not add broad prune, runtime removal or destructive maintenance to setup.
- Put private choices in ignored `mise.local.toml`; document their precedence.
  Never silently ignore or delete legacy `config.yml`.
- Do not add tests for this migration (explicit parent #41 decision). Retain
  operational checks. Record unverified machine compatibility honestly.

## Legacy path until cutover

Keep existing Ansible entrypoints usable while each concern migrates. Prefer
Ansible modules for changes to remaining legacy roles, and direct CLI commands
only for unsupported module behavior. Do not route new mise setup through
Ansible or add new parallel inventories. Remove legacy machinery only once
its executable behavior has a replacement.

## Review questions

1. Does each behavior have a clear owner, inventory and override path?
2. Are native resources used where their semantics fit the existing behavior?
3. Do prerequisites and dependent resources run in a predictable order?
4. Do partial failure and rerun preserve private state and converge?
5. Are remaining native gaps and compatibility limits documented?
