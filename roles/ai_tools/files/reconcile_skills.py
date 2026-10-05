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
import tempfile

from declarations import load_list, reject_duplicate, require_fields, validate_ref


SOURCE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def fail(message):
    print(json.dumps({"changed": False, "error": message}))
    raise SystemExit(1)


def load_desired():
    desired = load_list("AI_SKILLS_JSON", "ai_skills", fail)
    seen = set()
    for item in desired:
        require_fields(item, {"source", "name", "ref"}, "ai_skills", fail)
        source, name, ref = item.get("source"), item.get("name"), item.get("ref")
        if (not isinstance(source, str) or not SOURCE.fullmatch(source)
                or any(part in (".", "..") for part in source.split("/"))):
            fail(f"Invalid skill source {source!r}; use GitHub owner/repo shorthand")
        if not isinstance(name, str) or not NAME.fullmatch(name):
            fail(f"Invalid skill name {name!r}")
        validate_ref(ref, name, fail)
        reject_duplicate(name, seen, "skill name in ai_skills", fail)
    return desired


def load_lock(home):
    state_home = os.environ.get("XDG_STATE_HOME")
    lock_path = (Path(state_home) / "skills" / ".skill-lock.json" if state_home
                 else home / ".agents" / ".skill-lock.json")
    try:
        lock = json.loads(lock_path.read_text()).get("skills", {}) if lock_path.exists() else {}
        if not isinstance(lock, dict):
            raise ValueError("skills is not an object")
        return lock
    except (OSError, json.JSONDecodeError, AttributeError, ValueError) as exc:
        fail(f"Cannot read skills provenance at {lock_path}: {exc}")


def check_conflicts(desired, lock, home):
    canonical = home / ".agents" / "skills"
    agent_dirs = [home / ".codex" / "skills", home / ".cursor" / "skills"]
    for item in desired:
        name, source = item["name"], item["source"]
        paths = [canonical / name] + [directory / name for directory in agent_dirs]
        occupied = any(path.exists() or path.is_symlink() for path in paths)
        recorded = lock.get(name)
        if occupied and (not isinstance(recorded, dict)
                         or recorded.get("sourceType") != "github"
                         or not isinstance(recorded.get("source"), str)
                         or recorded["source"].lower() != source.lower()):
            fail(f"Skill {name} already exists, but its recorded source is not {source}; "
                 "resolve this conflict manually before rerunning macreset")
        if (isinstance(recorded, dict) and isinstance(recorded.get("source"), str)
                and recorded["source"].lower() != source.lower()):
            fail(f"Skill {name} is recorded from {recorded['source']}, not {source}")


def find_skill_paths(checkout, name):
    matches = []
    for candidate in Path(checkout).rglob("SKILL.md"):
        if ".git" in candidate.parts:
            continue
        if candidate.parent.name == name:
            matches.append(candidate.parent.relative_to(checkout).as_posix())
            continue
        try:
            lines = candidate.read_text().splitlines()
        except OSError as exc:
            fail(f"Cannot inspect upstream skill {candidate}: {exc}")
        if lines and lines[0].strip() == "---":
            for line in lines[1:]:
                if line.strip() == "---":
                    break
                if line.strip() in (f"name: {name}", f'name: "{name}"',
                                    f"name: '{name}'"):
                    matches.append(candidate.parent.relative_to(checkout).as_posix())
                    break
    return matches


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
                matches = find_skill_paths(checkout, name)
                if len(matches) != 1:
                    fail(f"Skill {name} from {source} has "
                         f"{len(matches)} matching upstream paths; check the source or name")
                folder = matches[0]
                result = subprocess.run(
                    ["git", "-C", checkout, "rev-parse", "--verify", f"HEAD:{folder}"],
                    text=True, capture_output=True, check=False,
                )
                if result.returncode:
                    fail(f"Skill {name} is no longer at its recorded path in {source}; "
                         "resolve the upstream move before rerunning macreset")
                hashes[name] = (result.stdout.strip(), f"{folder}/SKILL.md")
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

    check_conflicts(desired, lock, home)

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
                    and hashes.get(name) is not None
                    and recorded.get("skillFolderHash") == hashes[name][0]
                    and recorded.get("skillPath") == hashes[name][1]))
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
