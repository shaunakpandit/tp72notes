import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

from tp72notes import state
from tp72notes.classify import Verdict, by_speech_ratio
from tp72notes.config import Config
from tp72notes.device import list_local, make_recordings, parse_tree
from tp72notes.notes import update_note
from tp72notes.todos import extract_todos

EXISTING = """# 2026-11-06

## Todo


## Glance configuration

I want glance reconfigured
"""


class TodoTest(unittest.TestCase):
    def test_extracts_todo_sentences(self):
        text = "Had a good day. Todo, buy milk. To do: call mum! Nothing else. todo fix the bike"
        self.assertEqual(extract_todos(text), ["buy milk", "call mum", "fix the bike"])

    def test_ignores_todo_mid_sentence(self):
        self.assertEqual(extract_todos("I have a lot todo today. Toddler is fine."), [])


class NoteTest(unittest.TestCase):
    def test_creates_new_note(self):
        result = update_note(None, date(2026, 11, 14), [("09:30", "Todo buy milk.")], ["buy milk"])
        self.assertEqual(result, "# 2026-11-14\n\n## Todo\n- [ ] buy milk\n\n## Voice notes\n\n### 09:30\n\nTodo buy milk.\n")

    def test_inserts_into_existing_note(self):
        result = update_note(EXISTING, date(2026, 11, 6), [("10:00", "Some thought.")], ["call mum"])
        self.assertEqual(
            result,
            "# 2026-11-06\n\n## Todo\n- [ ] call mum\n\n\n## Glance configuration\n\nI want glance reconfigured\n"
            "\n## Voice notes\n\n### 10:00\n\nSome thought.\n",
        )

    def test_appends_to_existing_voice_section_and_is_idempotent(self):
        first = update_note(None, date(2026, 11, 14), [("09:30", "First.")], [])
        second = update_note(first, date(2026, 11, 14), [("09:30", "First."), ("12:00", "Second.")], [])
        self.assertTrue(second.endswith("### 09:30\n\nFirst.\n\n### 12:00\n\nSecond.\n"))
        self.assertEqual(update_note(second, date(2026, 11, 14), [("12:00", "Second.")], []), second)

    def test_adds_todo_heading_after_title_when_missing(self):
        result = update_note("# 2026-11-01\n\nprose\n", date(2026, 11, 1), [], ["x"])
        self.assertEqual(result, "# 2026-11-01\n\n## Todo\n- [ ] x\n\nprose\n")


class ClassifyTest(unittest.TestCase):
    def test_thresholds(self):
        config = Config()
        self.assertEqual(by_speech_ratio(0.05, config), Verdict.MUSIC)
        self.assertEqual(by_speech_ratio(0.3, config), Verdict.BORDERLINE)
        self.assertEqual(by_speech_ratio(0.8, config), Verdict.SPEECH)


class FilesTest(unittest.TestCase):
    def test_state_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested/state.json"
            self.assertEqual(state.load(path), {})
            state.save(path, {"a": {"verdict": "music"}})
            self.assertEqual(state.load(path), {"a": {"verdict": "music"}})

    def test_lists_local_recordings_with_globs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("memo.WAV", "tracks/song.wav", "notes/a.wav", "readme.txt"):
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_bytes(b"1234")
            recordings = list_local(root, ("**/*.wav",), ("tracks/**",))
            self.assertEqual([recording.id for recording in recordings], ["memo.WAV", "notes/a.wav"])


TREE = """Device 0 (VID=2367 and PID=0019) is a Teenage engineering TP-7.
Attempting to connect device(s)
Device: (NULL)
Storage: TP-7 MTP Device
1 recordings
  2 1980-01-01_000000_000.wav
  3 2026-11-14_190821_000.wav
11 library
OK.
"""


class MtpTest(unittest.TestCase):
    def test_parses_filetree(self):
        self.assertEqual(
            parse_tree(TREE),
            {"recordings": 1, "recordings/1980-01-01_000000_000.wav": 2, "recordings/2026-11-14_190821_000.wav": 3, "library": 11},
        )

    def test_dates_from_filename_with_unset_clock_fallback(self):
        recordings = make_recordings(parse_tree(TREE), ("**/*.wav",), ())
        self.assertEqual([recording.source for recording in recordings], [2, 3])
        self.assertTrue(recordings[0].clock_unset)
        self.assertEqual(recordings[0].recorded_at.date(), datetime.now().date())
        self.assertEqual((recordings[1].recorded_at, recordings[1].clock_unset), (datetime(2026, 11, 14, 19, 8, 21), False))


if __name__ == "__main__":
    unittest.main()
