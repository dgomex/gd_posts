# Telegram → Gemini Deep Research → LiteLLM blog → judge

The pipeline reads the **latest message** in a Telegram group or channel (used as the **research topic**; the chat should have at least one message), runs **Gemini Deep Research** with instructions from [`prompts/deep_research.txt`](prompts/deep_research.txt), then uses **LiteLLM** to draft and refine a blog post for up to **five** attempts. On each attempt it calls a **writer** and a **judge** with system prompts from [`prompts/blog_writer.txt`](prompts/blog_writer.txt) and [`prompts/judge.txt`](prompts/judge.txt). The loop stops when the judge’s reply is exactly **`approved`** (compared case-insensitively). The final post is **printed to the console**; sending anything back to Telegram is left commented out in the code.

Writer and judge both use the **`LLM`** class in [`src/llm.py`](src/llm.py) (`litellm.completion` with a system and user message). The model id is currently hardcoded in [`src/main.py`](src/main.py) as **`gemma3:4b-cloud`** against **`LLM_BASE_URL`** (default `https://ollama.com`).

## Setup

1. Create Telegram API credentials: https://my.telegram.org/apps
2. Copy `.env.example` to `.env` and fill in at least **Telegram** (`API_ID`, `API_HASH`, `GROUP`) and **Gemini** (`GEMINI_API_KEY` or `GOOGLE_API_KEY`). For Ollama Cloud–style models, set **`OLLAMA_API_KEY`** (or whatever your provider expects; see [LiteLLM docs](https://docs.litellm.ai/docs/)).
3. Install dependencies **inside a virtual environment**:

   ```sh
   cd /path/to/gd_posts
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

4. Run from the repository root:

   ```sh
   .venv/bin/python src/main.py
   ```

   On first run, Telethon will prompt you to sign in and will create a **`session.session`** file next to the process current working directory (the client is named `session` in code). Run from the repo root consistently so that file path stays predictable, or adjust [`src/telegram.py`](src/telegram.py) if you want a fixed path.

## Environment variables

See [`.env.example`](.env.example) for the full list. In short:

| Variable | Role |
|----------|------|
| `API_ID`, `API_HASH`, `GROUP` | Telethon: app credentials and numeric chat id |
| `GEMINI_API_KEY` or `GOOGLE_API_KEY` | Google GenAI client for Deep Research |
| `GEMINI_DEEP_RESEARCH_AGENT` | Optional; defaults to `deep-research-pro-preview-12-2025` in code |
| `LLM_BASE_URL` | Optional; default `https://ollama.com` for LiteLLM |

## Repository layout

| Path | Purpose |
|------|---------|
| `src/main.py` | Async entrypoint: Telegram → research → writer/judge loop |
| `src/telegram.py` | Telethon client: latest group message, optional send/reply helpers |
| `src/gemini.py` | `google.genai` client and Deep Research polling |
| `src/llm.py` | Thin LiteLLM wrapper (`text_complete`) |
| `prompts/*.txt` | Editable instructions for deep research, blog writer, and judge |
