"""Entry point: Telegram topic → Gemini pipeline → Telegram result."""

from __future__ import annotations

import asyncio

from pipeline import run_pipeline


if __name__ == "__main__":
    print("[main] Starting gd_posts pipeline (Telegram → Gemini → Telegram).", flush=True)
    asyncio.run(run_pipeline())
    print("[main] Pipeline finished (run_pipeline returned).", flush=True)
