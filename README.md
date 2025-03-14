# DreamBot (sna_net_bot) - Telegram Bot for Dream Recording and Analysis

Welcome to **DreamBot** (`sna_net_bot`) — a Telegram bot designed to record and analyze dreams using AI. The bot operates in early access mode and is tailored for users interested in psychology and esotericism, particularly women. We welcome your feedback to improve the product!

## Features
- **Dream Recording:** Record up to 5 dreams per day (7 with a subscription). Receive a confirmation after recording.
- **Dream Analysis:** AI-powered analysis (1 per day) with three approaches:
  - Psychological (Freud, Jung).
  - Esoteric (dream books, tarot).
  - Psychonautic (magic of consciousness).
  - Powered by YandexGPT for advanced text processing.
- **Dream History:** View all recorded dreams.
- **Limits:** Free tier: 5 dreams and 1 analysis per day; with subscription: 7 dreams per day.
- **Feedback:** Share your thoughts to help us improve the bot.

## Tech Stack
- **Language:** Python
- **Framework:** [aiogram](https://docs.aiogram.dev/)
- **Database:** PostgreSQL
- **AI:** YandexGPT for dream analysis
- **Logging:** `logging`
- **Localization:** i18n
- **Deployment:** Docker Compose

## Installation and Setup

### Prerequisites
- [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/)
- Python 3.10+
- Telegram Bot Token (get it from [@BotFather](https://t.me/BotFather))
- YandexGPT API credentials (folder ID, key ID, API key)

### Steps
1. Clone the repository:
```bash
   git clone https://github.com/your_username/sna_net_bot.git
   cd sna_net_bot
```
2. Install Python dependencies:
```bash
pip install -r requirements.txt
```
3. Create a .env file for database initialization:
```bash
POSTGRES_USER='sna_net'
POSTGRES_PASSWORD='YUCXp?L9@22vQx%'
POSTGRES_DB='sna_net_bot'
```
4. Create a config.yaml file with the following structure:
```yaml
bot:
  token: 'your_bot_token'

channel:
  url: 'your_channel_url'  # e.g., 'https://t.me/your_channel'
  id: 'your_channel_id'    # e.g., '-1002223333311'

database:
  user: 'postgres_username'
  password: 'postgres_password'
  database: 'postgres_database'
  host: 'db'

yandex:
  folder_id: 'your_folder_id'
  key_id: 'your_key_id'
  api_key: 'your_api_key'

admin:
  id: 'your_admin_id'  # e.g., '5111525111'
```
5. Run the bot using Docker Compose:
```bash
docker-compose up --build
```
### Access the bot on Telegram:
[Bot link](https://t.me/sna_net_bot)

### Configuration
.env: Used for PostgreSQL initialization (user, password, database).
config.yaml: Contains bot token, channel info, database settings, YandexGPT credentials, and admin ID.

### Contributing
We are open to contributions! Feel free to create an issue or submit a pull request. Share your feedback via Telegram: t.me/okolo_boga.

### License
[MIT License](https://github.com/okoloboga/sna_net/blob/main/LICENSE.md)

### Authors
[okoloboga](https://t.me/okolo_boga)

### Acknowledgments
Thanks to the [aiogram](https://docs.aiogram.dev/en/v3.18.0/) community for their amazing library.
Gratitude to all users providing feedback to improve the bot!