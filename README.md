# Telegram → Gemini: Deep Research, SEO blog, judge

Reads the **latest message** in a Telegram group (the **topic**), runs **Google Gemini Deep Research** with the [`skills/deep-research/SKILL.md`](skills/deep-research/SKILL.md) brief, drafts a markdown blog with [`skills/blog-post/SKILL.md`](skills/blog-post/SKILL.md), and loops with [`skills/seo-judge/SKILL.md`](skills/seo-judge/SKILL.md) up to **5** times. On success, Telegram gets a **short excerpt** only (full post is not sent).

## Setup

1. Register for a Telegram API ID and API Hash at https://my.telegram.org.
2. Copy `.env.example` to `.env` and fill in credentials (see comments in `.env.example`).
3. **Install Python dependencies only inside a virtual environment** (do not install into the system interpreter):

   ```sh
   cd /path/to/gd_posts
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

4. Run:

   ```sh
   .venv/bin/python main.py
   ```

## Security

- Do not commit your `.env` or Telethon session files.
- Respect Telegram’s and Google’s terms of service.

## Layout

- `main.py` — entry point.
- `pipeline.py` — Telegram + orchestration.
- `gemini_workflow.py` — Deep Research (interactions agent), writer, judge.
- `skills_loader.py` — loads `SKILL.md` frontmatter + body.
- `skills/*/SKILL.md` — editable prompts (“skills”).
