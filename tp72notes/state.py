import json
import os
from pathlib import Path


def load(path: Path) -> dict[str, dict]:
    return json.loads(path.read_text()) if path.exists() else {}


def save(path: Path, state: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True))
    os.replace(temporary, path)
