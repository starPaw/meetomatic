"""Environment configuration; .env is read as data, never executed."""

from dataclasses import dataclass
import os
from pathlib import Path
from urllib.parse import urlsplit


def load_env(path: str = ".env"):
    file = Path(path)
    if not file.is_file():
        return
    for line in file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or not key.replace("_", "").isalnum():
            raise ValueError("Invalid .env entry")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Config:
    token: str
    organizers: frozenset[int]
    group_id: int
    database: str = "data/bot.sqlite3"
    reminder_minutes: int = 60
    webapp_url: str = ""
    web_host: str = "127.0.0.1"
    web_port: int = 8087
    webapp_direct: bool = False

    @classmethod
    def from_env(cls, discovery: bool = False):
        load_env()
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not token or ":" not in token or any(c.isspace() for c in token):
            raise ValueError("Set TELEGRAM_BOT_TOKEN in .env")
        try:
            organizers = frozenset(int(uid.strip()) for uid in os.environ.get("ORGANIZER_IDS", "").split(",") if uid.strip())
            group = int(os.environ.get("GROUP_CHAT_ID") or 0)
            reminder = int(os.environ.get("REMINDER_LEAD_MINUTES", "60"))
        except ValueError as exc:
            raise ValueError("Organizer IDs, group ID and reminder minutes must be integers") from exc
        if any(uid <= 0 for uid in organizers) or group > 0 or (not discovery and group < 0 and not organizers):
            raise ValueError("Legacy GROUP_CHAT_ID must be negative and have positive ORGANIZER_IDS; new groups connect in Telegram")
        if not 1 <= reminder <= 10080:
            raise ValueError("REMINDER_LEAD_MINUTES must be between 1 and 10080")
        webapp = os.environ.get("WEBAPP_URL", "").strip().rstrip("/")
        if webapp and (urlsplit(webapp).scheme != "https" or not urlsplit(webapp).netloc or urlsplit(webapp).path not in ("", "/") or urlsplit(webapp).query or urlsplit(webapp).fragment):
            raise ValueError("WEBAPP_URL must be an HTTPS origin without a path or query parameters")
        try:
            port = int(os.environ.get("WEB_PORT", "8087"))
        except ValueError as exc:
            raise ValueError("WEB_PORT must be an integer") from exc
        if not 1024 <= port <= 65535:
            raise ValueError("WEB_PORT must be between 1024 and 65535")
        return cls(token, organizers, group, os.environ.get("DATABASE_PATH", "data/bot.sqlite3"), reminder,
                   webapp, os.environ.get("WEB_HOST", "127.0.0.1"), port,
                   os.environ.get("WEBAPP_DIRECT_LINKS", "0") == "1")
