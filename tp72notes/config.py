import tomllib
from dataclasses import dataclass, replace
from pathlib import Path

CONFIG_PATH = Path.home() / ".config/tp72notes/config.toml"


@dataclass(frozen=True)
class Config:
    notes_repo: Path = Path.home() / "notes"
    daily_dir: str = "daily"
    model: str = "small"
    language: str | None = "en"
    include: tuple[str, ...] = ("**/*.wav",)
    exclude: tuple[str, ...] = ()
    speech_ratio_threshold: float = 0.3
    borderline_margin: float = 0.1
    state_path: Path = Path.home() / ".local/state/tp72notes/processed.json"
    cache_dir: Path = Path.home() / ".cache/tp72notes"
    openrouter_key_file: Path | None = None
    openrouter_model: str = "meta-llama/llama-3.1-8b-instruct"


PATH_FIELDS = {"notes_repo", "state_path", "cache_dir", "openrouter_key_file"}
TUPLE_FIELDS = {"include", "exclude"}


def coerce(key: str, value):
    if key in PATH_FIELDS:
        return Path(value).expanduser()
    if key in TUPLE_FIELDS:
        return tuple(value)
    return value


def load(path: Path = CONFIG_PATH) -> Config:
    if not path.exists():
        return Config()
    data = tomllib.loads(path.read_text())
    return replace(Config(), **{key: coerce(key, value) for key, value in data.items()})
