"""Formatting helpers for the assessment recommender API."""

from __future__ import annotations

from typing import Any, Dict, List


def format_recommendations(recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize recommendation payloads to the API response contract."""

    formatted: List[Dict[str, Any]] = []
    for recommendation in recommendations:
        if not isinstance(recommendation, dict):
            continue
        test_type = recommendation.get("test_type") or recommendation.get("keys", "")
        if isinstance(test_type, list):
            test_type = ", ".join(str(item) for item in test_type)
        formatted.append(
            {
                "name": str(recommendation.get("name", "")),
                "url": str(recommendation.get("url", "")),
                "test_type": str(test_type),
            }
        )
    return formatted
