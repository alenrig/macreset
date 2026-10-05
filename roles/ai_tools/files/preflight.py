#!/usr/bin/env python3
"""Check the whole AI tools role before it changes installed state."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import herdr_integration_status
import reconcile_plugins
import reconcile_skills


def check_skill_source(source, ref, names):
    with tempfile.TemporaryDirectory(prefix="macreset-skill-preflight-") as checkout:
        argv = ["git", "clone", "--quiet", "--depth", "1", "--filter=blob:none"]
        if ref and not reconcile_plugins.COMMIT.fullmatch(ref):
            argv.extend(["--branch", ref])
        argv.extend([f"https://github.com/{source}.git", checkout])
        result = subprocess.run(argv, text=True, capture_output=True, check=False)
        if result.returncode:
            raise RuntimeError(f"Cannot read skill source {source} at {ref or 'HEAD'}: "
                               f"{result.stderr.strip() or result.stdout.strip()}")
        if ref and reconcile_plugins.COMMIT.fullmatch(ref):
            result = subprocess.run(["git", "-C", checkout, "fetch", "--quiet", "--depth", "1",
                                     "origin", ref], text=True, capture_output=True, check=False)
            if result.returncode:
                raise RuntimeError(f"Cannot resolve skill ref {source}#{ref}: "
                                   f"{result.stderr.strip() or result.stdout.strip()}")
            result = subprocess.run(["git", "-C", checkout, "checkout", "--quiet", "FETCH_HEAD"],
                                    text=True, capture_output=True, check=False)
            if result.returncode:
                raise RuntimeError(f"Cannot check out skill ref {source}#{ref}: {result.stderr.strip()}")
        for name in names:
            matches = reconcile_skills.find_skill_paths(checkout, name)
            if len(matches) != 1:
                raise RuntimeError(f"Skill {name} from {source} at {ref or 'HEAD'} has "
                                   f"{len(matches)} matching paths; check the source or name")


def check_plugin_commit(source, ref):
    with tempfile.TemporaryDirectory(prefix="macreset-plugin-preflight-") as checkout:
        result = subprocess.run(["git", "init", "--quiet", checkout],
                                text=True, capture_output=True, check=False)
        if result.returncode:
            raise RuntimeError(f"Cannot prepare plugin ref check: {result.stderr.strip()}")
        parts = source.split("/")
        result = subprocess.run(
            ["git", "-C", checkout, "fetch", "--quiet", "--depth", "1",
             f"https://github.com/{parts[0]}/{parts[1]}.git", ref],
            text=True, capture_output=True, check=False,
        )
        if result.returncode:
            raise RuntimeError(f"Cannot resolve Herdr plugin ref {source}#{ref}: "
                               f"{result.stderr.strip() or result.stdout.strip()}")


def main():
    skills = reconcile_skills.load_desired()
    plugins = reconcile_plugins.load_desired()
    for command in ("python3", "node", "npx", "git", "herdr"):
        if shutil.which(command) is None:
            raise RuntimeError(f"{command} is required for AI tools; install it before this role")

    home = Path.home()
    lock = reconcile_skills.load_lock(home)
    reconcile_skills.check_conflicts(skills, lock, home)
    grouped = {}
    for item in skills:
        grouped.setdefault((item["source"], item.get("ref")), []).append(item["name"])
    for (source, ref), names in grouped.items():
        check_skill_source(source, ref, names)

    # Probe both Herdr command families before either one can change local state.
    for command in (("integration", "install"), ("plugin", "install"),
                    ("plugin", "enable")):
        argv = ["herdr", *command, "--help"]
        result = subprocess.run(argv, text=True, capture_output=True, check=False)
        if result.returncode:
            raise RuntimeError(f"Herdr does not support {' '.join(command)}; update Herdr: "
                               f"{result.stderr.strip() or result.stdout.strip()}")
    states = herdr_integration_status.get_states()
    installed = reconcile_plugins.list_plugins()
    for item in plugins:
        source, ref = item["source"], item.get("ref")
        matches = [plugin for plugin in installed
                   if reconcile_plugins.source_matches(plugin, source.split("/"))]
        if len(matches) > 1:
            raise RuntimeError(f"Several installed Herdr plugins match {source}")
        if matches and not isinstance(matches[0].get("source", {}).get("resolved_commit"), str):
            raise RuntimeError(f"Herdr plugin {matches[0].get('plugin_id')} has no installed commit")
        if ref and reconcile_plugins.COMMIT.fullmatch(ref):
            check_plugin_commit(source, ref)
        reconcile_plugins.remote_commit(source, ref)
    print(json.dumps({"changed": False, "integrations": states}))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        print(f"AI tools preflight failed: {error}", file=sys.stderr)
        sys.exit(1)
