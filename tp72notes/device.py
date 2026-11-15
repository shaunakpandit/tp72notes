import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

MODEL_NAME = "TP-7"


@dataclass(frozen=True)
class Recording:
    id: str
    path: Path
    recorded_at: datetime


def find_block_device() -> Path | None:
    return next(
        (
            Path("/dev") / model_file.parents[1].name
            for model_file in Path("/sys/block").glob("sd*/device/model")
            if model_file.read_text().strip() == MODEL_NAME
        ),
        None,
    )


def current_mount(device: Path) -> tuple[Path, Path] | None:
    # Mountpoints in /proc/mounts escape spaces as \040.
    return next(
        (
            (Path(fields[0]), Path(fields[1].replace("\\040", " ")))
            for fields in map(str.split, Path("/proc/mounts").read_text().splitlines())
            if fields[0].startswith(str(device))
        ),
        None,
    )


def mount(device: Path) -> tuple[Path, Path]:
    """Returns (mounted block device, mountpoint)."""
    if existing := current_mount(device):
        return existing
    # The TP-7 storage may be the whole disk or its first partition.
    target = next(candidate for candidate in (Path(f"{device}1"), device) if candidate.exists())
    output = subprocess.run(
        ["udisksctl", "mount", "--no-user-interaction", "-b", str(target)],
        check=True, capture_output=True, text=True,
    ).stdout
    return target, Path(re.search(r" at (.+?)\.?$", output.strip()).group(1))


def unmount(block: Path) -> None:
    subprocess.run(["udisksctl", "unmount", "--no-user-interaction", "-b", str(block)], check=False)


def matches(path: Path, patterns: tuple[str, ...]) -> bool:
    return any(path.full_match(pattern, case_sensitive=False) for pattern in patterns)


def list_recordings(root: Path, include: tuple[str, ...], exclude: tuple[str, ...]) -> list[Recording]:
    paths = sorted(
        path for path in root.rglob("*")
        if path.is_file()
        and matches(path.relative_to(root), include)
        and not matches(path.relative_to(root), exclude)
    )
    return [
        Recording(
            id=f"{path.relative_to(root)}:{path.stat().st_size}",
            path=path,
            recorded_at=datetime.fromtimestamp(path.stat().st_mtime),
        )
        for path in paths
    ]
