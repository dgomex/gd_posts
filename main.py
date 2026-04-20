import os
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
GROUP = os.getenv('GROUP')

if not all([API_ID, API_HASH, GROUP]):
    print("Please set API_ID, API_HASH, and GROUP in your .env file.")
    exit(1)

async def main():
    async with TelegramClient('session', API_ID, API_HASH) as client:
        # Get entity for the group
        group_entity = await client.get_entity(int(GROUP))
        # Fetch the latest message
        history = await client(GetHistoryRequest(
            peer=group_entity,
            limit=1,
            offset_date=None,
            offset_id=0,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0
        ))
        if not history.messages:
            print("No messages found in the group.")
            return
        latest_message = history.messages[0]
        # Reply to the group
        await client.send_message(group_entity, f"Message processed successfully: {latest_message.message}", reply_to=latest_message.id)
        
        #Delete the latest message
        #await client.delete_messages(group_entity, [latest_message.id])

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
