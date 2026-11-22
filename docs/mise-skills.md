# Flux schema and agent skills

Run `mise run agents:maintain` from the trusted checkout after installing the
Flux CLI through the package setup. The task installs or updates the Flux
schema plugin and verifies it against the latest stable release. It reports
the Packslip skill gap after Flux verification succeeds. Full setup wiring
belongs to #57. The Ansible setup remains available during the transition.

## Deferred Packslip skills

- `fluxcd/agent-skills` v0.4.0 has checksum and skill archives but no signed
  Packslip bundle. Deferred skills are `gitops-knowledge`,
  `gitops-repo-audit`, and `gitops-cluster-debug`. The publisher can add a
  signed Packslip release declaring each skill and covering its archive digest
  or its source directory at the release commit.
  [Flux agent skills releases](https://github.com/fluxcd/agent-skills/releases)
- `mattpocock/skills` v1.3.2 has a tagged source release with no uploaded
  assets or signed Packslip bundle. Deferred skills are `ask-matt`,
  `code-review`, `codebase-design`, `diagnosing-bugs`, `domain-modeling`,
  `grill-with-docs`, `implement-spec`, `implement`,
  `improve-codebase-architecture`, `prototype`, `research`, `retro`,
  `setup-matt-pocock-skills`, `tdd`, `to-spec`, `to-tickets`, `triage`,
  `wayfinder`, `grill-me`, `grilling`, `handoff`, `teach`,
  `to-questionnaire`, `wait-what`, and `writing-for-agents`. The publisher
  would need to publish a compatible release artifact and signed bundle
  declaring those skill directories at the release commit or as signed assets.
  [Matt Pocock skills releases](https://github.com/mattpocock/skills/releases)

The minimum supported mise release, 2026.11.11, provides
`mise skills ls` and `mise skills sync`. Direct Packslip installs of both
versions above fail because the release bundle is absent. The
`repo:` resource format refers to a source directory in a signed release
manifest. A consumer's `mise.toml` selects a Packslip release and has no
inline skill-resource declaration. A local `release.toml` is input for
signing releases. A repackager would need to publish and sign its own
release, with a separate trust configuration.
[mise Packslip backend](https://mise.jdx.dev/dev-tools/backends/packslip.html)
[Packslip resource declarations](https://packslip.dev/docs/resources/)

When eligible bundles exist, declare the publisher versions in mise, check
the exact allowlists with `mise skills ls --json`, and use
`mise skills sync --dir` for the destinations Codex and Cursor read. Sync
links every skill from the active tools, so verify the active tool set and
the resources it exposes before syncing. It skips an existing directory or
unrelated symlink at a skill name. Resolve any conflict with the owner
before moving an existing installation. Until then, the task reports zero
skills installed and leaves owner skill paths as they are.
[mise skill sync](https://mise.jdx.dev/dev-tools/packslip-resources.html#skills)
