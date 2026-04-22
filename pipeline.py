"""Telegram trigger → Deep Research → blog post → judge loop → Telegram status."""

from __future__ import annotations

import asyncio
import os
import traceback
from pathlib import Path

from dotenv import load_dotenv
from google.genai import Client
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest

from gemini_workflow import judge_blog_post, research_excerpt, run_deep_research, write_blog_post
from skills_loader import load_skill

REPO_ROOT = Path(__file__).resolve().parent

TELEGRAM_MAX_MESSAGE_LEN = 4096
POST_ATTEMPTS = 5
DEFAULT_EXCERPT_CHARS = 700


def _clip_telegram(text: str) -> str:
    if len(text) <= TELEGRAM_MAX_MESSAGE_LEN:
        return text
    return text[: TELEGRAM_MAX_MESSAGE_LEN - 30] + "\n\n[message truncated]"


def _build_success_message(excerpt: str) -> str:
    excerpt = excerpt.strip().replace("\r\n", "\n")
    if len(excerpt) > DEFAULT_EXCERPT_CHARS:
        excerpt = excerpt[: DEFAULT_EXCERPT_CHARS - 1].rstrip() + "…"
    body = (
        "Success: blog post approved by the SEO judge.\n\n"
        f"Excerpt:\n\n{excerpt}\n\n"
        "(Full post is not sent on Telegram by design.)"
    )
    return _clip_telegram(body)


def _build_failure_message(reason: str, extra: str | None = None) -> str:
    parts = ["Failure:", reason.strip()]
    if extra:
        extra = extra.strip()
        if extra:
            parts.append(extra)
    return _clip_telegram("\n\n".join(parts))


async def run_pipeline() -> None:
    print("[pipeline] run_pipeline: loading .env", flush=True)
    load_dotenv()
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    group = os.getenv("GROUP")
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not all([api_id, api_hash, group, api_key]):
        print(
            "[pipeline] run_pipeline: missing env — need API_ID, API_HASH, GROUP, "
            "and GEMINI_API_KEY (or GOOGLE_API_KEY). Exiting.",
            flush=True,
        )
        return

    writer_model = os.getenv("GEMINI_WRITER_MODEL", "gemini-2.5-flash")
    judge_model = os.getenv("GEMINI_JUDGE_MODEL", "gemini-2.5-flash")
    dr_agent = os.getenv("GEMINI_DEEP_RESEARCH_AGENT", "deep-research-pro-preview-12-2025")
    poll_interval = float(os.getenv("DEEP_RESEARCH_POLL_SECONDS", "10"))
    max_wait = float(os.getenv("DEEP_RESEARCH_MAX_WAIT_SECONDS", "1800"))

    print(
        "[pipeline] Config: "
        f"group={group!r} writer_model={writer_model!r} judge_model={judge_model!r} "
        f"dr_agent={dr_agent!r} poll_interval_s={poll_interval} max_wait_s={max_wait} "
        "(API key present, not printed).",
        flush=True,
    )

    dr_path = REPO_ROOT / "skills" / "deep-research" / "SKILL.md"
    blog_path = REPO_ROOT / "skills" / "blog-post" / "SKILL.md"
    judge_path = REPO_ROOT / "skills" / "seo-judge" / "SKILL.md"
    print(f"[pipeline] Loading skills from {dr_path}", flush=True)
    dr_skill = load_skill(dr_path)
    print(f"[pipeline] Loaded deep-research skill name={dr_skill.name!r} body_chars={len(dr_skill.body)}", flush=True)
    print(f"[pipeline] Loading skills from {blog_path}", flush=True)
    blog_skill = load_skill(blog_path)
    print(f"[pipeline] Loaded blog-post skill name={blog_skill.name!r} body_chars={len(blog_skill.body)}", flush=True)
    print(f"[pipeline] Loading skills from {judge_path}", flush=True)
    judge_skill = load_skill(judge_path)
    print(f"[pipeline] Loaded seo-judge skill name={judge_skill.name!r} body_chars={len(judge_skill.body)}", flush=True)

    print("[pipeline] Initializing Gemini client.", flush=True)
    gemini_client = Client(api_key=api_key)

    print("[pipeline] Connecting Telethon (session file in cwd).", flush=True)
    async with TelegramClient("session", int(api_id), api_hash) as tg:
        print(f"[pipeline] Resolving group entity id={group!r}.", flush=True)
        group_entity = await tg.get_entity(int(group))
        print("[pipeline] Fetching latest group message (limit=1).", flush=True)
        history = await tg(
            GetHistoryRequest(
                peer=group_entity,
                limit=1,
                offset_date=None,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0,
            )
        )
        if not history.messages:
            print("[pipeline] No messages in group history. Exiting.", flush=True)
            return

        latest = history.messages[0]
        topic = (latest.message or "").strip()
        reply_to = latest.id
        print(
            f"[pipeline] Latest message id={reply_to} topic_len={len(topic)} "
            f"topic_preview={topic[:120]!r}{'…' if len(topic) > 120 else ''}",
            flush=True,
        )

        async def reply(text: str) -> None:
            print(
                f"[pipeline] Sending Telegram reply (reply_to={reply_to}) len={len(text)}.",
                flush=True,
            )
            await tg.send_message(group_entity, text, reply_to=reply_to)
            print("[pipeline] Telegram reply sent.", flush=True)

        if not topic:
            print("[pipeline] Topic empty — sending failure to Telegram and exiting.", flush=True)
            await reply(_build_failure_message("Empty topic message."))
            return

        print("[pipeline] Stage: Deep Research (blocking thread).", flush=True)
        try:
            research = await asyncio.to_thread(
                run_deep_research,
                gemini_client,
                topic=topic,
                skill_body=dr_skill.body,
                agent=dr_agent,
                poll_interval_s=poll_interval,
                max_wait_s=max_wait,
            )
        except Exception as exc:
            print(f"[pipeline] Deep Research raised: {exc!r}", flush=True)
            print(traceback.format_exc(), flush=True)
            tb = traceback.format_exc()
            await reply(
                _build_failure_message(
                    f"Deep Research failed: {exc}",
                    extra=tb[-1500:] if len(tb) > 1500 else tb,
                )
            )
            return

        print(f"[pipeline] Deep Research done: research_chars={len(research)}.", flush=True)

        excerpt_source = research_excerpt(research)
        print(
            f"[pipeline] Research excerpt for judge: excerpt_chars={len(excerpt_source)} "
            f"(truncation applied vs full report if long).",
            flush=True,
        )
        approved_post: str | None = None
        last_feedback = ""
        last_draft = ""

        # OUTPUT RESEARCH TO A FILE
        with open("research.md", "w") as f:
            f.write(research)

        for attempt in range(1, POST_ATTEMPTS + 1):
            print(
                f"[pipeline] Stage: write + judge attempt {attempt}/{POST_ATTEMPTS}.",
                flush=True,
            )
            try:
                print("[pipeline] Calling blog writer in thread…", flush=True)
                last_draft = await asyncio.to_thread(
                    write_blog_post,
                    gemini_client,
                    model=writer_model,
                    blog_skill_body=blog_skill.body,
                    topic=topic,
                    research=research,
                    previous_draft=last_draft if attempt > 1 else None,
                    judge_feedback=last_feedback or None,
                )
                print(f"[pipeline] Writer returned draft_chars={len(last_draft)}.", flush=True)
                print("[pipeline] Calling judge in thread…", flush=True)
                verdict = await asyncio.to_thread(
                    judge_blog_post,
                    gemini_client,
                    model=judge_model,
                    judge_skill_body=judge_skill.body,
                    topic=topic,
                    research_excerpt=excerpt_source,
                    post_markdown=last_draft,
                )
                print(
                    f"[pipeline] Judge result: approved={verdict.approved} scores={verdict.scores!r}",
                    flush=True,
                )
                if not verdict.approved:
                    fb = verdict.feedback.strip() or "(no feedback text)"
                    preview = fb[:400] + ("…" if len(fb) > 400 else "")
                    print(f"[pipeline] Judge feedback preview: {preview!r}", flush=True)
            except Exception as exc:
                print(f"[pipeline] Writer/judge error on attempt {attempt}: {exc!r}", flush=True)
                print(traceback.format_exc(), flush=True)
                await reply(
                    _build_failure_message(
                        f"Writer/judge error on attempt {attempt}/{POST_ATTEMPTS}: {exc}",
                    )
                )
                return

            if verdict.approved:
                approved_post = last_draft
                print("[pipeline] Judge approved — exiting write/judge loop.", flush=True)
                break

            last_feedback = verdict.feedback.strip() or (
                "Revise for stronger SEO structure, intent match, and specificity."
            )
            print("[pipeline] Judge rejected — will pass feedback to next writer pass.", flush=True)

        if approved_post is None:
            print(
                f"[pipeline] No approval after {POST_ATTEMPTS} attempts — sending failure to Telegram.",
                flush=True,
            )
            await reply(
                _build_failure_message(
                    f"Judge did not approve after {POST_ATTEMPTS} attempts.",
                    extra=f"Last feedback:\n{last_feedback}",
                )
            )
            return

        print(
            f"[pipeline] Success path: sending Telegram excerpt (full post_chars={len(approved_post)}).",
            flush=True,
        )
        await reply(_build_success_message(approved_post))
        print("[pipeline] run_pipeline: completed successfully.", flush=True)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
