from database.schemas import ImageObservation
from services.triage_service import SafetyTriageService

def test_triage_returns_low_risk_without_red_flags():
    service = SafetyTriageService()

    result = service.evaluate(
        transcript="I have mild dryness on my cheek.",
        observations=[
            ImageObservation(
                feature="mild dryness",
                confidence=0.80,
                body_area="left cheek",
            )
        ],
    )

    assert result.risk_level == "low"
    assert result.red_flags == []
    assert result.needs_human_review is False

def test_triage_detects_urgent_red_flag():
    service = SafetyTriageService()

    result = service.evaluate(
        transcript="My face is rapidly swelling and I have difficulty breathing.",
        observations=[],
    )

    assert result.risk_level == "urgent"
    assert result.needs_human_review is True
    assert len(result.red_flags) >= 1

def test_triage_detects_red_flag_in_observation():
    service = SafetyTriageService()

    result = service.evaluate(
        transcript="The area is getting worse.",
        observations=[
            ImageObservation(
                feature="rapidly spreading swelling",
                confidence=0.90,
                body_area="face",
            )
        ],
    )

    assert result.risk_level == "urgent"
    assert result.needs_human_review is True

def test_triage_explanation_is_always_present():
    service = SafetyTriageService()

    result = service.evaluate(
        transcript="I have mild redness.",
        observations=[],
    )

    assert result.explanation.strip() != ""