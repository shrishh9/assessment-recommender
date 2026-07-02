"""Pydantic models for the API contract.

These models define the shape of the request and response payloads used by the
chat endpoint. The schema is intentionally simple so future agent logic can be
added without changing the public contract.
"""

from typing import List, Literal

from pydantic import AliasChoices, BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in the conversation history."""

    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    messages: List[ChatMessage] = Field(
        ...,
        validation_alias=AliasChoices("messages", "conversation_history"),
        min_length=1,
        max_length=8,
    )


class Recommendation(BaseModel):
    """A recommendation returned to the client."""

    name: str
    url: str
    test_type: str


class ChatResponse(BaseModel):
    """Response body for the chat endpoint."""

    reply: str
    recommendations: List[Recommendation]
    end_of_conversation: bool
