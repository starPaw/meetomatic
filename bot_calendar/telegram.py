"""HTTPS Telegram client and durable delivery queue."""

import json
import logging
from html import escape
from pathlib import Path
import socket
import ssl
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import views
from .domain import RuleError, deadline_label


log = logging.getLogger(__name__)


class TelegramError(Exception):
    def __init__(self, code: int, description: str, retry_after: int = 0):
        self.code = code
        self.description = description
        self.retry_after = retry_after
        super().__init__(f"Telegram API error {code}")


class TelegramClient:
    def __init__(self, token: str):
        self._token = token
        self._base = "https://api.telegram.org/bot" + token + "/"
        paths = ssl.get_default_verify_paths()
        # python.org macOS installations may not have run Install Certificates.command.
        system_ca = "/etc/ssl/cert.pem"
        fallback = system_ca if not paths.cafile and Path(system_ca).is_file() else None
        self.context = ssl.create_default_context(cafile=fallback)

    def call(self, method: str, **payload):
        request = Request(self._base + method, data=json.dumps(payload).encode(),
                          headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=35, context=self.context) as response:
                body = json.load(response)
        except HTTPError as exc:
            try:
                body = json.loads(exc.read())
            except (ValueError, OSError):
                raise TelegramError(exc.code, "HTTP request failed") from None
        except (URLError, TimeoutError, socket.timeout, OSError):
            # Never propagate exceptions containing the request URL (and bot token).
            raise TelegramError(0, "Network request failed") from None
        except (ValueError, UnicodeError):
            raise TelegramError(0, "Invalid Telegram response") from None
        if not body.get("ok"):
            description = str(body.get("description", "Request failed")).replace(self._token, "[redacted]")
            raise TelegramError(body.get("error_code", 0), description,
                                body.get("parameters", {}).get("retry_after", 0))
        return body["result"]


def verified_group_admin(client, gid: int, uid: int, bot_id: int) -> dict:
    chat = client.call("getChat", chat_id=gid)
    if chat.get("type") not in ("group", "supergroup"):
        raise RuleError("Можно подключить только Telegram-группу.")
    bot = client.call("getChatMember", chat_id=gid, user_id=bot_id)
    if bot.get("status") in ("left", "kicked"):
        raise RuleError("Сначала добавьте бота в группу.")
    if bot.get("status") == "restricted" and not bot.get("can_send_messages"):
        raise RuleError("Разрешите боту отправлять сообщения в группе.")
    if bot.get("status") == "member" and not chat.get("permissions", {}).get("can_send_messages", True):
        raise RuleError("Разрешите боту отправлять сообщения в группе.")
    admins = client.call("getChatAdministrators", chat_id=gid)
    if not any(admin.get("user", {}).get("id") == uid and admin.get("status") in ("creator", "administrator") for admin in admins):
        raise RuleError("Подключить группу может только её администратор. Отправьте команду от своего личного аккаунта.")
    return chat


class Delivery:
    def __init__(self, app, client):
        self.app = app
        self.db = app.db
        self.client = client
        self.db.execute("UPDATE outbox SET state='uncertain',last_error='Delivery interrupted; not retried' WHERE kind='reminder' AND state='sending'")

    def flush(self, limit: int = 50):
        rows = self.db.all("SELECT * FROM outbox WHERE state='pending' AND next_attempt<=? ORDER BY CASE WHEN kind='answer' THEN 0 ELSE 1 END,id LIMIT ?",
                           (self.app.now(), limit))
        for row in rows:
            if not self.db.one("SELECT 1 FROM outbox WHERE id=? AND state='pending' AND payload=?", (row["id"], row["payload"])):
                continue  # The meeting may have been deleted since this batch was read.
            payload = json.loads(row["payload"])
            if row["kind"] == "reminder":
                # Claim before I/O: after a crash/ambiguous timeout do not send a second reminder.
                self.db.execute("UPDATE outbox SET state='sending' WHERE id=?", (row["id"],))
            try:
                result, reference = self.deliver(row["kind"], payload)
            except RuleError:
                if row["kind"] in ("refresh", "reminder") and not self.db.one("SELECT 1 FROM sessions WHERE id=?", (payload["session_id"],)):
                    self.db.execute("DELETE FROM outbox WHERE id=?", (row["id"],))
                    continue
                raise
            except TelegramError as exc:
                if exc.code == 400 and "message is not modified" in exc.description.lower():
                    result, reference = None, None
                else:
                    attempts = row["attempts"] + 1
                    retryable = (exc.code in (0, 429) or exc.code >= 500) and row["kind"] != "answer"
                    if row["kind"] == "reminder":
                        retryable = exc.code == 429
                    uncertain = row["kind"] == "reminder" and (exc.code == 0 or exc.code >= 500)
                    state = "pending" if retryable else ("uncertain" if uncertain else "failed")
                    delay = max(exc.retry_after, min(300, 2 ** min(attempts, 8)))
                    self.db.execute("UPDATE outbox SET state=?,attempts=?,next_attempt=?,last_error=? WHERE id=? AND (kind!='refresh' OR payload=?)",
                                    (state, attempts, self.app.now() + delay, exc.description, row["id"], row["payload"]))
                    log.warning("Delivery %s failed, code=%s, retry=%s", row["id"], exc.code, retryable)
                    if exc.code == 429:
                        break
                    continue
            with self.db.transaction():
                if reference and result:
                    sid, column = reference
                    self.db.execute(f"UPDATE sessions SET {column}=? WHERE id=?", (result["message_id"], sid))
                if row["kind"] == "refresh":
                    # Refreshes can be queued again; domain notifications retain their dedupe keys.
                    self.db.execute("DELETE FROM outbox WHERE id=? AND payload=?", (row["id"], row["payload"]))
                else:
                    self.db.execute("UPDATE outbox SET state='sent',attempts=attempts+1 WHERE id=?", (row["id"],))

    def deliver(self, kind: str, payload: dict):
        if kind == "connect_group":
            gid, uid = payload["group_id"], payload["user_id"]
            try:
                if self.app.now() > payload["expires"]:
                    raise RuleError("Запрос подключения устарел. Выберите группу заново.")
                chat = verified_group_admin(self.client, gid, uid, int(self.app.config.token.split(":", 1)[0]))
            except (RuleError, TelegramError) as exc:
                if isinstance(exc, TelegramError) and (exc.code in (0, 429) or exc.code >= 500):
                    raise
                text = str(exc) if isinstance(exc, RuleError) else "Не удалось проверить группу. Добавьте бота, разрешите ему отправлять сообщения и выберите группу заново."
                with self.db.transaction():
                    self.app.say(payload["reply_chat"], escape(text))
                return None, None
            with self.db.transaction():
                existing = self.db.one("SELECT active FROM groups WHERE id=?", (gid,))
                self.app.connect_group(gid, chat.get("title", "Наша группа"), uid)
                self.app.say(uid, f"Группа <b>{escape(chat.get('title', 'Наша группа'))}</b> подключена. Создавайте встречи в приложении.",
                             self.app.web_button(group_id=gid, screen="meetings") if self.app.config.webapp_url else None)
                if not existing or not existing["active"]:
                    self.app.say(gid, "<b>Группа подключена</b>\nВсе встречи, выбор времени и голосования — в приложении. Администратор может создать первую встречу.", self.app.group_button(group_id=gid))
            return None, None
        if kind == "refresh":
            session = self.app.session(payload["session_id"])
            if not self.db.one("SELECT 1 FROM groups WHERE id=? AND active=1", (session["group_id"],)):
                return None, None
            view = self.app.view(session["id"])
            target = payload["target"]
            if target == "progress":
                text = views.app_progress_text(view) if self.app.config.webapp_url else views.progress_text(view)
                markup = views.keyboard([[{"text": "Выбрать время", "url": f"https://t.me/{self.app.username}?start=availability_{view.id}"}]]) if view.state == "open" else views.keyboard([])
                if self.app.config.webapp_url and view.state != "cancelled":
                    label = "Выбрать время" if view.state == "open" else "Голосовать" if view.state == "voting" else "Открыть результаты"
                    markup = self.app.group_button(label, view.id)
                column = "progress_message_id"
            else:
                text, markup = views.vote_text(view), views.vote_keyboard(view)
                if self.app.config.webapp_url and view.state == "voting":
                    markup = self.app.group_button("Голосовать в приложении", view.id, "results")
                column = "vote_message_id"
            body = {"chat_id": session["group_id"], "text": text, "parse_mode": "HTML", "reply_markup": markup}
            if session[column]:
                body["message_id"] = session[column]
                return self.client.call("editMessageText", **body), None
            return self.client.call("sendMessage", **body), (view.id, column)
        if kind == "reminder":
            view = self.app.view(payload["session_id"])
            if view.state != "open" or self.app.now() >= view.deadline or not view.missing or not self.db.one("SELECT 1 FROM groups WHERE id=? AND active=1", (view.group_id,)):
                return None, None
            names = ", ".join(f'<a href="tg://user?id={uid}">{escape(view.names[uid])}</a>' for uid in view.missing)
            payload = {"chat_id": view.group_id,
                       "text": f"Напоминание · <b>{escape(view.title)}</b> · #{view.id}. Ждём: {names}.\nОтветьте до {deadline_label(view.deadline)}.",
                       "parse_mode": "HTML"}
            return self.client.call("sendMessage", **payload), None
        if kind == "answer":
            return self.client.call("answerCallbackQuery", **payload), None
        method = payload.pop("method", "sendMessage")
        return self.client.call(method, **payload), None
