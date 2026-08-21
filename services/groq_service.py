from pathlib import Path
from typing import Any

from groq import Groq

class GroqTranscriptionService:
    """Transcribe patient audio using Groq Whisper."""

    def __init__(
        self,
        api_key: str,
        model: str = "whisper-large-v3",
        client: Any | None = None,
    ):
        self.model = model
        self.client = client or Groq(api_key=api_key)

    def transcribe(self, audio_path: str | Path) -> str:
        """Transcribe an audio file and return cleaned text."""
        path = Path(audio_path)

        if not path.is_file():
            raise FileNotFoundError(
                f"Audio file was not found: {path}"
            )

        audio_bytes = path.read_bytes()

        response = self.client.audio.transcriptions.create(
            file=(path.name, audio_bytes),
            model=self.model,
        )

        transcript = response.text.strip()

        if not transcript:
            raise ValueError("Groq returned an empty transcript.")

        return transcript