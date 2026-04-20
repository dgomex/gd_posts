# Telegram Group Reader & Responder

This project reads the latest message from a Telegram group and replies that it was processed successfully using Telethon.

## Setup
1. Register for a Telegram API ID and API Hash at https://my.telegram.org.
2. Copy `.env.example` to `.env` and fill in your credentials.
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Run the script:
   ```sh
   python main.py
   ```

## Security
- Do not commit your `.env` or session files.
- Only use your own Telegram account and respect Telegram's terms of service.
