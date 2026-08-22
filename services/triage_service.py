from collections.abc import Sequence

from database.schemas import ImageObservation, TriageResult

class SafetyTriageService:
    """Classify safety risk without making a medical diagnosis."""

    RED_FLAG_PHRASES = (
        "difficulty breathing",
        "trouble breathing",
        "rapidly swelling",
        "rapidly spreading swelling",
        "rapid swelling",
        "severe swelling",
        "swelling of the face",
        "swelling of the lips",
        "swelling of the throat",
        "eye involvement",
        "vision changes",
        "severe pain",
        "high fever",
        "fainting",
        "unconscious",
    )

    def evaluate(
        self,
        transcript: str,
        observations: Sequence[ImageObservation],
    ) -> TriageResult:
        """Return a conservative safety classification."""
        observation_text = " ".join(
            observation.feature
            for observation in observations
        )

        combined_text = (
            f"{transcript} {observation_text}"
        ).lower()

        red_flags = [
            phrase
            for phrase in self.RED_FLAG_PHRASES
            if phrase in combined_text
        ]

        if red_flags:
            return TriageResult(
                risk_level="urgent",
                red_flags=red_flags,
                needs_human_review=True,
                explanation=(
                    "Potential warning signs were identified. "
                    "Human clinical review is recommended."
                ),
            )

        return TriageResult(
            risk_level="low",
            red_flags=[],
            needs_human_review=False,
            explanation=(
                "No configured urgent warning signs were identified. "
                "This result is not a diagnosis."
            ),
        )