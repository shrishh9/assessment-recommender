from agent.graph import AssessmentFlow


def test_agent_returns_structured_response() -> None:
    flow = AssessmentFlow()
    result = flow.run([
        {"role": "user", "content": "I need a recommendation for a Python backend engineer."}
    ])

    assert result.reply
    assert isinstance(result.recommendations, list)
    assert isinstance(result.end_of_conversation, bool)
    assert isinstance(result.metadata, dict)
