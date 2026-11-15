# Agent skills and CLI plugins

Run `mise run skills` for the configured global skills and `mise run plugins`
for Flux schema and Helm unittest. The tasks install their Node / package
prerequisites first. The complete setup task waits for both tasks; Ansible is retired.

`vars.agent_skills` in `mise.toml` is a JSON source/name mapping. Override the
whole mapping in ignored `mise.local.toml` to change it; this replaces the
legacy `flux_agent_skills` and `matt_pocock_agent_skills` lists. Existing private
`config.yml` is never deleted; translate its choices before using mise.

Skills continue to use `npx --yes skills`, global Codex and Cursor registration,
and the CLI's canonical `~/.agents/skills` directory and `.skill-lock.json`.
Each run inventories installed skills, checks source, both agents, lock source,
path metadata and Git tree content hash. Missing, damaged or mismatched entries
are repaired with `skills add`; healthy entries are refreshed with `skills
update`. Final inventory and lock/content checks must pass. Temporary Git object
stores are removed in `finally`, including failures. Unmanaged skills remain.
Network/authentication errors and malformed inventory/lock data fail the task.
The CLI is resolved through npm as in the legacy implementation; this does not
pin or independently authenticate its npm distribution.

Flux keeps its catalog validation and GitHub latest stable release resolution.
An absent schema plugin is installed; a stale one is updated. Final inventory
must report the resolved version. Catalog, release and command errors propagate.

Helm unittest supports Helm 3's upstream Git installation and Helm 4's signed
release archive installation. Each run resolves the upstream stable release and
checks CLI inventory plus plugin directory metadata. Updates install the exact
release in an isolated plugin directory before replacing the old installation.
Helm 4 always uses `--verify=true` with a dedicated temporary keyring, populated
from upstream's HTTPS `public-key.asc`; it never changes the user's GPG keyring
or disables verification. `gnupg` is the additional native formula prerequisite.
The trust root is upstream's HTTPS key publication, not a separately pinned key
fingerprint. Helm 3 retains upstream Git installation's weaker verification.

The staged plugin must report the desired version before replacement. Existing
plugins are backed up on the same filesystem; final verification failure rolls
back the previous directory. If rollback itself fails, an error names the backup
retained for manual recovery. Normal temporary workspaces are always removed.
Helm's update command is deliberately avoided because its OCI update can delete
the installed plugin before installation and has no explicit keyring/verification
flags. New releases missing a valid signed archive/provenance fail safely on
Helm 4. Unknown/duplicate/corrupt inventories fail rather than imply absence.

Native mise package declarations cover prerequisites; native tool-distributed
skills sync does not preserve this CLI lock/content contract, and Flux/Helm
plugin lifecycle lacks native parity, so these remain explicit tasks. Setup is
not transactional across skills and plugins; rerun after fixing a failure.
No tests or machine setup runs were performed for this migration. Fresh Mac,
Intel, npm CLI compatibility, plugin hook behavior and actual signed release
availability remain unverified.
