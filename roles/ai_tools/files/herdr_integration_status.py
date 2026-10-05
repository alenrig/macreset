"""Read Herdr's integration status without changing any installed integration."""

import json
import re
import shutil
import subprocess
import sys


MANAGED = ("codex", "cursor")
STATUS = re.compile(r"^(?P<name>[a-z][a-z0-9-]*):\s*(?P<state>current|outdated|not installed)(?:\s|$)")


def main():
    if shutil.which("herdr") is None:
        raise RuntimeError("Herdr is missing from PATH. Install Herdr before running the AI tools role.")

    result = subprocess.run(
        ["herdr", "integration", "status"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no diagnostic output"
        raise RuntimeError(
            "Cannot read Herdr integration status. Upgrade Herdr to a version that supports "
            f"'herdr integration status' for Codex and Cursor. Herdr said: {detail}"
        )

    states = {}
    for line in result.stdout.splitlines():
        match = STATUS.match(line.strip())
        if not match or match.group("name") not in MANAGED:
            continue
        name = match.group("name")
        if name in states:
            raise RuntimeError(f"Herdr reported duplicate integration status for {name}.")
        states[name] = match.group("state")

    missing = set(MANAGED) - states.keys()
    if missing:
        names = ", ".join(sorted(missing))
        raise RuntimeError(
            f"Herdr did not report a supported status for {names}. Upgrade Herdr to a version "
            "that supports the Codex and Cursor integrations."
        )
    print(json.dumps(states))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        print(f"Herdr integration preflight failed: {error}", file=sys.stderr)
        sys.exit(1)
