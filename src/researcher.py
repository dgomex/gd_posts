"""Gemini Deep Research client + LangGraph node factory.

The Deep Research agent is accessed via the ``Interactions API`` of
``google-genai``. Tasks run for several minutes, so the agent is started in
the background and polled until it transitions to ``completed`` (or fails /
times out).

Reference: https://ai.google.dev/gemini-api/docs/deep-research
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional

from .config import ResearchConfig
from .state import PostState


_TERMINAL_FAILED_STATUSES = {"failed", "cancelled", "incomplete"}


class DeepResearcher:
    """Thin wrapper around ``google.genai.Client.interactions``.

    Starts a background research interaction and polls until completion,
    returning the concatenated text of all ``type=="text"`` outputs.
    """

    def __init__(self, config: ResearchConfig):
        self.config = config

        # The SDK falls back to GEMINI_API_KEY / GOOGLE_API_KEY automatically
        # when api_key is None, but we forward the value explicitly when set
        # so the user-provided RESEARCH__API_KEY wins over the global env.
        try:
            from google import genai
        except ImportError as exc:  # pragma: no cover - import-time guard
            raise ImportError(
                "google-genai is required for Deep Research. "
                "Install with: pip install 'google-genai>=1.55.0'"
            ) from exc

        api_key = config.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "No Gemini API key found. Set RESEARCH__API_KEY, GEMINI_API_KEY, "
                "or GOOGLE_API_KEY in the environment."
            )
        self._client = genai.Client(api_key=api_key)

    @staticmethod
    def _text_from_outputs(interaction: Any) -> str:
        """Concatenate every ``type == "text"`` output produced by the agent."""
        chunks: list[str] = []
        for item in getattr(interaction, "outputs", None) or []:
            if getattr(item, "type", None) == "text":
                text = getattr(item, "text", "") or ""
                if text:
                    chunks.append(text)
        return "\n\n".join(chunks).strip()

    def run(self, prompt: str, *, log: Callable[[str], None] = lambda _msg: None) -> str:
        """Run a Deep Research task and return its final text report.

        Args:
            prompt: The full user input (instructions + topic).
            log:    Optional logging callback for progress lines.

        Raises:
            RuntimeError: if the agent ends in a non-completed terminal state
                or completes with no text output.
            TimeoutError: if the task does not finish within ``max_wait_s``.
        """
        cfg = self.config
        log(
            f"[deep_research] starting agent={cfg.agent!r} "
            f"poll_interval={cfg.poll_interval_s}s max_wait={cfg.max_wait_s:.0f}s"
        )

        created = self._client.interactions.create(
            agent=cfg.agent,
            input=prompt,
            background=True,
            stream=False,
        )
        interaction_id = created.id
        log(f"[deep_research] interaction id={interaction_id!r}")

        deadline = time.monotonic() + cfg.max_wait_s
        last: Any = None
        prev_status: Optional[str] = None
        poll_n = 0

        while time.monotonic() < deadline:
            poll_n += 1
            last = self._client.interactions.get(interaction_id)
            status = getattr(last, "status", None)
            if status != prev_status or poll_n == 1 or poll_n % 6 == 0:
                log(f"[deep_research] poll #{poll_n} status={status!r}")
            prev_status = status

            if status == "completed":
                text = self._text_from_outputs(last)
                if not text:
                    raise RuntimeError(
                        "Deep Research completed but returned no text outputs."
                    )
                log(f"[deep_research] done output_chars={len(text)}")
                return text

            if status in _TERMINAL_FAILED_STATUSES:
                err = getattr(last, "error", None)
                raise RuntimeError(
                    f"Deep Research ended with status={status!r}"
                    + (f": {err}" if err else "")
                )

            time.sleep(cfg.poll_interval_s)

        raise TimeoutError(
            f"Deep Research timed out after {cfg.max_wait_s:.0f}s "
            f"(last_status={getattr(last, 'status', None)!r})."
        )


def _read_research_prompt(prompts_dir: Path) -> str:
    return (prompts_dir / "research.txt").read_text(encoding="utf-8").strip()


def make_researcher_node(
    researcher: DeepResearcher, prompts_dir: Path
) -> Callable[[PostState], dict]:
    """Return a LangGraph node that runs Deep Research on ``state.topic``."""
    instructions = _read_research_prompt(prompts_dir)

    def researcher_node(state: PostState) -> dict:
        topic = (state.topic or "").strip()
        if not topic:
            raise ValueError("PostState.topic is empty; nothing to research.")

        prompt = (
            "## Instructions (follow closely)\n\n"
            f"{instructions}\n\n"
            "---\n\n"
            "## Research topic\n\n"
            f"{topic}\n"
        )

        def _log(msg: str) -> None:
            print(msg, file=sys.stderr, flush=True)

        report = researcher.run(prompt, log=_log)
        return {"source_content": report}

    return researcher_node
