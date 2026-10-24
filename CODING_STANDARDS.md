# Coding standards

These standards apply to new and modified setup code in this repository. In a
diff review, report violations in changed behavior; do not report unchanged
legacy code merely because it is nearby. Apply the hard requirements below as
rules. Treat the review guidelines as prompts for a finding only when the diff
provides concrete evidence of a maintenance or correctness problem. Leave
formatting and other rules already enforced by `ansible-lint` to the linter.

## Hard requirements: Ansible owns setup

1. Express every setup action as an Ansible play, role, or task. This includes
   setup performed later in a sandbox or other environment created by the
   playbook. Do not write, download, template, or invoke Python, shell, or
   other scripts to perform setup. The ban covers inline interpreter snippets
   and scripts embedded in generated configuration. Ansible's own runtime and
   modules are outside the meaning of "script" here.
2. Prefer a purpose-built Ansible module for the desired state. Use
   `ansible.builtin.command` only when no suitable module can perform the
   action. In that case, invoke the target CLI directly with `argv`, document
   why the module route is unavailable, and make the task's change and failure
   conditions reflect observed state. `command` must not be used to invoke a
   shell, interpreter, script file, or inline program. Do not use
   `ansible.builtin.shell`, `raw`, or `script` for setup.
3. Existing Ansible roles and collection modules may be used. The preference
   for `ansible.builtin` modules applies when a suitable built-in module
   exists; it does not ban the project's declared Ansible dependencies.

The Herdr sbx plugin's `customAgents.pi.setupScript` is a narrow exception to
the first rule. Herdr runs it inside each newly created sandbox, which is not
an Ansible inventory host. It may install Pi and copy Ansible-managed model
files and host skills into that sandbox. Keep the setup in the plugin's
configuration and limit it to those first-start actions.

## Review guidelines: structure and execution

- Let a play choose the target host and the sequence of roles or tasks. Keep
  each role focused on configuring its assigned target. If a future change
  configures another host, add a play for that host instead of making a role
  secretly switch hosts or connection settings.
- Keep the current `localhost` play easy to read: use `pre_tasks` for work
  needed before roles and `post_tasks` for work that depends on them. If a
  play uses roles, avoid a second, substantial `tasks` sequence whose timing
  relative to the roles is easy to miss. Remember that notified handlers run
  at section boundaries.
- Use a role when its defaults or separate tasks, files, and templates make a
  cohesive setup concern clearer. Use a small play-level task for simple
  orchestration; do not create a role solely to wrap one module call.
- Use a handler for an action that should run only after a task reports a
  change. Use a normal idempotent task for a state that must be ensured on
  every run. Keep handler names distinct and avoid cross-role notifications
  that hide dependencies.

## Review guidelines: configuration and variables

- Keep portable setup behavior in the playbook and roles. Put Mac-specific
  choices that a user may override in the documented `config.yml` overlay;
  keep repository defaults in `default.config.yml` or a role's
  `defaults/main.yml` where appropriate. Avoid making users override a
  high-precedence role variable to change a supported setting.
- Use variables for a real choice or repeated value, not to turn straightforward
  task flow into a chain of Jinja calculations. Prefer native YAML booleans,
  numbers, lists, and maps; avoid constructing typed data by concatenating
  strings and relying on implicit conversion.
- Give related variables one clear owner and distinct names. Avoid defining
  the same key at multiple precedence levels unless an override is an
  intentional, documented interface. Use `set_fact` or `register` for values
  learned during execution, not as a substitute for clear defaults and inputs.
  Account for when a Jinja value is evaluated, especially if it refers to a
  fact or task-local value.
- Treat this repository's inventory as the `localhost` execution target. Do
  not add fake hosts or dynamic groups as storage for configuration. If the
  project later manages multiple hosts, give each managed target an inventory
  entry and use meaningful groups and plays to express where work runs.

## Review questions

For each changed setup path, ask:

1. Is the complete setup expressed through Ansible tasks, including any later
   setup inside a generated environment, apart from the Herdr Pi exception?
2. If `command` appears, is there genuinely no suitable module, is the CLI
   invoked directly without a script or interpreter, and is repeat-run state
   handled explicitly?
3. Does the play make the execution target and ordering obvious?
4. Do configuration values have a clear source and override path? Can a
   reader predict their types and when they are evaluated?
5. Will a second run converge without reporting an artificial change, and
   will required service or resource state still be ensured after a partial
   earlier run?

## Sources

The review guidelines adapt the following articles to this repository's
single-host Mac setup. Their multi-host inventory examples are background for
future expansion, not current requirements. The hard Ansible-only setup rule
is a project decision, not a claim made by these articles.

- [Ansible foundations, part 1: plays, roles, tasks, and handlers](https://habr.com/ru/articles/508762/)
- [Ansible foundations, part 2: inventory and configuration placement](https://habr.com/ru/articles/509938/)
- [Ansible foundations, part 3: variables, evaluation, and precedence](https://habr.com/ru/articles/512036/)
- [Ansible `command` module documentation](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/command_module.html)
