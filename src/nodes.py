"""LangGraph node factories: writer, judge, finalize, and the routing rule."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from .state import JudgeFeedback, PostState


def _read_prompt(prompts_dir: Path, name: str) -> str:
    return (prompts_dir / name).read_text(encoding="utf-8").strip()


def _coerce_to_text(content: Any) -> str:
    """Normalise a chat-model response into plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Some providers return a list of content parts.
        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                parts.append(str(part["text"]))
        return "".join(parts)
    return str(content)


def make_writer_node(
    llm: BaseChatModel, prompts_dir: Path
) -> Callable[[PostState], dict]:
    """Return a node that produces the next draft of the post."""
    system_prompt = _read_prompt(prompts_dir, "writer.txt")

    def writer_node(state: PostState) -> dict:
        if state.feedback_history:
            history_lines = [
                f"Round {i} feedback (score {fb.score}/10):\n{fb.feedback}"
                for i, fb in enumerate(state.feedback_history, start=1)
            ]
            feedback_block = "\n\n".join(history_lines)
        else:
            feedback_block = "(no prior feedback — this is the first draft)"

        previous_draft = state.draft or "(no prior draft)"

        user_prompt = (
            f"## Source content\n{state.source_content}\n\n"
            f"## Previous draft\n{previous_draft}\n\n"
            f"## Reviewer feedback so far\n{feedback_block}\n\n"
            "Write the next version of the post in Markdown. "
            "Address every reviewer point and do not repeat past mistakes."
        )

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])

        return {
            "draft": _coerce_to_text(response.content).strip(),
            "iteration": state.iteration + 1,
        }

    return writer_node


def make_judge_node(
    llm: BaseChatModel, prompts_dir: Path
) -> Callable[[PostState], dict]:
    """Return a node that judges the current draft and returns structured feedback."""
    system_prompt = _read_prompt(prompts_dir, "judge.txt")
    structured_llm = llm.with_structured_output(JudgeFeedback)

    def judge_node(state: PostState) -> dict:
        user_prompt = (
            f"## Source content\n{state.source_content}\n\n"
            f"## Draft post (round {state.iteration})\n{state.draft}\n\n"
            "Judge whether this post is publication-ready. "
            "Respond with strict JSON matching the required schema."
        )

        feedback = structured_llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])

        # Some providers return a dict instead of the Pydantic model — normalise.
        if not isinstance(feedback, JudgeFeedback):
            feedback = JudgeFeedback.model_validate(feedback)

        return {
            "last_judgement": feedback,
            "feedback_history": state.feedback_history + [feedback],
        }

    return judge_node


def decide_next(state: PostState) -> str:
    """Conditional edge: approve, give up, or rewrite."""
    if state.last_judgement and state.last_judgement.approved:
        return "approve"
    if state.iteration >= state.max_iterations:
        return "give_up"
    return "rewrite"


def finalize_node(state: PostState) -> dict:
    """Mark the current draft as the final post."""
    return {"final_post": state.draft}
