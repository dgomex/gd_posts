"""CLI entry point: Telegram-driven trigger for the researcher/writer/judge graph.

Two modes:

* Default (single-shot): connect to the group, fetch the latest message, run
  the graph once, send the status reply, exit.
* ``--watch``: keep the Telethon connection open and run the graph for every
  new message that arrives. Messages are processed serially via an internal
  queue inside :class:`~src.telegram_io.TelegramListener`.

After every run the orchestrator:

* sends ``"Agent Feedback: Post Created"`` (judge approved) or
  ``"Agent Feedback: Post Failed to Be Created"`` (rejection / exception)
  as a Telegram reply to the original message;
* saves approved posts to ``outputs/<UTC timestamp>-<slug>.md``.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

from .config import Settings, get_settings
from .graph import build_graph
from .state import PostState
from .telegram_io import TelegramListener


REPLY_SUCCESS = "Agent Feedback: Post Created"
REPLY_FAILURE = "Agent Feedback: Post Failed to Be Created"


def _parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="gd-posts",
        description=(
            "Run the researcher/writer/judge graph on a Telegram group. "
            "By default fetches the latest message and runs once. "
            "Use --watch to process every new message as it arrives."
        ),
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch the group and run the graph for each new message.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Override MAX_ITERATIONS (default: 3).",
    )
    parser.add_argument(
        "--save-report",
        type=Path,
        default=None,
        help="In single-shot mode, also save the raw research report to this path.",
    )
    return parser.parse_args(argv)


def _slugify(text: str, max_len: int = 50) -> str:
    """Lowercase, collapse non-alphanumerics to dashes, trim, truncate."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    slug = slug[:max_len].rstrip("-")
    return slug or "post"


def _save_post(state: PostState, topic: str, outputs_dir: Path = Path("outputs")) -> Path:
    """Write the final post to ``outputs/<UTC timestamp>-<slug>.md`` and return the path."""
    outputs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = _slugify(topic)
    path = outputs_dir / f"{ts}-{slug}.md"
    post = state.final_post or state.draft or ""
    path.write_text(post, encoding="utf-8")
    return path


def _is_approved(state: PostState) -> bool:
    return bool(state.last_judgement and state.last_judgement.approved)


def _coerce_state(result: Any) -> PostState:
    return result if isinstance(result, PostState) else PostState.model_validate(result)


async def _process_one(
    settings: Settings,
    app: Any,
    listener: TelegramListener,
    topic: str,
    message_id: int,
    save_report: Optional[Path] = None,
) -> bool:
    """Run the graph for one topic and reply with status. Returns True on approval."""
    preview = topic.replace("\n", " ")[:80]
    print(f"[gd-posts] processing message id={message_id}: {preview!r}", file=sys.stderr)

    approved = False
    try:
        initial_state = PostState(topic=topic, max_iterations=settings.max_iterations)
        # Run the sync graph in a worker thread so Telethon's heartbeat keeps flowing.
        result = await asyncio.to_thread(app.invoke, initial_state)
        final_state = _coerce_state(result)

        last_fb = final_state.last_judgement
        if last_fb is not None:
            verdict = "APPROVED" if last_fb.approved else "REJECTED"
            print(
                f"[gd-posts] {verdict} after {final_state.iteration} round(s) "
                f"score={last_fb.score}/10",
                file=sys.stderr,
            )

        approved = _is_approved(final_state)
        if approved:
            path = _save_post(final_state, topic)
            print(f"[gd-posts] saved post to {path}", file=sys.stderr)

        if save_report and final_state.source_content:
            save_report.write_text(final_state.source_content, encoding="utf-8")
            print(f"[gd-posts] saved research report to {save_report}", file=sys.stderr)

    except Exception:
        print("[gd-posts] pipeline failed:", file=sys.stderr)
        traceback.print_exc()
        approved = False

    reply = REPLY_SUCCESS if approved else REPLY_FAILURE
    try:
        await listener.send_reply(message_id, reply)
    except Exception:
        # Don't let a failed reply hide the original outcome.
        print("[gd-posts] failed to send reply:", file=sys.stderr)
        traceback.print_exc()
    return approved


async def _async_main(args: argparse.Namespace, settings: Settings) -> int:
    app = build_graph(settings)

    print(
        f"[gd-posts] researcher={settings.research.agent} "
        f"writer={settings.writer.provider}:{settings.writer.model} "
        f"judge={settings.judge.provider}:{settings.judge.model} "
        f"max_iterations={settings.max_iterations}",
        file=sys.stderr,
    )

    async with TelegramListener(settings.telegram) as listener:
        if args.watch:
            print("[gd-posts] watch mode: waiting for new messages...", file=sys.stderr)
            async for text, message_id in listener.iter_new_messages():
                # In watcher mode we don't write a single research report path;
                # successive runs would clobber it. save_report is single-shot only.
                await _process_one(settings, app, listener, text, message_id)
            return 0  # unreachable in normal operation

        latest = await listener.fetch_latest()
        if latest is None:
            print("[gd-posts] no text messages found in the group.", file=sys.stderr)
            return 1
        text, message_id = latest
        ok = await _process_one(
            settings, app, listener, text, message_id, save_report=args.save_report
        )
        return 0 if ok else 2


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)

    settings = get_settings()
    if args.max_iterations is not None:
        settings.max_iterations = args.max_iterations

    if not settings.telegram.is_configured():
        print(
            "Error: Telegram is not configured. Set TELEGRAM__API_ID, "
            "TELEGRAM__API_HASH, and TELEGRAM__GROUP in your environment / .env.",
            file=sys.stderr,
        )
        return 1

    try:
        return asyncio.run(_async_main(args, settings))
    except KeyboardInterrupt:
        print("\n[gd-posts] interrupted, exiting.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
