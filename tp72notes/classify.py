from enum import Enum

from . import openrouter
from .config import Config


class Verdict(Enum):
    SPEECH = "speech"
    MUSIC = "music"
    BORDERLINE = "borderline"


def by_speech_ratio(ratio: float, config: Config) -> Verdict:
    if ratio < config.speech_ratio_threshold - config.borderline_margin:
        return Verdict.MUSIC
    if ratio < config.speech_ratio_threshold + config.borderline_margin:
        return Verdict.BORDERLINE
    return Verdict.SPEECH


def by_transcript(transcript: str, config: Config) -> Verdict:
    """Resolves borderline cases with a cheap model if a key is configured, otherwise treats them as music."""
    if not (config.openrouter_key_file and config.openrouter_key_file.exists()):
        return Verdict.MUSIC
    answer = openrouter.ask(
        config.openrouter_key_file,
        config.openrouter_model,
        "This transcript came from a pocket recorder used for both voice memos and music. "
        "Reply with exactly one word: NOTE if it is a spoken voice memo, MUSIC if it is song lyrics, "
        f"instruments or noise.\n\nTranscript:\n{transcript[:500]}",
    )
    return Verdict.SPEECH if answer.upper().startswith("NOTE") else Verdict.MUSIC
