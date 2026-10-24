"""Ansible module to merge macreset's Ollama model into Pi configuration."""

import json
import os
from pathlib import Path
import tempfile
from ansible.module_utils.basic import AnsibleModule


def quoted_string_end(source, start):
    """Return the index just after a JSON string, including escaped quotes."""
    escaped = False
    for index in range(start + 1, len(source)):
        char = source[index]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            return index + 1
    return len(source)


def strip_jsonc(source):
    """Pi accepts comments and trailing commas in existing settings files."""
    source = source.lstrip("\ufeff")
    output = []
    index = 0
    while index < len(source):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""
        if char == '"':
            end = quoted_string_end(source, index)
            output.append(source[index:end])
            index = end
        elif char == "/" and next_char == "/":
            index = source.find("\n", index)
            if index < 0:
                break
            output.append("\n")
            index += 1
        elif char == "/" and next_char == "*":
            end = source.find("*/", index + 2)
            if end < 0:
                raise ValueError("Unclosed JSON comment")
            output.append(" ")
            index = end + 2
        else:
            output.append(char)
            index += 1
    without_comments = "".join(output)
    output = []
    index = 0
    while index < len(without_comments):
        char = without_comments[index]
        if char == '"':
            end = quoted_string_end(without_comments, index)
            output.append(without_comments[index:end])
            index = end
        elif char == "," and without_comments[index + 1 :].lstrip().startswith(("]", "}")):
            index += 1
        else:
            output.append(char)
            index += 1
    return "".join(output)


def read_json(path):
    if not path.exists():
        return {}
    data = json.loads(strip_jsonc(path.read_text()))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def write_if_changed(path, data, check_mode):
    desired = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text() == desired:
        return False
    if check_mode:
        return True
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


def merge(agent_dir, model_id, context_length, base_url, check_mode):
    agent_dir = Path(agent_dir)
    if not check_mode:
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
    models_changed = write_if_changed(models_path, models, check_mode)
    settings_changed = write_if_changed(settings_path, settings, check_mode)
    return models_changed or settings_changed


def main():
    module = AnsibleModule(
        argument_spec={
            "agent_dir": {"type": "path", "required": True},
            "model_id": {"type": "str", "required": True},
            "context_length": {"type": "int", "required": True},
            "base_url": {"type": "str", "required": True},
        },
        supports_check_mode=True,
    )
    try:
        changed = merge(check_mode=module.check_mode, **module.params)
    except (OSError, ValueError, TypeError) as error:
        module.fail_json(msg=str(error))
    module.exit_json(changed=changed)


if __name__ == "__main__":
    main()
