# Meetomatic

[Meetomatic](https://t.me/MeetomaticBot) is a Telegram bot and Mini App for finding a meeting time across a group. It supports one-time meetings on specific dates and recurring weekly meetings, stores responses in SQLite, and keeps groups and meetings separate.

Participants submit their availability or explicitly decline. The organizer can review intersections, select up to three options for a final vote, and confirm the winner. Ties are resolved by the organizer. Missing responses are distinct from refusals, and partial-attendance options require explicit confirmation.

The Mini App supports English, Russian, Czech, and Ukrainian, as well as light and dark themes. Bot commands and group messages are currently in Russian. All meeting times use `Europe/Prague`, including daylight-saving transitions.

## Using the bot

Open [@MeetomaticBot](https://t.me/MeetomaticBot) in Telegram and follow the prompts to open the Mini App. Add the bot to a group and connect the group in the app. Organizers can create meetings, invite participants, collect availability, start a vote, and confirm a result. Participants can update their availability before collection closes and change their vote while voting is open.

## Running your own instance

You need Python 3.11 or newer, the system time zone database (such as `tzdata` on Linux), and network access to Telegram. There are no third-party Python dependencies. For the Mini App, you also need a public HTTPS origin and reverse proxy.

1. Create a bot with [@BotFather](https://t.me/BotFather) and add it to your Telegram group.
2. Copy `.env.example` to `.env`, set `TELEGRAM_BOT_TOKEN`, and restrict access with `chmod 600 .env`. Never commit this file or your SQLite database.
3. Set `WEBAPP_URL` to your HTTPS origin to enable the Mini App. Configure your reverse proxy to forward requests to the configured `WEB_HOST` and `WEB_PORT`. The files in `deploy/` are examples; replace the domain, paths, and service user before using them.
4. Run the checks and start one polling process for the token:

```sh
python3 -m bot_calendar --check
python3 -m bot_calendar
```

`--check` validates configuration and Telegram connectivity without polling. An existing webhook must be removed explicitly before long polling can start. New installations can leave `ORGANIZER_IDS` and `GROUP_CHAT_ID` empty and connect groups through the Mini App. Those variables are for bootstrapping a legacy single-group installation. `python3 -m bot_calendar --discover` enables ID discovery with `/whoami`.

For direct Mini App links, configure the bot's Main App in BotFather with the same `WEBAPP_URL` and set `WEBAPP_DIRECT_LINKS=1`. Without it, links open the bot's private chat first.

Preview the interface locally without Telegram polling:

```sh
python3 -m bot_calendar.web --port 8087
# Open http://127.0.0.1:8087/?preview=1
```

The preview uses sample data. The server verifies Telegram Mini App init data before accepting authenticated requests. Keep the database and backups private; preserve the database across updates. Before a schema upgrade, stop the service and make a consistent SQLite backup. The current schema is version 3; older code cannot read it.

## Tests

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q bot_calendar tests
node --test tests/test_availability.cjs tests/test_i18n.cjs
```

Tests run offline using temporary databases and a fake Telegram transport. Node.js is only needed for the JavaScript tests. The bundled Manrope font is distributed under its [OFL license](bot_calendar/static/OFL.txt).
