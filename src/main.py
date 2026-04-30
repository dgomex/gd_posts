"""CLI entry point: read a source file, run the writer/judge loop, print the post."""

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
            "Generate a blog post from a source file via an LLM writer/judge loop. "
            "The writer drafts the post; the judge reviews up to N times. "
            "If the judge approves, the post is printed; otherwise the last draft "
            "is printed with the final feedback."
        ),
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to the source file to write a post about.",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Optional output file. Prints to stdout if omitted.",
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

    if not args.input.exists():
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        return 1

    settings = get_settings()
    if args.max_iterations is not None:
        settings.max_iterations = args.max_iterations

    source_content = args.input.read_text(encoding="utf-8")
    if not source_content.strip():
        print(f"Error: input file is empty: {args.input}", file=sys.stderr)
        return 1

    app = build_graph(settings)

    initial_state = PostState(
        source_content=source_content,
        max_iterations=settings.max_iterations,
    )

    print(
        f"[gd-posts] writer={settings.writer.provider}:{settings.writer.model} "
        f"judge={settings.judge.provider}:{settings.judge.model} "
        f"max_iterations={settings.max_iterations}",
        file=sys.stderr,
    )

    result = app.invoke(initial_state)
    final_state = result if isinstance(result, PostState) else PostState.model_validate(result)

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
