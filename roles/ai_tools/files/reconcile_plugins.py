#!/usr/bin/env python3
"""Install and enable only declared Herdr marketplace plugins.

Input: AI_HERDR_PLUGINS_JSON, a list of {source, ref?} objects.
Output: JSON with ``changed`` for Ansible.
"""

import json
import os
import re
import shutil
import subprocess

from declarations import load_list, reject_duplicate, require_fields, validate_ref


SOURCE_PART = re.compile(r"^[A-Za-z0-9_.-]+$")
COMMIT = re.compile(r"^[0-9a-fA-F]{40}$")


def fail(message):
    print(json.dumps({"changed": False, "error": message}))
    raise SystemExit(1)


def run(argv, description):
    try:
        result = subprocess.run(argv, text=True, capture_output=True, check=False)
    except OSError as exc:
        fail(f"{description}: {exc}")
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        fail(f"{description}: {detail or 'command failed'}")
    return result.stdout


def load_desired():
    desired = load_list("AI_HERDR_PLUGINS_JSON", "ai_herdr_plugins", fail)
    seen = set()
    for item in desired:
        require_fields(item, {"source", "ref"}, "ai_herdr_plugins", fail)
        source, ref = item.get("source"), item.get("ref")
        parts = source.split("/") if isinstance(source, str) else []
        if (len(parts) < 2 or any(not SOURCE_PART.fullmatch(part) or part in (".", "..")
                                  for part in parts)):
            fail(f"Invalid Herdr plugin source {source!r}; use public GitHub owner/repo[/subdir]")
        validate_ref(ref, f"Herdr plugin {source}", fail)
        normalized = source.lower()
        reject_duplicate(normalized, seen, "Herdr plugin source", fail)
    return desired


def list_plugins():
    output = run(["herdr", "plugin", "list", "--json"],
                 "Cannot list Herdr plugins; update Herdr if plugin commands are unsupported")
    try:
        plugins = json.loads(output)["result"]["plugins"]
        if not isinstance(plugins, list):
            raise ValueError("plugins is not a list")
        return plugins
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        fail(f"Unexpected Herdr plugin list JSON; update Herdr: {exc}")


def source_matches(plugin, parts):
    source = plugin.get("source") or {}
    if source.get("kind") != "github":
        return False
    if (str(source.get("owner", "")).lower(), str(source.get("repo", "")).lower()) != (
            parts[0].lower(), parts[1].lower()):
        return False
    managed = source.get("managed_path")
    root = plugin.get("plugin_root")
    if not isinstance(managed, str) or not isinstance(root, str):
        fail(f"Herdr plugin {plugin.get('plugin_id')} has incomplete GitHub source metadata")
    relative = os.path.relpath(root, managed)
    if relative == ".." or relative.startswith("../"):
        fail(f"Herdr plugin {plugin.get('plugin_id')} is outside its managed checkout")
    return relative.lower() == ("/".join(parts[2:]).lower() if len(parts) > 2 else ".")


def remote_commit(source, ref):
    parts = source.split("/")
    url = f"https://github.com/{parts[0]}/{parts[1]}.git"
    if ref and COMMIT.fullmatch(ref):
        return ref.lower()
    patterns = (["refs/heads/" + ref, "refs/tags/" + ref, "refs/tags/" + ref + "^{}"]
                if ref else ["HEAD"])
    output = run(["git", "ls-remote", "--exit-code", url, *patterns],
                 f"Cannot resolve {source} at {ref or 'HEAD'}; check the public source and ref")
    refs = dict(line.split("\t", 1)[::-1] for line in output.splitlines() if "\t" in line)
    chosen = (refs.get("refs/heads/" + ref) or refs.get("refs/tags/" + ref + "^{}")
              or refs.get("refs/tags/" + ref)) if ref else refs.get("HEAD")
    if not chosen or not COMMIT.fullmatch(chosen):
        fail(f"Cannot resolve {source} at {ref or 'HEAD'} to a Git commit")
    return chosen.lower()


def main():
    desired = load_desired()
    if not desired:
        print(json.dumps({"changed": False, "installed": [], "enabled": []}))
        return
    for command in ("herdr", "git"):
        if shutil.which(command) is None:
            fail(f"{command} is required for Herdr marketplace plugins; install it first")
    plugins = list_plugins()
    # Validate every declaration and remote before changing any installed plugin.
    planned = []
    for item in desired:
        source, ref = item["source"], item.get("ref")
        matches = [plugin for plugin in plugins if source_matches(plugin, source.split("/"))]
        if len(matches) > 1:
            fail(f"Several installed Herdr plugins match {source}; resolve the conflict manually")
        existing = matches[0] if matches else None
        commit = remote_commit(source, ref)
        if existing and not isinstance(existing.get("source", {}).get("resolved_commit"), str):
            fail(f"Herdr plugin {existing.get('plugin_id')} has no installed commit; inspect it manually")
        planned.append((item, existing, commit))

    installed, enabled = [], []
    for item, existing, commit in planned:
        source, ref = item["source"], item.get("ref")
        if existing is None or existing["source"]["resolved_commit"].lower() != commit:
            argv = ["herdr", "plugin", "install", source]
            if ref:
                argv.extend(["--ref", ref])
            argv.append("--yes")
            run(argv, f"Cannot install {source}; check source/ref, Herdr version, or linked-plugin conflict")
            installed.append(source)
            matches = [plugin for plugin in list_plugins()
                       if source_matches(plugin, source.split("/"))]
            if len(matches) != 1:
                fail(f"Herdr installed {source}, but could not identify its plugin; inspect plugin list")
            existing = matches[0]
            if existing["source"].get("resolved_commit", "").lower() != commit:
                fail(f"Herdr installed {source} at a different commit than the requested ref")
        if not existing.get("enabled"):
            plugin_id = existing.get("plugin_id")
            if not isinstance(plugin_id, str) or not plugin_id:
                fail(f"Herdr plugin from {source} has no plugin ID")
            run(["herdr", "plugin", "enable", plugin_id],
                f"Cannot enable Herdr plugin {plugin_id}; update Herdr or inspect the plugin")
            enabled.append(plugin_id)
    print(json.dumps({"changed": bool(installed or enabled), "installed": installed, "enabled": enabled}))


if __name__ == "__main__":
    main()
