"""Telethon-based wrapper for reading and replying to a Telegram group.

Two access patterns are exposed:

* :py:meth:`TelegramListener.fetch_latest` for single-shot runs.
* :py:meth:`TelegramListener.iter_new_messages` for long-running watcher mode;
  it yields ``(text, message_id)`` tuples in arrival order via an internal
  :py:class:`asyncio.Queue`, naturally serialising downstream processing.

The first run is interactive: Telethon prompts for the phone number and login
code in the terminal and writes a session file at
``TelegramConfig.session_path``. ``session.*`` is already in ``.gitignore``.
"""

from __future__ import annotations

import asyncio
import sys
from typing import AsyncIterator, Optional, Tuple

from .config import TelegramConfig


class TelegramListener:
    """Async context manager around a single Telethon ``TelegramClient``."""

    def __init__(self, config: TelegramConfig):
        if not config.is_configured():
            raise ValueError(
                "TelegramConfig is not fully configured. "
                "Set TELEGRAM__API_ID, TELEGRAM__API_HASH, and TELEGRAM__GROUP."
            )
        self.config = config

        try:
            from telethon import TelegramClient  # noqa: F401  (validation)
        except ImportError as exc:  # pragma: no cover - import-time guard
            raise ImportError(
                "telethon is required for the Telegram trigger. "
                "Install with: pip install 'telethon>=1.36.0'"
            ) from exc

        from telethon import TelegramClient

        self._client = TelegramClient(
            str(config.session_path),
            int(config.api_id),  # type: ignore[arg-type]
            str(config.api_hash),
        )
        self._entity = None
        self._queue: "asyncio.Queue[Tuple[str, int]]" = asyncio.Queue()
        self._handler_registered = False

    async def __aenter__(self) -> "TelegramListener":
        self._log(
            f"connecting (session={self.config.session_path}, "
            f"group={self.config.group})"
        )
        await self._client.start()
        self._entity = await self._client.get_entity(int(self.config.group))  # type: ignore[arg-type]
        self._log("connected")
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self._log("disconnecting")
        await self._client.disconnect()

    async def fetch_latest(self) -> Optional[Tuple[str, int]]:
        """Return the most recent text message in the group, or ``None``."""
        messages = await self._client.get_messages(self._entity, limit=1)
        if not messages:
            return None
        msg = messages[0]
        text = (getattr(msg, "message", None) or "").strip()
        if not text:
            return None
        return text, int(msg.id)

    async def iter_new_messages(self) -> AsyncIterator[Tuple[str, int]]:
        """Async iterator yielding ``(text, message_id)`` for each new message.

        Concurrent triggers queue: messages arriving while the consumer is
        still working on the previous one wait their turn in the queue.
        """
        from telethon import events

        if not self._handler_registered:
            @self._client.on(events.NewMessage(chats=self._entity))
            async def _handler(event):  # pragma: no cover - exercised via Telethon
                text = (getattr(event.message, "message", None) or "").strip()
                if not text:
                    return
                await self._queue.put((text, int(event.message.id)))

            self._handler_registered = True
            self._log("watching for new messages")

        while True:
            yield await self._queue.get()

    async def send_reply(self, message_id: int, text: str) -> None:
        """Send ``text`` as a reply to ``message_id`` in the configured group."""
        self._log(f"replying to message id={message_id}: {text!r}")
        await self._client.send_message(self._entity, text, reply_to=message_id)

    @staticmethod
    def _log(msg: str) -> None:
        print(f"[telegram] {msg}", file=sys.stderr, flush=True)
