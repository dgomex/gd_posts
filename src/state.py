"""Pydantic models that flow through the LangGraph workflow."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class JudgeFeedback(BaseModel):
    """Structured response returned by the judge LLM."""

    approved: bool = Field(
        description="True only if the post is publication-ready as-is."
    )
    score: int = Field(
        ge=0, le=10,
        description="Overall quality score from 0 (unusable) to 10 (excellent).",
    )
    feedback: str = Field(
        description=(
            "Specific, actionable feedback for the writer. "
            "If approved, briefly summarise the strengths instead."
        ),
    )


class PostState(BaseModel):
    """Shared state passed between LangGraph nodes."""

    source_content: str
    max_iterations: int = 3

    draft: str = ""
    iteration: int = 0
    feedback_history: list[JudgeFeedback] = Field(default_factory=list)
    last_judgement: Optional[JudgeFeedback] = None
    final_post: Optional[str] = None
