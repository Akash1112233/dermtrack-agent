from pathlib import Path
from typing import Any

import httpx


class DeepgramService:
    """Speech-to-text and text-to-speech using Deepgram REST APIs."""

    LISTEN_URL = "https://api.deepgram.com/v1/listen"
    SPEAK_URL = "https://api.deepgram.com/v1/speak"

    def __init__(
        self,
        api_key: str,
        stt_model: str = "nova-3",
        tts_model: str = "aura-2-thalia-en",
        client: Any | None = None,
    ):
        self.api_key = api_key
        self.stt_model = stt_model
        self.tts_model = tts_model
        self.client = client or httpx.Client(timeout=120.0)

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Token {self.api_key}"}

    def transcribe(
        self,
        audio_path: str | Path,
        content_type: str = "audio/wav",
    ) -> str:
        """Transcribe an audio file with Deepgram."""
        path = Path(audio_path)

        if not path.is_file():
            raise FileNotFoundError(
                f"Audio file was not found: {path}"
            )

        return self.transcribe_bytes(
            audio_bytes=path.read_bytes(),
            content_type=content_type,
        )

    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        content_type: str = "audio/webm",
    ) -> str:
        """Transcribe raw browser-recorded audio bytes."""
        if not audio_bytes:
            raise ValueError("Audio data cannot be empty.")

        response = self.client.post(
            self.LISTEN_URL,
            params={
                "model": self.stt_model,
                "smart_format": "true",
                "punctuate": "true",
            },
            headers={
                **self._auth_headers,
                "Content-Type": content_type,
            },
            content=audio_bytes,
        )
        response.raise_for_status()

        payload = response.json()
        transcript = (
            payload.get("results", {})
            .get("channels", [{}])[0]
            .get("alternatives", [{}])[0]
            .get("transcript", "")
            .strip()
        )

        if not transcript:
            raise ValueError("Deepgram returned an empty transcript.")

        return transcript

    def synthesize(self, text: str) -> bytes:
        """Convert patient-facing text into MP3 audio bytes."""
        cleaned_text = text.strip()

        if not cleaned_text:
            raise ValueError("Text cannot be empty.")

        response = self.client.post(
            self.SPEAK_URL,
            params={
                "model": self.tts_model,
                "encoding": "mp3",
            },
            headers={
                **self._auth_headers,
                "Content-Type": "application/json",
            },
            json={"text": cleaned_text},
        )
        response.raise_for_status()

        if not response.content:
            raise ValueError("Deepgram returned empty audio.")

        return response.content
