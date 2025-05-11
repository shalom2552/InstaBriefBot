# InstaBriefBot

**InstaBriefBot** is a Telegram bot that collects and summarizes messages from selected news channels. It allows users to ask free-form questions and receive concise, AI-generated news briefs, using the latest messages from synced Telegram sources.

## Features

- Fetch and store messages from multiple Telegram news channels
- Ask natural-language questions and get relevant news summaries
- Sync messages on demand or via command
- Manage authorized users and news sources dynamically
- Real-time progress feedback in the chat
- Local SQLite database for storage
- GPT-powered keyword extraction and summarization
- Inline logging and error tracking
- Admin-only commands and access control

## Technologies Used

- Python 3.12+
- Telethon (Telegram API client)
- Aiogram (Telegram Bot Framework)
- OpenAI API (language model)
- SQLite (local storage)
- dotenv (env variable management)
- tqdm (CLI progress bar)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/shalom2552/InstaBriefBot.git
   cd InstaBriefBot
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your `.env` file**
   Create a `.env` file in the root directory with the following keys:

   ```env
   TELEGRAM_API_ID=insert_here
   TELEGRAM_API_HASH=insert_here
   TELEGRAM_BOT_TOKEN=insert_here
   OPENAI_API_KEY=insert_here
   AUTHORIZED_USER_IDS=123456789,987654321
   ```

## Usage

To run the bot:

```bash
python3 main.py
```

The bot will:
- Initialize the database
- Start polling for messages
- Listen for commands and respond with summaries

## Bot Commands

| Command     | Description                                |
|-------------|--------------------------------------------|
| `/start`    | Begin using the bot                        |
| `/sync`     | Sync messages from all configured channels |
| `/latest`   | Summarize the most recent synced messages  |
| `/add`      | Add a new news channel                     |
| `/remove`   | Remove an existing channel                 |
| `/debug`    | Show last extracted keywords and stats     |
| `/stats`    | View per-channel message statistics        |
| `/help`     | Show this command list                     |

## Logging

The bot logs:
- Sync operations
- Summarization queries
- Errors and exceptions
- User actions and updates

Logs appear in the terminal and can be redirected to a file if desired.

## Security Notes

- Only users listed in `AUTHORIZED_USER_IDS` can interact with the bot.
- All API keys are loaded from a secure `.env` file (excluded from version control).

## Future Ideas

- Scheduled automatic sync
- Cloud deployment
- Inline queries and reply markup
- Search across stored news
- Daily/weekly summary digest
