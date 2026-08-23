from types import SimpleNamespace

import pytest

from services.gemini_vision import GeminiVisionService

class FakeVisionModel:
    def __init__(self, response_content):
        self.response_content = response_content
        self.received_messages = None

    def invoke(self, messages):
        self.received_messages = messages
        return SimpleNamespace(content=self.response_content)

def test_vision_service_returns_structured_observations(tmp_path):
    image_path = tmp_path / "skin.jpg"
    image_path.write_bytes(b"fake image bytes")

    fake_response = """
    [
        {
            "feature": "localized redness",
            "confidence": 0.84,
            "body_area": "left cheek"
        },
        {
            "feature": "mild dryness",
            "confidence": 0.71,
            "body_area": "left cheek"
        }
    ]
    """

    fake_model = FakeVisionModel(fake_response)

    service = GeminiVisionService(
        api_key="test-key",
        model_name="gemini-2.5-flash",
        model=fake_model,
    )

    observations = service.analyze_image(image_path)

    assert len(observations) == 2
    assert observations[0].feature == "localized redness"
    assert observations[0].confidence == 0.84
    assert observations[1].body_area == "left cheek"
    assert fake_model.received_messages is not None

def test_vision_service_rejects_invalid_response(tmp_path):
    image_path = tmp_path / "skin.jpg"
    image_path.write_bytes(b"fake image bytes")

    fake_model = FakeVisionModel("This is not valid JSON.")

    service = GeminiVisionService(
        api_key="test-key",
        model_name="gemini-2.5-flash",
        model=fake_model,
    )

    with pytest.raises(ValueError, match="valid JSON"):
        service.analyze_image(image_path)


def test_vision_service_accepts_fenced_json(tmp_path):
    image_path = tmp_path / "skin.png"
    image_path.write_bytes(b"fake image bytes")
    fake_model = FakeVisionModel(
        '```json\n[{"feature":"redness","confidence":0.8,"body_area":"arm"}]\n```'
    )

    service = GeminiVisionService(api_key="test-key", model=fake_model)

    observations = service.analyze_image(image_path)

    assert observations[0].feature == "redness"
