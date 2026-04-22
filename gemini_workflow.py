"""Gemini: Deep Research (interactions agent), blog writer, structured JSON judge."""

from __future__ import annotations

import json
import time
import warnings
from typing import Any

from google.genai import Client, types
from pydantic import BaseModel, Field


class JudgeScores(BaseModel):
    """Explicit numeric fields; a dict type caused Gemini to emit an unsupported JSON schema."""

    seo: float = Field(description="0–10 SEO quality.")
    content: float = Field(description="0–10 editorial/content quality.")
    readiness: float = Field(description="0–10 publish readiness.")


class JudgeVerdict(BaseModel):
    approved: bool
    feedback: str = Field(default="", description="Actionable edits or brief confirmation.")
    scores: JudgeScores = Field(description="Numeric rubric; always include all three fields.")


def _suppress_interactions_warning() -> None:
    warnings.filterwarnings(
        "ignore",
        message="Interactions usage is experimental.*",
        category=UserWarning,
    )


def _text_from_interaction_outputs(interaction: Any) -> str:
    chunks: list[str] = []
    for item in interaction.outputs or []:
        if getattr(item, "type", None) == "text":
            chunks.append(getattr(item, "text", "") or "")
    return "\n\n".join(c for c in chunks if c).strip()


def run_deep_research(
    client: Client,
    *,
    topic: str,
    skill_body: str,
    agent: str,
    background: bool = True,
    poll_interval_s: float = 10.0,
    max_wait_s: float = 1800.0,
) -> str:
    """Start Deep Research interaction and poll until completed or failed.

    Deep Research agents (e.g. deep-research-pro-preview-12-2025) do not accept
    system_instruction on the Interactions API; the skill text is prepended to
    input instead, per Google API guidance.
    """
    _suppress_interactions_warning()
    print(
        f"[gemini] Deep Research: creating interaction (agent={agent!r}, "
        f"background={background}, poll_every={poll_interval_s}s, max_wait={max_wait_s}s).",
        flush=True,
    )
    user_input = (
        "## Instructions (from project skill — follow closely)\n\n"
        f"{skill_body.strip()}\n\n"
        "---\n\n"
        "## Research topic\n\n"
        f"{topic.strip()}\n"
    )
    print(
        f"[gemini] Deep Research: skill inlined in input (no system_instruction); "
        f"input_chars={len(user_input)}.",
        flush=True,
    )
    created = client.interactions.create(
        agent=agent,
        input=user_input,
        background=background,
        stream=False,
    )
    interaction_id = created.id
    print(f"[gemini] Deep Research: interaction created id={interaction_id!r}.", flush=True)
    deadline = time.monotonic() + max_wait_s
    last: Any = None
    poll_n = 0
    prev_status: str | None = None
    while time.monotonic() < deadline:
        poll_n += 1
        last = client.interactions.get(interaction_id, stream=False)
        status = last.status
        elapsed = time.monotonic() - (deadline - max_wait_s)
        if status != prev_status or poll_n == 1 or poll_n % 5 == 0:
            print(
                f"[gemini] Deep Research: poll #{poll_n} status={status!r} "
                f"elapsed={elapsed:.0f}s id={interaction_id!r}",
                flush=True,
            )
        prev_status = status
        if status == "completed":
            text = _text_from_interaction_outputs(last)
            if not text:
                raise RuntimeError("Deep Research completed but returned no text outputs.")
            print(
                f"[gemini] Deep Research: completed, output_chars={len(text)} "
                f"(outputs_items={len(last.outputs or [])}).",
                flush=True,
            )
            return text
        if status in ("failed", "cancelled", "incomplete"):
            print(f"[gemini] Deep Research: terminal status={status!r} (failing).", flush=True)
            raise RuntimeError(f"Deep Research ended with status={status!r}.")
        time.sleep(poll_interval_s)

    print(
        f"[gemini] Deep Research: timed out after {max_wait_s:.0f}s "
        f"(last_status={getattr(last, 'status', None)!r}).",
        flush=True,
    )
    raise TimeoutError(
        f"Deep Research timed out after {max_wait_s:.0f}s (last_status={getattr(last, 'status', None)!r})."
    )


def write_blog_post(
    client: Client,
    *,
    model: str,
    blog_skill_body: str,
    topic: str,
    research: str,
    previous_draft: str | None,
    judge_feedback: str | None,
) -> str:
    parts: list[str] = [
        f"Topic:\n{topic.strip()}\n\nDeep research report:\n{research.strip()}",
    ]
    if previous_draft:
        parts.append(f"Previous draft:\n{previous_draft.strip()}")
    if judge_feedback:
        parts.append(f"Judge feedback (address every point):\n{judge_feedback.strip()}")

    user_message = "\n\n".join(parts)
    print(
        f"[gemini] Blog writer: calling generate_content model={model!r} "
        f"user_chars={len(user_message)} "
        f"has_previous_draft={bool(previous_draft)} has_judge_feedback={bool(judge_feedback)}.",
        flush=True,
    )
    resp = client.models.generate_content(
        model=model,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=blog_skill_body,
            temperature=0.7,
        ),
    )
    text = (resp.text or "").strip()
    if not text:
        print("[gemini] Blog writer: empty response text (error).", flush=True)
        raise RuntimeError("Blog writer returned empty content.")
    print(f"[gemini] Blog writer: done, draft_chars={len(text)}.", flush=True)
    return text


def judge_blog_post(
    client: Client,
    *,
    model: str,
    judge_skill_body: str,
    topic: str,
    research_excerpt: str,
    post_markdown: str,
) -> JudgeVerdict:
    """Returns structured verdict; uses JSON schema when supported."""
    user_message = (
        f"Topic:\n{topic.strip()}\n\n"
        f"Research excerpt (for grounding checks):\n{research_excerpt.strip()}\n\n"
        f"Blog post markdown:\n{post_markdown.strip()}"
    )
    print(
        f"[gemini] Judge: calling generate_content model={model!r} "
        f"user_chars={len(user_message)} post_chars={len(post_markdown.strip())}.",
        flush=True,
    )
    resp = client.models.generate_content(
        model=model,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=judge_skill_body,
            temperature=0.2,
            response_mime_type="application/json",
            response_schema=JudgeVerdict,
        ),
    )
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, JudgeVerdict):
        print(
            f"[gemini] Judge: verdict approved={parsed.approved} "
            f"scores={parsed.scores!r} feedback_len={len(parsed.feedback)} (parsed object).",
            flush=True,
        )
        return parsed
    raw = (resp.text or "").strip()
    if not raw:
        print("[gemini] Judge: empty response (error).", flush=True)
        raise RuntimeError("Judge returned empty content.")
    try:
        data: Any = json.loads(raw)
        v = JudgeVerdict.model_validate(data)
        print(
            f"[gemini] Judge: verdict approved={v.approved} scores={v.scores!r} "
            f"feedback_len={len(v.feedback)} (JSON text).",
            flush=True,
        )
        return v
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"[gemini] Judge: failed to parse JSON, raw_prefix={raw[:200]!r}", flush=True)
        raise RuntimeError(f"Judge output was not valid JSON: {raw[:500]!r}") from exc


def research_excerpt(research: str, max_chars: int = 6000) -> str:
    r = research.strip()
    if len(r) <= max_chars:
        return r
    return r[: max_chars - 20] + "\n\n[truncated]"
