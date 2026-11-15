# TP7 to notes 

## goal

- plug tp7 by teenage engineering into thoth via usb
- automatically transcribe all voices notes for current day into text. 
- add these to daily notes in notes repo (will need to pull down repo on this machine)
- keep track of ported days, backfill when needed (havent plugged in for a while)
- when translating, phrases starting with todo, should be flagged for vreating a potential checklist item for 
- commit changes and push to repo 
- if needed, openrouter api key can be given for tasks better suited by ai. these tasks shouod he runnable on cheap models or even a descision model. ideally speach to text can be done locally? this coild become expensive 


## usage

```sh
nix develop
python -m unittest                                   # tests
python -m tp72notes --dry-run --device-path ~/tp7    # preview against copied files
python -m tp72notes                                  # mount TP-7, transcribe, commit, push
```

Optional `~/.config/tp72notes/config.toml` (all keys optional):

```toml
notes_repo = "~/notes"
model = "small"                 # faster-whisper model
include = ["**/*.wav"]
exclude = []                    # e.g. a music folder on the TP-7
speech_ratio_threshold = 0.3    # below this (minus margin) = music
openrouter_key_file = "~/.config/tp72notes/openrouter-key"
```

NixOS: import `nixosModules.default` and set `services.tp72notes.enable = true;` to run on plug-in.
