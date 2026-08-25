from database.schemas import ImageObservation, PatientIntake
from agents.nodes.web_researcher import build_safe_research_query, web_research_node


class Result:
    title = "Trusted guidance"
    url = "https://aad.org/guidance"
    score = 0.8


class FakeTavily:
    def __init__(self):
        self.query = None

    def search(self, query):
        self.query = query
        return [Result()]


def test_web_research_builds_query_without_patient_identifiers():
    state = {
        "patient_id": "patient-secret-123",
        "transcript": "Akash email@example.com has symptoms",
        "patient_intake": PatientIntake(
            symptom_duration="1-7 days",
            affected_area="Arms or hands",
        ),
        "image_observations": [ImageObservation(feature="redness", confidence=0.8)],
    }

    query = build_safe_research_query(state)

    assert "patient-secret-123" not in query
    assert "email@example.com" not in query
    assert "1-7 days" in query
    assert "redness" in query


def test_web_research_skips_when_local_sources_exist_in_auto_mode():
    tavily = FakeTavily()
    state = {"research_mode": "auto", "retrieved_sources": ["local"]}

    result = web_research_node(state, tavily)

    assert result == state
    assert tavily.query is None


def test_web_research_returns_cited_sources_when_local_is_empty():
    tavily = FakeTavily()
    state = {
        "research_mode": "local_plus_web",
        "patient_intake": PatientIntake(affected_area="Face"),
        "retrieved_sources": [],
    }

    result = web_research_node(state, tavily)

    assert str(result["web_retrieved_sources"][0].url) == "https://aad.org/guidance"
    assert tavily.query is not None
