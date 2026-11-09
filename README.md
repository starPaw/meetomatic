# Meetomatic

[Meetomatic](https://t.me/MeetomaticBot) is a Telegram bot and Mini App for finding a meeting time across a group. It supports one-time meetings on specific dates and recurring weekly meetings, stores responses in SQLite, and keeps groups and meetings separate.

Participants submit their availability or explicitly decline. The organizer can review intersections, select up to three options for a final vote, and confirm the winner. Ties are resolved by the organizer. Missing responses are distinct from refusals, and partial-attendance options require explicit confirmation.

The Mini App supports English, Russian, Czech, and Ukrainian, as well as light and dark themes. Bot commands and group messages are currently in Russian. All meeting times use `Europe/Prague`, including daylight-saving transitions.

## Using the bot

Open [@MeetomaticBot](https://t.me/MeetomaticBot) in Telegram and follow the prompts to open the Mini App. Add the bot to a group and connect the group in the app. Organizers can create meetings, invite participants, collect availability, start a vote, and confirm a result. Participants can update their availability before collection closes and change their vote while voting is open.

## Running your own instance

You need Python 3.11 or newer on a Unix-like system (Linux or macOS), the system time zone database (such as `tzdata` on Linux), and outbound HTTPS access to `api.telegram.org`. There are no third-party Python dependencies. The Mini App also needs a public HTTPS origin and a reverse proxy.

Check `python3 --version` first. If it points to an older Python, use the command for your Python 3.11+ installation in place of `python3` below (and update `ExecStart` if using the example systemd service).

1. Create a bot with [@BotFather](https://t.me/BotFather), copy its token, and add the bot to your Telegram group with permission to send messages. The person connecting the group must be a group administrator.
2. Download the project and create a private configuration file:

   ```sh
   git clone https://github.com/starPaw/meetomatic.git
   cd meetomatic
   cp .env.example .env
   chmod 600 .env
   ```

3. Edit `.env` and set `TELEGRAM_BOT_TOKEN` to the token from BotFather. For the Mini App, set `WEBAPP_URL` to your public HTTPS origin, for example `https://meet.example.com` (no path or query). Configure your domain, TLS certificate, and reverse proxy to forward requests to `WEB_HOST:WEB_PORT` (by default `127.0.0.1:8087`). The files in `deploy/` are examples; replace the domain, certificate paths, and service user before using them. Never commit `.env`, the database, or its backups.
4. From the project directory, check connectivity and start one polling process for the token:

```sh
python3 -m bot_calendar --check
python3 -m bot_calendar
```

`--check` validates configuration and Telegram connectivity without polling or sending messages. An existing webhook must be removed explicitly before long polling can start. The bot reads `.env` from its working directory; existing environment variables take precedence. Keep the process running to receive updates and process deadlines.

5. Open your bot's private chat, send `/start`, and open the Mini App. Choose the group where you are an administrator and the bot is already a member. If needed, use `/group` in the private chat to select it. Telegram verifies the administrator before connecting the group. New installations can leave `ORGANIZER_IDS` and `GROUP_CHAT_ID` empty.

### Configuration

| Variable | Purpose |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Required token for your own bot. |
| `WEBAPP_URL` | Public HTTPS origin for the Mini App. Leave empty to disable it. |
| `WEB_HOST`, `WEB_PORT` | Mini App listen address and port; defaults are `127.0.0.1` and `8087`. Keep the listener behind your HTTPS reverse proxy. |
| `WEBAPP_DIRECT_LINKS` | Set to `1` only after configuring the Main App in BotFather; defaults to `0`. |
| `DATABASE_PATH` | SQLite database path; defaults to `data/bot.sqlite3`. Its parent directory must be writable. |
| `REMINDER_LEAD_MINUTES` | Reminder lead time, from 1 to 10080 minutes; defaults to 60. |
| `ORGANIZER_IDS`, `GROUP_CHAT_ID` | Optional legacy single-group bootstrap: comma-separated positive numeric organizer IDs and a negative group chat ID. Do not use usernames for authorization. |

The text-based creation wizard is for the legacy configured group; use the Mini App for multiple groups and meetings. To discover IDs, run `python3 -m bot_calendar --discover`, send `/whoami` in the private chat and `/whoami@your_bot_username` in the group, then stop discovery before starting normal polling. Discovery requires the token and only one polling process may run at a time.

For direct Mini App links, configure the bot's Main App in BotFather with the same `WEBAPP_URL` and set `WEBAPP_DIRECT_LINKS=1`. Without it, links open the bot's private chat first.

Preview the interface locally without Telegram polling:

```sh
python3 -m bot_calendar.web --port 8087
# Open http://127.0.0.1:8087/?preview=1
```

The preview requires a valid-looking token in `.env` and a writable database path; it initializes the configured database but does not poll Telegram. Use a separate `DATABASE_PATH` for a disposable preview. Its sample interface does not submit real answers. The server verifies Telegram Mini App init data before accepting authenticated requests.

### Persistence and updates

Keep the database and backups private, and preserve the database across updates. To make a consistent backup using SQLite's backup API (replace the paths if configured differently):

```sh
python3 -c 'import sqlite3; src=sqlite3.connect("data/bot.sqlite3"); dst=sqlite3.connect("data/backup.sqlite3"); src.backup(dst); dst.close(); src.close()'
```

Stop the service and back up the database before a schema upgrade. The current schema is version 3; older code cannot read it. The example systemd unit in `deploy/bot-calendar.service` must be adapted to your user, project directory, and writable data directory before installation.

## Tests

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q bot_calendar tests
node --test tests/test_availability.cjs tests/test_i18n.cjs
```

Tests run offline using temporary databases and a fake Telegram transport. Node.js is only needed for the JavaScript tests. The bundled Manrope font is distributed under its [OFL license](bot_calendar/static/OFL.txt).
