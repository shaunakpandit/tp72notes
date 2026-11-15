import json
import urllib.request
from pathlib import Path

URL = "https://openrouter.ai/api/v1/chat/completions"


def ask(key_file: Path, model: str, prompt: str) -> str:
    request = urllib.request.Request(
        URL,
        data=json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}]}).encode(),
        headers={
            "Authorization": f"Bearer {key_file.read_text().strip()}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)["choices"][0]["message"]["content"].strip()
