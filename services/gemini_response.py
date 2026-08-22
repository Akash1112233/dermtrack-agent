from typing import Any
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from database.schemas import (
    ImageObservation,
    RetrievedSource,
    TriageResult,
)

class GeminiResponseService:
    """Generate safe, educational consultation responses."""
    
    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        model: Any | None = None,
    ):
        self.model = model or ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.2,
        )

    def generate(
        self,
        transcript: str,
        observations: list[ImageObservation],
        triage: TriageResult | None,
        sources: list[RetrievedSource],
    ) -> str:
        """Generate a cautious patient-facing response."""
        if not transcript.strip() and not observations:
            raise ValueError(
                "At least one piece of consultation data is required."
            )

        observation_text = "\n".join(
            (
                f"- {observation.feature} "
                f"(confidence: {observation.confidence:.2f}, "
                f"area: {observation.body_area})"
            )
            for observation in observations
        ) or "- No image observations available."

        source_text = "\n".join(
            (
                f"- {source.title} "
                f"(similarity: {source.similarity_score:.2f}, "
                f"url: {source.url})"
            )
            for source in sources
        ) or "- No retrieved sources available."

        triage_text = (
            triage.model_dump_json(indent=2)
            if triage is not None
            else "No triage result available."
        )

        prompt = f"""
        You are a cautious dermatology-support assistant. Generate educational information only. Do not diagnose a disease. Do not prescribe medication. Do not claim certainty from an image. Clearly recommend professional medical evaluation when appropriate. If the safety triage indicates urgent risk, clearly prioritize urgent professional or emergency care.

        Patient transcript: {transcript or "No transcript available."}
        Non-diagnostic image observations: {observation_text}
        Safety triage: {triage_text}
        Retrieved knowledge sources: {source_text}

        Write a concise, empathetic response for the patient.
        """

        response = self.model.invoke(
            [HumanMessage(content=prompt)]
        )
        
        # Cleaned up duplicate return statements and handled multimodal content parts
        raw_content = response.content
        if isinstance(raw_content, str):
            content = raw_content
        elif isinstance(raw_content, list):
            content_parts = []
            for part in raw_content:
                if isinstance(part, str):
                    content_parts.append(part)
                elif isinstance(part, dict):
                    text = part.get("text")
                    if isinstance(text, str):
                        content_parts.append(text)
            content = "\n".join(content_parts)
        else:
            content = ""

        if not content.strip():
            raise ValueError(
                "Gemini returned an empty response."
            )

        return content.strip()
