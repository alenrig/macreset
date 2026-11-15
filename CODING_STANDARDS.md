# Coding standards

These standards apply to setup and maintenance. `bootstrap.sh` installs or
locates mise; mise owns machine configuration and explicit maintenance.
`macreset.sh` delegates to the same bootstrap.

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

## Review questions

1. Does each behavior have a clear owner, inventory and override path?
2. Are native resources used where their semantics fit the existing behavior?
3. Do prerequisites and dependent resources run in a predictable order?
4. Do partial failure and rerun preserve private state and converge?
5. Are remaining native gaps and compatibility limits documented?
