"""CLI entry point: research a topic, run the writer/judge loop, print the post."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from .config import get_settings
from .graph import build_graph
from .state import PostState


def _parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="gd-posts",
        description=(
            "Generate a blog post about a topic using a Gemini Deep Research "
            "report as input, then iterating with an LLM writer/judge loop. "
            "If the judge approves, the post is printed; otherwise the last "
            "draft is printed alongside the final feedback."
        ),
    )
    parser.add_argument(
        "topic",
        type=str,
        help="The topic Deep Research should investigate.",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Optional output file for the final post. Prints to stdout if omitted.",
    )
    parser.add_argument(
        "--save-report",
        type=Path,
        default=None,
        help="Optional path to also save the raw Deep Research report.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Override MAX_ITERATIONS (default: 3).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)

    topic = args.topic.strip()
    if not topic:
        print("Error: topic must not be empty.", file=sys.stderr)
        return 1

    settings = get_settings()
    if args.max_iterations is not None:
        settings.max_iterations = args.max_iterations

    app = build_graph(settings)

    initial_state = PostState(
        topic=topic,
        max_iterations=settings.max_iterations,
    )

    print(
        f"[gd-posts] researcher={settings.research.agent} "
        f"writer={settings.writer.provider}:{settings.writer.model} "
        f"judge={settings.judge.provider}:{settings.judge.model} "
        f"max_iterations={settings.max_iterations}",
        file=sys.stderr,
    )
    print(f"[gd-posts] topic: {topic}", file=sys.stderr)

    result = app.invoke(initial_state)
    final_state = result if isinstance(result, PostState) else PostState.model_validate(result)

    if args.save_report and final_state.source_content:
        args.save_report.write_text(final_state.source_content, encoding="utf-8")
        print(f"[gd-posts] Wrote research report to {args.save_report}", file=sys.stderr)

    last_fb = final_state.last_judgement
    if last_fb is not None:
        status = "APPROVED" if last_fb.approved else "REJECTED (max rounds reached)"
        print(
            f"\n[gd-posts] {status} after {final_state.iteration} round(s)\n"
            f"[gd-posts] Final score: {last_fb.score}/10\n"
            f"[gd-posts] Final feedback: {last_fb.feedback}\n",
            file=sys.stderr,
        )

    post = final_state.final_post or final_state.draft
    if args.output:
        args.output.write_text(post, encoding="utf-8")
        print(f"[gd-posts] Wrote post to {args.output}", file=sys.stderr)
    else:
        print(post)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
