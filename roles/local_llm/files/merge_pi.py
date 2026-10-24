#!/usr/bin/env python3
"""Merge macreset's Ollama model into Pi's user configuration."""

import json
import os
from pathlib import Path
import sys
import tempfile


def strip_jsonc(source):
    """Pi accepts comments and trailing commas in existing settings files."""
    source = source.lstrip("\ufeff")
    output = []
    index = 0
    quoted = False
    escaped = False
    while index < len(source):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""
        if quoted:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
            output.append(char)
        elif char == "/" and next_char == "/":
            index = source.find("\n", index)
            if index < 0:
                break
            output.append("\n")
        elif char == "/" and next_char == "*":
            end = source.find("*/", index + 2)
            if end < 0:
                raise ValueError("Unclosed JSON comment")
            output.append(" ")
            index = end + 1
        else:
            output.append(char)
        index += 1
    without_comments = "".join(output)
    output = []
    quoted = False
    escaped = False
    for index, char in enumerate(without_comments):
        if quoted:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
            output.append(char)
        elif char == "," and without_comments[index + 1 :].lstrip().startswith(("]", "}")):
            continue
        else:
            output.append(char)
    return "".join(output)


def read_json(path):
    if not path.exists():
        return {}
    data = json.loads(strip_jsonc(path.read_text()))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def write_if_changed(path, data):
    desired = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text() == desired:
        return False
    fd, staged = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as output:
            output.write(desired)
        os.chmod(staged, 0o600)
        os.replace(staged, path)
    finally:
        if os.path.exists(staged):
            os.unlink(staged)
    return True


def main():
    agent_dir, model_id, context_length, base_url = sys.argv[1:]
    agent_dir = Path(agent_dir)
    agent_dir.mkdir(parents=True, exist_ok=True)
    models_path = agent_dir / "models.json"
    settings_path = agent_dir / "settings.json"
    models = read_json(models_path)
    providers = models.setdefault("providers", {})
    if not isinstance(providers, dict):
        raise ValueError(f"{models_path}: providers must be an object")
    provider = providers.setdefault("ollama", {})
    if not isinstance(provider, dict):
        raise ValueError(f"{models_path}: ollama provider must be an object")
    provider.update(baseUrl=base_url, api="openai-completions", apiKey="ollama")
    existing_models = provider.setdefault("models", [])
    if not isinstance(existing_models, list):
        raise ValueError(f"{models_path}: ollama models must be an array")
    selected = next((item for item in existing_models if isinstance(item, dict) and item.get("id") == model_id), None)
    if selected is None:
        selected = {"id": model_id}
        existing_models.append(selected)
    selected["contextWindow"] = int(context_length)
    settings = read_json(settings_path)
    settings["defaultProvider"] = "ollama"
    settings["defaultModel"] = model_id
    changed = write_if_changed(models_path, models)
    changed = write_if_changed(settings_path, settings) or changed
    print(json.dumps({"changed": changed, "models": str(models_path), "settings": str(settings_path)}))


if __name__ == "__main__":
    main()
