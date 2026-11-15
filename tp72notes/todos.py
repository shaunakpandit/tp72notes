import re

SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")
TODO = re.compile(r"^\s*(?:todo|to do|to-do)\b[\s,:.\-]*(.+?)[\s.!?]*$", re.IGNORECASE)


def extract_todos(text: str) -> list[str]:
    return [
        match.group(1)
        for match in map(TODO.match, SENTENCE_BOUNDARY.split(text))
        if match
    ]
