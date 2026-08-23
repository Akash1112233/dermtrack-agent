from pathlib import Path

from services.deepgram_service import DeepgramService


class FakeResponse:
    def __init__(self, payload=None, content=b"audio-bytes"):
        self._payload = payload or {}
        self.content = content

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeHttpClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.response


def test_deepgram_transcribes_audio_bytes():
    fake_client = FakeHttpClient(
        FakeResponse(
            payload={
                "results": {
                    "channels": [
                        {
                            "alternatives": [
                                {"transcript": "I have itching."}
                            ]
                        }
                    ]
                }
            }
        )
    )
    service = DeepgramService(
        api_key="test-key",
        client=fake_client,
    )

    transcript = service.transcribe_bytes(
        b"audio",
        content_type="audio/webm",
    )

    assert transcript == "I have itching."
    assert fake_client.calls[0][1]["params"]["model"] == "nova-3"
    assert fake_client.calls[0][1]["headers"]["Content-Type"] == (
        "audio/webm"
    )


def test_deepgram_transcribes_audio_file(tmp_path: Path):
    audio_path = tmp_path / "recording.wav"
    audio_path.write_bytes(b"audio")
    fake_client = FakeHttpClient(
        FakeResponse(
            payload={
                "results": {
                    "channels": [
                        {
                            "alternatives": [
                                {"transcript": "Mild redness."}
                            ]
                        }
                    ]
                }
            }
        )
    )
    service = DeepgramService(
        api_key="test-key",
        client=fake_client,
    )

    assert service.transcribe(audio_path) == "Mild redness."


def test_deepgram_synthesizes_audio():
    fake_client = FakeHttpClient(FakeResponse(content=b"mp3-bytes"))
    service = DeepgramService(
        api_key="test-key",
        tts_model="aura-2-thalia-en",
        client=fake_client,
    )

    audio = service.synthesize("Please contact a clinician.")

    assert audio == b"mp3-bytes"
    assert fake_client.calls[0][1]["params"]["model"] == (
        "aura-2-thalia-en"
    )
    assert fake_client.calls[0][1]["json"] == {
        "text": "Please contact a clinician."
    }
