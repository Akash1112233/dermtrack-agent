import base64
import json
import mimetypes
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from database.schemas import ImageObservation

class GeminiVisionService:
    """Generate non-diagnostic image observations with Gemini."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        model: Any | None = None,
    ):
        self.model = model or ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0,
        )

    def analyze_image(
        self,
        image_path: str | Path,
    ) -> list[ImageObservation]:
        """Analyze an image and return structured observations."""
        path = Path(image_path)

        if not path.is_file():
            raise FileNotFoundError(
                f"Image file was not found: {path}"
            )

        image_bytes = path.read_bytes()
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")

        mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"

        prompt = """
Analyze this skin image for non-diagnostic visual observations only.

Do not provide a diagnosis.
Do not recommend medication.
Do not identify a disease.
Use cautious language.

Return only a valid JSON array. Each item must contain:
- feature: short observation
- confidence: number between 0 and 1
- body_area: visible body area, or "unknown"

If no useful observation is possible, return [].
"""

        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": prompt,
                },
                {
                    "type": "image_url",
                    "image_url": (
                        f"data:{mime_type};base64,{encoded_image}"
                    ),
                },
            ]
        )

        response = self.model.invoke([message])
        response_text = self._extract_response_text(response)

        try:
            raw_observations = json.loads(response_text)
        except json.JSONDecodeError as error:
            raise ValueError(
                "Gemini did not return valid JSON."
            ) from error

        if not isinstance(raw_observations, list):
            raise ValueError(
                "Gemini response must be a JSON array."
            )

        try:
            return [
                ImageObservation.model_validate(item)
                for item in raw_observations
            ]
        except Exception as error:
            raise ValueError(
                "Gemini returned invalid observation data."
            ) from error

    @staticmethod
    def _extract_response_text(response: Any) -> str:
        """Extract text from a LangChain model response."""
        content = response.content

        if isinstance(content, str):
            return content.strip()

        raise ValueError(
            "Gemini returned an unsupported response format."
        )