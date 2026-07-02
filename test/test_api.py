from fastapi.testclient import TestClient

from app.main import create_app
import app.routes as routes


def test_chat_endpoint_returns_agent_payload() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/chat",
        json={
            "conversation_history": [
                {"role": "user", "content": "I need a recommendation for a Java developer."}
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "reply" in payload
    assert "recommendations" in payload
    assert "end_of_conversation" in payload


def test_chat_endpoint_returns_empty_recommendations_for_clarification() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/chat",
        json={
            "conversation_history": [
                {"role": "user", "content": "I need assessments for a role."}
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["recommendations"] == []


def test_chat_endpoint_formats_recommendation_payload() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/chat",
        json={
            "conversation_history": [
                {"role": "user", "content": "I need a recommendation for a Python backend engineer."}
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    for recommendation in payload["recommendations"]:
        assert set(recommendation.keys()) >= {"name", "url", "test_type"}


def test_chat_endpoint_returns_safe_error_payload_when_flow_fails(monkeypatch) -> None:
    def broken_run(_conversation_history):
        raise RuntimeError("boom")

    monkeypatch.setattr(routes.flow, "run", broken_run)

    client = TestClient(create_app())
    response = client.post(
        "/chat",
        json={
            "conversation_history": [
                {"role": "user", "content": "I need a recommendation for a Java developer."}
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"]
    assert payload["recommendations"] == []
    assert payload["end_of_conversation"] is True
