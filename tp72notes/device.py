import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

TREE_LINE = re.compile(r"^( *)(\d+) (.+)$")
FILENAME_TIME = re.compile(r"(\d{4}-\d{2}-\d{2}_\d{6})")
UNSET_CLOCK_YEAR = 1980


@dataclass(frozen=True)
class Recording:
    # shortcut: id is the device path, so a reused filename (possible while the clock is unset) is seen as done; add file size from mtp-files if that happens.
    id: str
    source: int | Path  # MTP object id, or a local file with --device-path
    recorded_at: datetime
    clock_unset: bool = False


def recorded_at(name: str, now: datetime) -> tuple[datetime, bool]:
    """TP-7 names files YYYY-MM-DD_HHMMSS_NNN; an unset clock shows as 1980, so those fall back to now."""
    match = FILENAME_TIME.search(name)
    parsed = datetime.strptime(match.group(1), "%Y-%m-%d_%H%M%S") if match else None
    return (parsed, False) if parsed and parsed.year > UNSET_CLOCK_YEAR else (now, True)


def parse_tree(output: str) -> dict[str, int]:
    """mtp-filetree prints `<id> <name>` indented two spaces per level; returns relative path -> id."""
    paths, stack = {}, []
    for indent, object_id, name in (match.groups() for match in map(TREE_LINE.match, output.splitlines()) if match):
        stack = stack[: len(indent) // 2] + [name]
        paths["/".join(stack)] = int(object_id)
    return paths


def matches(path: str, patterns: tuple[str, ...]) -> bool:
    return any(Path(path).full_match(pattern, case_sensitive=False) for pattern in patterns)


def make_recordings(paths: dict[str, int | Path], include: tuple[str, ...], exclude: tuple[str, ...]) -> list[Recording]:
    now = datetime.now()
    return [
        Recording(path, source, *recorded_at(Path(path).name, now))
        for path, source in sorted(paths.items())
        if matches(path, include) and not matches(path, exclude)
    ]


def list_mtp(include: tuple[str, ...], exclude: tuple[str, ...]) -> list[Recording]:
    output = subprocess.run(["mtp-filetree"], capture_output=True, text=True).stdout
    # libmtp tools exit 0 even when they can't open the device.
    if "Storage:" not in output:
        raise SystemExit("TP-7 not found, or not in file transfer mode")
    return make_recordings(parse_tree(output), include, exclude)


def list_local(root: Path, include: tuple[str, ...], exclude: tuple[str, ...]) -> list[Recording]:
    paths = {str(path.relative_to(root)): path for path in root.rglob("*") if path.is_file()}
    return make_recordings(paths, include, exclude)


def fetch(recording: Recording, target: Path) -> None:
    if isinstance(recording.source, Path):
        shutil.copy2(recording.source, target)
        return
    result = subprocess.run(["mtp-getfile", str(recording.source), str(target)], capture_output=True, text=True)
    if not target.exists():
        raise RuntimeError(f"mtp-getfile failed for {recording.id}:\n{result.stdout}{result.stderr}")
