import argparse
import difflib
import shutil
import subprocess
import sys
from itertools import groupby
from pathlib import Path

from . import device, notes, state
from .classify import Verdict
from .config import Config, load
from .todos import extract_todos
from .transcribe import transcribe


def notify(message: str) -> None:
    print(message)
    subprocess.run(["notify-send", "tp72notes", message], check=False, capture_output=True)


def cache_copy(recording: device.Recording, cache_dir: Path) -> Path:
    # Copy off the device first so unplugging mid-run doesn't break transcription.
    target = cache_dir / recording.id.replace("/", "_")
    if not target.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(recording.path, target)
    return target


def write_notes(config: Config, transcribed: list[tuple[device.Recording, str]], dry_run: bool) -> list[Path]:
    by_day = groupby(sorted(transcribed, key=lambda pair: pair[0].recorded_at), key=lambda pair: pair[0].recorded_at.date())
    changed = []
    for day, pairs in by_day:
        pairs = list(pairs)
        path = config.notes_repo / config.daily_dir / f"{day.isoformat()}.md"
        old = path.read_text() if path.exists() else None
        new = notes.update_note(
            old,
            day,
            [(recording.recorded_at.strftime("%H:%M"), text) for recording, text in pairs],
            [todo for _, text in pairs for todo in extract_todos(text)],
        )
        if new == old:
            continue
        if dry_run:
            sys.stdout.writelines(difflib.unified_diff((old or "").splitlines(True), new.splitlines(True), "a/" + path.name, "b/" + path.name))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(new)
        changed.append(path)
    return changed


def run(config: Config, device_path: Path | None, force: set[str], dry_run: bool) -> None:
    if not dry_run:
        notes.pull(config.notes_repo)
    mounted = None
    if device_path is None:
        block = device.find_block_device()
        if block is None:
            raise SystemExit("TP-7 not found")
        mounted, device_path = device.mount(block)
    try:
        processed = state.load(config.state_path)
        pending = [
            recording
            for recording in device.list_recordings(device_path, config.include, config.exclude)
            if recording.id not in processed or recording.id in force
        ]
        cached = [(recording, cache_copy(recording, config.cache_dir)) for recording in pending]
    finally:
        if mounted:
            device.unmount(mounted)

    results = [(recording, transcribe(path, config, force=recording.id in force)) for recording, path in cached]
    for recording, result in results:
        print(f"{result.verdict.value:6} {result.speech_ratio:.2f} {recording.id}")

    transcribed = [(recording, result.text) for recording, result in results if result.verdict is Verdict.SPEECH and result.text]
    changed = write_notes(config, transcribed, dry_run)
    if changed and not dry_run:
        notes.commit_and_push(
            config.notes_repo,
            changed,
            "voice notes: " + ", ".join(path.stem for path in changed),
        )
    if not dry_run:
        state.save(config.state_path, processed | {
            recording.id: {"verdict": result.verdict.value, "date": recording.recorded_at.date().isoformat()}
            for recording, result in results
        })
    skipped = [recording.id for recording, result in results if result.verdict is Verdict.MUSIC]
    notify(
        f"{len(transcribed)} transcribed, {len(skipped)} skipped as music"
        + (f" ({', '.join(skipped)})" if skipped else "")
        + (f"; updated {', '.join(path.stem for path in changed)}" if changed else "")
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="tp72notes", description="Transcribe TP-7 voice notes into daily notes.")
    parser.add_argument("--dry-run", action="store_true", help="print note diffs; don't write, commit or record state")
    parser.add_argument("--device-path", type=Path, help="read recordings from this directory instead of the TP-7")
    parser.add_argument("--force", action="append", default=[], metavar="ID", help="reprocess ID and treat it as speech")
    parser.add_argument("--config", type=Path, help="config file path")
    args = parser.parse_args()
    config = load(args.config) if args.config else load()
    try:
        run(config, args.device_path, set(args.force), args.dry_run)
    except Exception as error:
        notify(f"failed: {error}")
        raise


if __name__ == "__main__":
    main()
