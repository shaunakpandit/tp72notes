import subprocess
from datetime import date
from pathlib import Path

TODO_HEADING = "## Todo"
VOICE_HEADING = "## Voice notes"


def section_end(lines: list[str], heading_index: int) -> int:
    """Index after the last non-blank line of the section starting at heading_index."""
    next_heading = next(
        (index for index in range(heading_index + 1, len(lines)) if lines[index].startswith(("# ", "## "))),
        len(lines),
    )
    return max(
        (index + 1 for index in range(heading_index, next_heading) if lines[index].strip()),
        default=heading_index + 1,
    )


def insert_into_section(lines: list[str], heading: str, new_lines: list[str], fallback_index: int) -> list[str]:
    if not new_lines:
        return lines
    if heading not in lines:
        padding = [""] if fallback_index > 0 and lines[fallback_index - 1].strip() else []
        trailing = [""] if fallback_index < len(lines) and lines[fallback_index].strip() else []
        return lines[:fallback_index] + padding + [heading] + new_lines + trailing + lines[fallback_index:]
    end = section_end(lines, lines.index(heading))
    return lines[:end] + new_lines + lines[end:]


def update_note(content: str | None, day: date, entries: list[tuple[str, str]], todos: list[str]) -> str:
    """entries are (HH:MM, transcript) pairs; anything already in the note is skipped."""
    lines = (content or f"# {day.isoformat()}\n\n{TODO_HEADING}\n").rstrip("\n").split("\n")
    existing = "\n".join(lines)
    todo_lines = [f"- [ ] {todo}" for todo in dict.fromkeys(todos) if f"- [ ] {todo}" not in lines]
    entry_lines = [
        line
        for time, text in entries
        if text not in existing
        for line in ("", f"### {time}", "", text)
    ]
    after_title = 1 if lines[0].startswith("# ") else 0
    lines = insert_into_section(lines, TODO_HEADING, todo_lines, after_title)
    lines = insert_into_section(lines, VOICE_HEADING, entry_lines, len(lines))
    return "\n".join(lines) + "\n"


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def pull(repo: Path) -> None:
    git(repo, "pull", "--rebase")


def commit_and_push(repo: Path, paths: list[Path], message: str) -> None:
    git(repo, "add", *map(str, paths))
    # The notes repo's pre-commit hook syncs new checkboxes into todo.md.
    git(repo, "commit", "-m", message)
    git(repo, "push")
