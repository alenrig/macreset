"""Shared validation for the role's declarative source lists."""

import json
import os
import re


REF = re.compile(r"^[A-Za-z0-9_./-]+$")


def load_list(environment, label, fail):
    try:
        desired = json.loads(os.environ[environment])
    except (KeyError, json.JSONDecodeError) as exc:
        fail(f"{label} must be a JSON-compatible list: {exc}")
    if not isinstance(desired, list):
        fail(f"{label} must be a list")
    return desired


def require_fields(item, fields, label, fail):
    if not isinstance(item, dict) or set(item) - fields:
        fail(f"Each {label} entry needs " +
             ("source, name, and optional ref only" if "name" in fields
              else "source and optional ref only"))


def validate_ref(ref, subject, fail):
    if ref is not None and (not isinstance(ref, str) or not REF.fullmatch(ref)
                            or ref.startswith("/") or ".." in ref.split("/")):
        fail(f"Invalid Git ref for {subject}: {ref!r}")


def reject_duplicate(key, seen, label, fail):
    if key in seen:
        fail(f"Duplicate {label}: {key}")
    seen.add(key)
