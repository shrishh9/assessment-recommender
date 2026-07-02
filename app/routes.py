"""API route handlers for the assessment recommender service."""

from __future__ import annotations

from pathlib import Path
import sys

from fastapi import APIRouter

from app.schemas import ChatRequest, ChatResponse, Recommendation
from utils.formatter import format_recommendations

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent.graph import AssessmentFlow

router = APIRouter()
flow = AssessmentFlow()


def _to_chat_response(result) -> ChatResponse:
    """Convert an agent result into the public API response contract."""

    action = str(result.metadata.get("action", "")).strip().lower()
    recommendations = []
    if action not in {"clarify", "refuse"}:
        recommendations = [
            Recommendation(**recommendation)
            for recommendation in format_recommendations(result.recommendations)[:10]
        ]

    return ChatResponse(
        reply=result.reply,
        recommendations=recommendations,
        end_of_conversation=result.end_of_conversation,
    )


@router.get("/health")
def health() -> dict[str, str]:
    """Simple health check endpoint for monitoring and deployment."""

    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Route a conversation turn through the assessment recommender flow."""

    try:
        result = flow.run([message.model_dump() for message in request.messages])
    except Exception:
        return ChatResponse(
            reply="I'm sorry, I couldn't process your request right now. Please try again.",
            recommendations=[],
            end_of_conversation=True,
        )

    return _to_chat_response(result)
