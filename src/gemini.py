from google.genai import Client

import os
import time
from pathlib import Path
from typing import Any



class Gemini:
    def __init__(self, api_key):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.gemini_client = Client(api_key=self.api_key)

    def _text_from_interaction_outputs(self, interaction: Any) -> str:
        chunks: list[str] = []
        for item in interaction.outputs or []:
            if getattr(item, "type", None) == "text":
                chunks.append(getattr(item, "text", "") or "")
        return "\n\n".join(c for c in chunks if c).strip()

    def run_deep_research(self, prompt_txt_path, topic, agent="deep-research-pro-preview-12-2025", background=True, poll_interval_s=2.0, max_wait_s=1800.0):

        instructions = prompt_txt_path.read_text(encoding="utf-8").strip()
        user_input = (
            "## Instructions (from prompt file — follow closely)\n\n"
            f"{instructions}\n\n"
            "---\n\n"
            "## Research topic\n\n"
            f"{topic.strip()}\n"
        )
        print(
            f"[deep_research] create interaction agent={agent!r} prompt_file={prompt_txt_path!r} "
            f"input_chars={len(user_input)} poll={poll_interval_s}s max_wait={max_wait_s}s.",
            flush=True,
        )
        created = self.gemini_client.interactions.create(
            agent=agent,
            input=user_input,
            background=background,
            stream=False,
        )
        interaction_id = created.id
        deadline = time.monotonic() + max_wait_s
        last: Any = None
        poll_n = 0
        prev_status: str | None = None
        while time.monotonic() < deadline:
            poll_n += 1
            last = self.gemini_client.interactions.get(interaction_id, stream=False)
            status = last.status
            if status != prev_status or poll_n == 1 or poll_n % 5 == 0:
                print(f"[deep_research] poll #{poll_n} status={status!r} id={interaction_id!r}", flush=True)
            prev_status = status
            if status == "completed":
                text = self._text_from_interaction_outputs(last)
                if not text:
                    raise RuntimeError("Deep Research completed but returned no text outputs.")
                print(f"[deep_research] done output_chars={len(text)}", flush=True)
                return text
            if status in ("failed", "cancelled", "incomplete"):
                raise RuntimeError(f"Deep Research ended with status={status!r}.")
            time.sleep(poll_interval_s)

        raise TimeoutError(
            f"Deep Research timed out after {max_wait_s:.0f}s (last_status={getattr(last, 'status', None)!r})."
        )