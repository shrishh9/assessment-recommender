"""State definitions for the LangGraph agent.

The state is intentionally simple so the workflow can be easily tested and later
connected to the FastAPI chat endpoint.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """State carried through the LangGraph workflow."""

    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    planner_output: Optional[Dict[str, Any]] = None
    retrieved_assessments: List[Dict[str, Any]] = Field(default_factory=list)
    reply: str = ""
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    end_of_conversation: bool = False
    error: Optional[str] = None


class AgentResult(BaseModel):
    """Structured result returned by the agent workflow."""

    reply: str
    recommendations: List[Dict[str, Any]]
    end_of_conversation: bool
    metadata: Dict[str, Any] = Field(default_factory=dict)
