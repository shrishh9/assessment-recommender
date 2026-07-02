"""Individual LangGraph nodes for the assessment recommender.

Each node has one responsibility and returns a structured result that the graph
can route to the next step.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from agent.prompts import (
    CLARIFICATION_PROMPT,
    COMPARISON_PROMPT,
    RECOMMENDATION_PROMPT,
    REFINEMENT_PROMPT,
    REFUSAL_PROMPT,
    build_prompt,
)


class LLMClient:
    """Small adapter for the Groq chat API."""

    def __init__(self) -> None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set")

        from groq import Groq

        self.client = Groq(api_key=api_key)

    def generate(self, prompt: str) -> str:
        """Generate a response with Groq using the provided prompt."""

        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=400,
        )
        return response.choices[0].message.content or ""


def _format_recommendations(assessments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert retrieved assessments into the API-friendly recommendation payload."""

    formatted = []
    for assessment in assessments:
        test_type = assessment.get("test_type") or assessment.get("keys", "")
        if isinstance(test_type, list):
            test_type = ", ".join(str(item) for item in test_type)
        formatted.append(
            {
                "name": assessment.get("name", ""),
                "url": assessment.get("url", ""),
                "test_type": test_type,
            }
        )
    return formatted


def clarification_node(state: Dict[str, Any], llm_client: Optional[LLMClient] = None) -> Dict[str, Any]:
    """Ask a short follow-up question when the planner says more context is required."""

    prompt = build_prompt(
        CLARIFICATION_PROMPT,
        state.get("conversation_history", []),
        state.get("planner_output", {}).get("extracted_context", {}),
    )
    if llm_client is None:
        llm_client = LLMClient()
    reply = llm_client.generate(prompt)

    return {
        "reply": reply.strip() or "Could you tell me the target role, seniority, and relevant skills?",
        "recommendations": [],
        "metadata": {
            "action": "Clarify",
            "planner_reason": state.get("planner_output", {}).get("reason"),
            "missing_information": state.get("planner_output", {}).get("missing_information", []),
        },
        "end_of_conversation": False,
    }


def recommendation_node(state: Dict[str, Any], llm_client: Optional[LLMClient] = None) -> Dict[str, Any]:
    """Recommend assessments using only the retrieved catalog evidence."""

    assessments = state.get("retrieved_assessments", [])
    prompt = build_prompt(
        RECOMMENDATION_PROMPT,
        state.get("conversation_history", []),
        state.get("planner_output", {}).get("extracted_context", {}),
        assessments,
    )
    if llm_client is None:
        llm_client = LLMClient()
    reply = llm_client.generate(prompt)

    return {
        "reply": reply.strip(),
        "recommendations": _format_recommendations(assessments),
        "metadata": {
            "action": "Recommend",
            "planner_reason": state.get("planner_output", {}).get("reason"),
            "retrieval_count": len(assessments),
        },
        "end_of_conversation": False,
    }


def comparison_node(state: Dict[str, Any], llm_client: Optional[LLMClient] = None) -> Dict[str, Any]:
    """Compare assessments using retrieved catalog evidence only."""

    assessments = state.get("retrieved_assessments", [])
    prompt = build_prompt(
        COMPARISON_PROMPT,
        state.get("conversation_history", []),
        state.get("planner_output", {}).get("extracted_context", {}),
        assessments,
    )
    if llm_client is None:
        llm_client = LLMClient()
    reply = llm_client.generate(prompt)

    return {
        "reply": reply.strip(),
        "recommendations": _format_recommendations(assessments),
        "metadata": {
            "action": "Compare",
            "planner_reason": state.get("planner_output", {}).get("reason"),
            "retrieval_count": len(assessments),
        },
        "end_of_conversation": False,
    }


def refinement_node(state: Dict[str, Any], llm_client: Optional[LLMClient] = None) -> Dict[str, Any]:
    """Refine prior recommendations when the user changes requirements."""

    assessments = state.get("retrieved_assessments", [])
    prompt = build_prompt(
        REFINEMENT_PROMPT,
        state.get("conversation_history", []),
        state.get("planner_output", {}).get("extracted_context", {}),
        assessments,
    )
    if llm_client is None:
        llm_client = LLMClient()
    reply = llm_client.generate(prompt)

    return {
        "reply": reply.strip(),
        "recommendations": _format_recommendations(assessments),
        "metadata": {
            "action": "Refine",
            "planner_reason": state.get("planner_output", {}).get("reason"),
            "retrieval_count": len(assessments),
        },
        "end_of_conversation": False,
    }


def refusal_node(state: Dict[str, Any], llm_client: Optional[LLMClient] = None) -> Dict[str, Any]:
    """Return a safe refusal for out-of-scope or prompt-injection requests."""

    prompt = build_prompt(
        REFUSAL_PROMPT,
        state.get("conversation_history", []),
        state.get("planner_output", {}).get("extracted_context", {}),
    )
    if llm_client is None:
        llm_client = LLMClient()
    reply = llm_client.generate(prompt)

    return {
        "reply": reply.strip() or "I can help with SHL assessment recommendations only.",
        "recommendations": [],
        "metadata": {
            "action": "Refuse",
            "planner_reason": state.get("planner_output", {}).get("reason"),
        },
        "end_of_conversation": True,
    }
