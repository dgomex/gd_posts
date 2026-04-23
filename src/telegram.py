from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest

class Telegram:
    def __init__(self, api_id, api_hash, group):
        self.api_id = int(api_id)
        self.api_hash = api_hash
        self.group = int(group)
        self.telegram_client = TelegramClient("session", int(api_id), api_hash)

    async def __aenter__(self):
        await self.telegram_client.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.telegram_client.disconnect()

    async def get_latest_message(self):
        print(f"[telegram] Resolving group entity id={self.group!r}.", flush=True)
        group_entity = await self.telegram_client.get_entity(int(self.group))
        print("[telegram] Fetching latest group message (limit=1).", flush=True)
        history = await self.telegram_client(
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
            print("[telegram] No messages in group history. Exiting.", flush=True)
            return

        latest = history.messages[0]
        topic = (latest.message or "").strip()
        message_id = latest.id
        return topic, message_id

    async def send_message(self, message):
        print(f"[telegram] Sending message to group id={self.group!r}.", flush=True)
        await self.telegram_client.send_message(self.group, message)
        print("[telegram] Message sent.", flush=True)

    async def reply(self, message, reply_to):
        print(f"[telegram] Sending reply to message id={reply_to!r}.", flush=True)
        await self.telegram_client.send_message(self.group, message, reply_to=reply_to)
        print("[telegram] Reply sent.", flush=True)