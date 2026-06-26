#!/usr/bin/env python3
"""Install traffic-light hooks without removing existing Claude Code settings."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
EXAMPLE_PATH = PROJECT_ROOT / "claude-hooks.example.json"
SCRIPT_MARKER = str(PROJECT_ROOT / "scripts" / "claude_traffic_light.py")
PROJECT_ROOT_PLACEHOLDER = "__PROJECT_ROOT__"


def is_traffic_light_group(group: object) -> bool:
    """Return whether a hook group belongs to this project."""
    if not isinstance(group, dict):
        return False

    hooks = group.get("hooks")
    if not isinstance(hooks, list):
        return False

    return any(
        isinstance(hook, dict) and SCRIPT_MARKER in str(hook.get("command", ""))
        for hook in hooks
    )


def replace_project_root(value: object) -> object:
    """Replace template placeholders with this checkout's absolute path."""
    if isinstance(value, str):
        return value.replace(PROJECT_ROOT_PLACEHOLDER, str(PROJECT_ROOT))
    if isinstance(value, list):
        return [replace_project_root(item) for item in value]
    if isinstance(value, dict):
        return {key: replace_project_root(item) for key, item in value.items()}
    return value


def main() -> None:
    """Merge the example hooks into the user's Claude Code settings."""
    settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    example = replace_project_root(json.loads(EXAMPLE_PATH.read_text(encoding="utf-8")))

    installed_hooks = settings.setdefault("hooks", {})
    for event, new_groups in example["hooks"].items():
        existing_groups = installed_hooks.setdefault(event, [])
        installed_hooks[event] = [
            group for group in existing_groups if not is_traffic_light_group(group)
        ] + new_groups

    backup_path = SETTINGS_PATH.with_suffix(".json.traffic-light-backup")
    backup_path.write_text(
        SETTINGS_PATH.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    SETTINGS_PATH.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Installed Claude traffic-light hooks in {SETTINGS_PATH}")
    print(f"Backup written to {backup_path}")


if __name__ == "__main__":
    main()
