from dataclasses import dataclass
from functools import cache
from pathlib import Path

from .classify import Verdict, by_speech_ratio, by_transcript
from .config import Config


@dataclass(frozen=True)
class Result:
    verdict: Verdict
    speech_ratio: float
    text: str = ""


@cache
def load_model(name: str):
    from faster_whisper import WhisperModel

    return WhisperModel(name, device="cpu", compute_type="int8")


def transcribe(path: Path, config: Config, force: bool = False) -> Result:
    # VAD runs before the segment generator is consumed, so music is rejected without decoding it.
    segments, info = load_model(config.model).transcribe(str(path), language=config.language, vad_filter=True)
    ratio = info.duration_after_vad / info.duration if info.duration else 0.0
    verdict = Verdict.SPEECH if force else by_speech_ratio(ratio, config)
    if verdict is Verdict.MUSIC:
        return Result(verdict, ratio)
    text = " ".join(segment.text.strip() for segment in segments).strip()
    if verdict is Verdict.BORDERLINE:
        verdict = by_transcript(text, config)
    return Result(verdict, ratio, text if verdict is Verdict.SPEECH else "")
