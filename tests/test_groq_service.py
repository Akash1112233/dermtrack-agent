from types import SimpleNamespace

from services.groq_service import GroqTranscriptionService

class FakeTranscriptions:
    def __init__(self):
        self.received_file = None
        self.received_model = None

    def create(self, file, model):
        self.received_file = file
        self.received_model = model

        return SimpleNamespace(
            text="  I have redness and itching on my cheek.  "
        )

class FakeAudio:
    def __init__(self):
        self.transcriptions = FakeTranscriptions()

class FakeGroqClient:
    def __init__(self):
        self.audio = FakeAudio()

def test_transcription_service_returns_clean_transcript(tmp_path):
    audio_path = tmp_path / "patient.wav"
    audio_path.write_bytes(b"fake audio bytes")

    fake_client = FakeGroqClient()

    service = GroqTranscriptionService(
        api_key="test-key",
        model="whisper-large-v3",
        client=fake_client,
    )

    transcript = service.transcribe(audio_path)

    assert transcript == "I have redness and itching on my cheek."
    assert fake_client.audio.transcriptions.received_model == (
        "whisper-large-v3"
    )

def test_transcription_service_sends_audio_bytes(tmp_path):
    audio_path = tmp_path / "patient.wav"
    audio_path.write_bytes(b"fake audio bytes")

    fake_client = FakeGroqClient()

    service = GroqTranscriptionService(
        api_key="test-key",
        model="whisper-large-v3",
        client=fake_client,
    )

    service.transcribe(audio_path)

    received_file = fake_client.audio.transcriptions.received_file

    assert received_file[0] == "patient.wav"
    assert received_file[1] == b"fake audio bytes"