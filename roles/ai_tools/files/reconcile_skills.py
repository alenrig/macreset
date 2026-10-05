#!/usr/bin/env python3
"""Install declared user-level skills without taking over unrelated skills.

Input: AI_SKILLS_JSON, a list of {source, name, ref?} objects. Output: JSON with
``changed`` for Ansible. The skills CLI owns installation and its provenance lock.
"""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


SOURCE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REF = re.compile(r"^[A-Za-z0-9_./-]+$")


def fail(message):
    print(json.dumps({"changed": False, "error": message}))
    raise SystemExit(1)


def load_desired():
    try:
        desired = json.loads(os.environ["AI_SKILLS_JSON"])
    except (KeyError, json.JSONDecodeError) as exc:
        fail(f"ai_skills must be a JSON-compatible list: {exc}")
    if not isinstance(desired, list):
        fail("ai_skills must be a list")
    seen = set()
    for item in desired:
        if not isinstance(item, dict) or set(item) - {"source", "name", "ref"}:
            fail("Each ai_skills entry needs source, name, and optional ref only")
        source, name, ref = item.get("source"), item.get("name"), item.get("ref")
        if not isinstance(source, str) or not SOURCE.fullmatch(source):
            fail(f"Invalid skill source {source!r}; use GitHub owner/repo shorthand")
        if not isinstance(name, str) or not NAME.fullmatch(name):
            fail(f"Invalid skill name {name!r}")
        if ref is not None and (not isinstance(ref, str) or not REF.fullmatch(ref)
                                or ref.startswith("/") or ".." in ref.split("/")):
            fail(f"Invalid Git ref for {name}: {ref!r}")
        if name in seen:
            fail(f"Duplicate skill name in ai_skills: {name}")
        seen.add(name)
    return desired


def load_lock(home):
    state_home = os.environ.get("XDG_STATE_HOME")
    lock_path = (Path(state_home) / "skills" / ".skill-lock.json" if state_home
                 else home / ".agents" / ".skill-lock.json")
    try:
        return json.loads(lock_path.read_text()).get("skills", {}) if lock_path.exists() else {}
    except (OSError, json.JSONDecodeError, AttributeError) as exc:
        fail(f"Cannot read skills provenance at {lock_path}: {exc}")


def upstream_hashes(desired, lock):
    """Read Git tree hashes for the declared, installed, unpinned skills only."""
    by_source = {}
    for item in desired:
        name = item["name"]
        recorded = lock.get(name)
        if item.get("ref") is not None or not isinstance(recorded, dict):
            continue
        skill_path = recorded.get("skillPath")
        if not isinstance(skill_path, str):
            by_source.setdefault(item["source"], []).append((name, None))
            continue
        path = Path(skill_path)
        if (path.is_absolute() or path.name != "SKILL.md"
                or not path.parent.parts or ".." in path.parts):
            fail(f"Invalid recorded skill path for {name}: {skill_path!r}")
        by_source.setdefault(item["source"], []).append((name, path.parent.as_posix()))

    hashes = {}
    for source, skills in by_source.items():
        with tempfile.TemporaryDirectory(prefix="macreset-skills-") as checkout:
            result = subprocess.run(
                ["git", "clone", "--quiet", "--depth", "1", "--filter=blob:none",
                 f"https://github.com/{source}.git", checkout],
                text=True, capture_output=True, check=False,
            )
            if result.returncode:
                fail(f"Could not check upstream skills from {source}: "
                     f"{result.stderr.strip() or result.stdout.strip()}")
            for name, folder in skills:
                if folder is None:
                    hashes[name] = None
                    continue
                result = subprocess.run(
                    ["git", "-C", checkout, "rev-parse", "--verify", f"HEAD:{folder}"],
                    text=True, capture_output=True, check=False,
                )
                if result.returncode:
                    fail(f"Skill {name} is no longer at its recorded path in {source}; "
                         "resolve the upstream move before rerunning macreset")
                hashes[name] = result.stdout.strip()
    return hashes


def main():
    desired = load_desired()
    for command in ("python3", "node", "npx", "git"):
        if shutil.which(command) is None:
            fail(f"{command} is required for Agent Skills; install it before this role")
    home = Path.home()
    lock = load_lock(home)
    canonical = home / ".agents" / "skills"
    agent_dirs = [home / ".codex" / "skills", home / ".cursor" / "skills"]

    # Check every declaration before any installer invocation can mutate a skill.
    for item in desired:
        name, source = item["name"], item["source"]
        paths = [canonical / name] + [directory / name for directory in agent_dirs]
        occupied = any(path.exists() or path.is_symlink() for path in paths)
        recorded = lock.get(name)
        if occupied and (not isinstance(recorded, dict)
                         or recorded.get("sourceType") != "github"
                         or recorded.get("source", "").lower() != source.lower()):
            fail(f"Skill {name} already exists, but its recorded source is not {source}; "
                 "resolve this conflict manually before rerunning macreset")
        if (isinstance(recorded, dict) and isinstance(recorded.get("source"), str)
                and recorded["source"].lower() != source.lower()):
            fail(f"Skill {name} is recorded from {recorded['source']}, not {source}")

    # Complete conflict checks before fetching or changing any declared skill.
    hashes = upstream_hashes(desired, lock)
    installed = []
    for item in desired:
        name, source, ref = item["name"], item["source"], item.get("ref")
        paths = [canonical / name] + [directory / name for directory in agent_dirs]
        recorded = lock.get(name, {})
        present = all(path.exists() for path in paths)
        same_ref = isinstance(recorded, dict) and recorded.get("ref") == ref
        current = (ref is not None or
                   (isinstance(recorded, dict)
                    and recorded.get("skillFolderHash") == hashes.get(name)
                    and hashes.get(name) is not None))
        if present and same_ref and current:
            continue
        source_arg = f"{source}#{ref}" if ref else source
        argv = ["npx", "--yes", "skills@latest", "add", source_arg,
                "--skill", name, "--global", "--agent", "codex", "--agent", "cursor", "--yes"]
        result = subprocess.run(argv, text=True, capture_output=True, check=False)
        if result.returncode:
            fail(f"Could not install {name} from {source_arg}: "
                 f"{result.stderr.strip() or result.stdout.strip()}")
        if not all(path.exists() for path in paths):
            fail(f"skills reported success, but {name} is missing from the shared "
                 "directory or a Codex/Cursor link")
        installed.append(name)
        lock = load_lock(home)
    print(json.dumps({"changed": bool(installed), "installed": installed}))


if __name__ == "__main__":
    main()
