"""
File I/O utilities for reading, writing, and managing opencode config pairs.
"""
import json
import shutil
from pathlib import Path
from typing import Any

from opencode_configer.models import ConfigSet

OPENCODE_DIR = Path.home() / ".config" / "opencode"
ACTIVE_CONFIG = OPENCODE_DIR / "config.json"
ACTIVE_OH_MY = OPENCODE_DIR / "oh-my-opencode.json"


def _ensure_dir(path: Path) -> None:
    """
    Create directory and all parents if they don't exist.

    :param path: Directory path to create.
    :type path: Path
    :rtype: None
    """
    path.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path) -> dict[str, Any]:
    """
    Read a JSON file, returning an empty dict if the file doesn't exist.

    :param path: Path to the JSON file.
    :type path: Path
    :return: Parsed JSON content.
    :rtype: dict[str, Any]
    """
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    """
    Write data as formatted JSON to a file, creating parent directories as needed.

    :param path: Destination file path.
    :type path: Path
    :param data: Data to serialize.
    :type data: dict[str, Any]
    :rtype: None
    """
    _ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_active_opencode() -> dict[str, Any]:
    """
    Read the active opencode config.json.

    :return: Config contents, or empty dict if file is absent.
    :rtype: dict[str, Any]
    """
    return _read_json(ACTIVE_CONFIG)


def read_active_oh_my_opencode() -> dict[str, Any]:
    """
    Read the active oh-my-opencode.json.

    :return: Config contents, or empty dict if file is absent.
    :rtype: dict[str, Any]
    """
    return _read_json(ACTIVE_OH_MY)


def write_active_opencode(data: dict[str, Any]) -> None:
    """
    Overwrite the active opencode config.json.

    :param data: Config data to write.
    :type data: dict[str, Any]
    :rtype: None
    """
    _write_json(ACTIVE_CONFIG, data)


def write_active_oh_my_opencode(data: dict[str, Any]) -> None:
    """
    Overwrite the active oh-my-opencode.json.

    :param data: Config data to write.
    :type data: dict[str, Any]
    :rtype: None
    """
    _write_json(ACTIVE_OH_MY, data)


def list_sets() -> list[ConfigSet]:
    """
    List all named config sets stored under ~/.config/opencode/<name>/.

    Directories that are not named sets (i.e., don't contain at least one
    known config file) are excluded.

    :return: List of ConfigSet metadata objects.
    :rtype: list[ConfigSet]
    """
    _ensure_dir(OPENCODE_DIR)
    sets: list[ConfigSet] = []
    for child in sorted(OPENCODE_DIR.iterdir()):
        if not child.is_dir():
            continue
        has_opencode = (child / "config.json").exists()
        has_oh_my = (child / "oh-my-opencode.json").exists()
        if has_opencode or has_oh_my:
            sets.append(ConfigSet(name=child.name, has_opencode=has_opencode, has_oh_my_opencode=has_oh_my))
    return sets


def save_set(name: str, opencode_config: dict[str, Any], oh_my_config: dict[str, Any]) -> None:
    """
    Save a named config pair to ~/.config/opencode/<name>/.

    :param name: Set name (used as directory name).
    :type name: str
    :param opencode_config: opencode config.json data.
    :type opencode_config: dict[str, Any]
    :param oh_my_config: oh-my-opencode.json data.
    :type oh_my_config: dict[str, Any]
    :rtype: None
    :raises ValueError: If the name contains path separators.
    """
    if "/" in name or "\\" in name or name in (".", ".."):
        raise ValueError(f"Invalid set name: {name!r}")
    set_dir = OPENCODE_DIR / name
    _ensure_dir(set_dir)
    _write_json(set_dir / "config.json", opencode_config)
    _write_json(set_dir / "oh-my-opencode.json", oh_my_config)


def load_set(name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Load a named config pair from ~/.config/opencode/<name>/.

    :param name: Set name.
    :type name: str
    :return: Tuple of (opencode_config, oh_my_opencode_config).
    :rtype: tuple[dict[str, Any], dict[str, Any]]
    :raises FileNotFoundError: If the named set directory does not exist.
    """
    set_dir = OPENCODE_DIR / name
    if not set_dir.is_dir():
        raise FileNotFoundError(f"Config set '{name}' not found.")
    return _read_json(set_dir / "config.json"), _read_json(set_dir / "oh-my-opencode.json")


def apply_set(name: str) -> None:
    """
    Copy a named config set to the active config paths.

    :param name: Set name to apply.
    :type name: str
    :rtype: None
    :raises FileNotFoundError: If the named set directory does not exist.
    """
    set_dir = OPENCODE_DIR / name
    if not set_dir.is_dir():
        raise FileNotFoundError(f"Config set '{name}' not found.")
    _ensure_dir(OPENCODE_DIR)
    src_config = set_dir / "config.json"
    src_oh_my = set_dir / "oh-my-opencode.json"
    if src_config.exists():
        shutil.copy2(src_config, ACTIVE_CONFIG)
    if src_oh_my.exists():
        shutil.copy2(src_oh_my, ACTIVE_OH_MY)


def delete_set(name: str) -> None:
    """
    Delete a named config set directory.

    :param name: Set name to delete.
    :type name: str
    :rtype: None
    :raises FileNotFoundError: If the set does not exist.
    """
    set_dir = OPENCODE_DIR / name
    if not set_dir.is_dir():
        raise FileNotFoundError(f"Config set '{name}' not found.")
    shutil.rmtree(set_dir)
