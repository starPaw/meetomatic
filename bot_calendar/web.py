"""Telegram Mini App HTTP interface. Identity comes only from signed initData."""

import argparse
from datetime import datetime, timedelta
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
from pathlib import Path
import re
import threading
from urllib.parse import parse_qsl, parse_qs, urlsplit
import uuid

from .config import Config
from .domain import PRAGUE, RuleError, clock, parse_deadline, utc_now
from .service import Application
from .storage import Database
from .telegram import TelegramClient, TelegramError
from . import views


log = logging.getLogger(__name__)
ASSETS = Path(__file__).with_name("static")


class APIError(Exception):
    def __init__(self, status: int, message: str, code: str = "invalid_request"):
        super().__init__(message)
        self.status, self.code = status, code


def verify_init_data(raw: str, token: str, now: float, max_age: int = 3600) -> dict:
    try:
        if not raw or len(raw) > 16384:
            raise ValueError
        pairs = parse_qsl(raw, keep_blank_values=True, strict_parsing=True)
        fields = dict(pairs)
        if len(fields) != len(pairs):
            raise ValueError
        received = fields.pop("hash")
        if not re.fullmatch(r"[0-9a-f]{64}", received):
            raise ValueError
        check = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
        secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(received, expected):
            raise ValueError
        authenticated_at = int(fields["auth_date"])
        if not now - max_age <= authenticated_at <= now + 30:
            raise ValueError
        user = json.loads(fields["user"])
        if not isinstance(user, dict) or type(user.get("id")) is not int or user["id"] <= 0 or user.get("is_bot"):
            raise ValueError
        return user
    except (KeyError, ValueError, TypeError):
        raise APIError(401, "Откройте приложение заново через Telegram.", "telegram_auth_required") from None


def state_for(app: Application, user: dict, sid: int | None = None, group_id: int | None = None, meeting_id: int | None = None) -> dict:
    uid = user["id"]
    now = datetime.fromtimestamp(app.now(), PRAGUE)
    groups = app.db.all("SELECT g.* FROM groups g WHERE g.active=1 AND ("
             "EXISTS(SELECT 1 FROM group_organizers WHERE group_id=g.id AND user_id=?) OR "
             "EXISTS(SELECT 1 FROM group_members WHERE group_id=g.id AND user_id=?) OR "
             "EXISTS(SELECT 1 FROM sessions s JOIN participants p ON p.session_id=s.id WHERE s.group_id=g.id AND p.user_id=?)) ORDER BY g.created_at,g.id", (uid, uid, uid))
    result = {
        "user": {"id": uid, "name": (user.get("first_name") or "Участник")[:48]},
        "is_organizer": False, "bot_username": app.username,
        "timezone": "Europe/Prague", "server_time": app.now(),
        "defaults": {"deadline": (now + timedelta(days=1)).replace(hour=20, minute=0).strftime("%Y-%m-%dT%H:%M")},
        "round": None, "schedule": None, "group_name": "Наша встреча", "people": [],
        "group_id": None, "meeting_id": None, "meetings": [],
        "groups": [{"id": group["id"], "title": group["title"], "is_organizer": app.is_organizer(uid, group["id"])} for group in groups],
        "connect_url": f"https://t.me/{app.username}?start=connect",
        "add_bot_url": f"https://t.me/{app.username}?startgroup=connect",
    }
    row = app.session(sid) if sid else None
    if row is not None:
        if (group_id is not None and group_id != row["group_id"]) or (meeting_id is not None and meeting_id != row["meeting_id"]):
            raise RuleError("Подбор относится к другой встрече или группе.")
        group_id, meeting_id = row["group_id"], row["meeting_id"]
    elif meeting_id is not None:
        meeting = app.meeting(meeting_id)
        if group_id is not None and group_id != meeting["group_id"]:
            raise RuleError("Встреча относится к другой группе.")
        group_id = meeting["group_id"]
    if group_id is None and groups:
        group_id = groups[0]["id"]
    group = next((group for group in groups if group["id"] == group_id), None)
    if group is None:
        result["not_invited"] = True
        if group_id is not None and app.db.one("SELECT 1 FROM groups WHERE id=? AND active=1", (group_id,)):
            result["join_group_id"] = group_id
        return result
    organizer = app.is_organizer(uid, group_id)
    result.update(group_id=group_id, group_name=group["title"], is_organizer=organizer)
    for meeting in app.db.all("SELECT m.*,s.id AS round_id,s.state,s.duration,"
                              "(SELECT COUNT(*) FROM participants WHERE session_id=s.id) AS expected_count,"
                              "(SELECT COUNT(*) FROM answers WHERE session_id=s.id) AS answered_count "
                              "FROM meetings m LEFT JOIN sessions s ON s.id=(SELECT MAX(id) FROM sessions WHERE meeting_id=m.id) "
                              "WHERE m.group_id=? ORDER BY m.id DESC", (group_id,)):
        schedule = app.db.one("SELECT * FROM schedules WHERE meeting_id=?", (meeting["id"],))
        item = {key: meeting[key] for key in ("id", "title", "round_id", "state", "duration", "expected_count", "answered_count", "mode")}
        item["schedule"] = {key: schedule[key] for key in ("day", "start", "duration", "session_id", "mode", "date")} if schedule else None
        result["meetings"].append(item)
    if meeting_id is None and result["meetings"]:
        meeting_id = result["meetings"][0]["id"]
    if meeting_id is not None and not any(meeting["id"] == meeting_id for meeting in result["meetings"]):
        raise RuleError("Встреча не найдена в этой группе.")
    result["meeting_id"] = meeting_id
    if row is None and meeting_id is not None:
        row = app.db.one("SELECT * FROM sessions WHERE meeting_id=? ORDER BY id DESC LIMIT 1", (meeting_id,))
    if organizer:
        people = {p["user_id"]: p["name"] for p in app.db.all("SELECT p.user_id,p.name FROM participants p JOIN sessions s ON s.id=p.session_id WHERE s.group_id=? ORDER BY s.id", (group_id,))}
        people.update({p["user_id"]: p["name"] for p in app.db.all("SELECT u.user_id,u.name FROM users u JOIN group_members gm ON gm.user_id=u.user_id WHERE gm.group_id=?", (group_id,))})
        people.setdefault(uid, result["user"]["name"])
        result["people"] = [{"id": person, "name": name} for person, name in sorted(people.items(), key=lambda item: item[1].casefold())]
    if row is not None and not organizer and not app.db.one("SELECT 1 FROM participants WHERE session_id=? AND user_id=?", (row["id"], uid)):
        result["not_invited"] = True
        return result
    schedule = app.db.one("SELECT * FROM schedules WHERE meeting_id=?", (meeting_id,)) if meeting_id is not None else None
    if schedule:
        result["schedule"] = {key: schedule[key] for key in ("day", "start", "duration", "session_id", "mode", "date")}
        result["schedule"]["text"] = views.schedule_text(schedule["day"], schedule["start"], schedule["duration"], schedule["date"])
    if row is None:
        return result
    sid = row["id"]
    view = app.view(sid)
    session = app.session(sid)
    if session["state"] == "final" and (not schedule or schedule["session_id"] != sid):
        chosen = next(slot for slot in view.slots if slot.id == session["chosen_slot"])
        result["schedule"] = {"day": chosen.day, "start": chosen.start, "duration": chosen.duration,
                              "session_id": sid, "mode": view.mode, "date": chosen.date,
                              "text": views.schedule_text(chosen.day, chosen.start, chosen.duration, chosen.date)}
    def candidate_json(candidate):
        data = {"slot_id": candidate.slot.id, "day": candidate.slot.day,
                "date": candidate.slot.date,
                "start": candidate.slot.start, "end": candidate.slot.start + view.duration,
                "label": candidate.slot.label, "available_count": len(candidate.available),
                "expected_count": len(view.names), "common": candidate.common,
                "expired": candidate.slot.starts_at is not None and candidate.slot.starts_at <= app.now()}
        if organizer:
            data["unavailable"] = [view.names[person] for person in candidate.unavailable]
            data["missing"] = [view.names[person] for person in candidate.missing]
        return data
    candidates = {candidate.slot.id: candidate for candidate in view.candidates}
    votes = {slot_id: list(view.votes.values()).count(slot_id) for slot_id in view.nominations}
    best = max(votes.values(), default=0)
    publication = app.db.one("SELECT state FROM outbox WHERE dedupe_key=?", (f"final:{sid}",))
    round_data = {
        "id": sid, "meeting_id": meeting_id, "group_id": group_id, "title": view.title,
        "state": view.state, "duration": view.duration, "windows": session["windows"],
        "mode": view.mode,
        "deadline": datetime.fromtimestamp(view.deadline, PRAGUE).isoformat(), "deadline_ts": view.deadline,
        "deadline_label": datetime.fromtimestamp(view.deadline, PRAGUE).strftime("%d.%m, %H:%M"),
        "can_answer": uid in view.names and view.state == "open" and app.now() < view.deadline,
        "is_expected": uid in view.names, "expected_count": len(view.names), "answered_count": len(view.responses),
        "missing": [view.names[person] for person in view.missing],
        "participants": [{"name": name, "answered": person in view.responses, "voted": person in view.votes, **({"id": person} if organizer else {})} for person, name in view.names.items()],
        "slots": [{"id": slot.id, "day": slot.day, "start": slot.start, "end": slot.start + slot.duration,
                   "date": slot.date,
                   "start_label": clock(slot.start), "end_label": clock(slot.start + slot.duration)} for slot in view.slots],
        "my_answer": None if uid not in view.responses else {"slots": sorted(view.responses[uid]), "none": not bool(view.responses[uid])},
        "candidates": [candidate_json(candidate) for candidate in view.top],
        "preliminary": bool(view.missing), "nominations": view.nominations,
        "vote_options": [{**candidate_json(candidates[slot_id]), "votes": votes[slot_id]} for slot_id in view.nominations],
        "voted_count": len(view.votes), "my_vote": view.votes.get(uid),
        "voting_missing": [name for person, name in view.names.items() if person not in view.votes],
        "leaders": [slot_id for slot_id, count in votes.items() if best and count == best],
        "publication_state": publication[0] if publication else None,
    }
    if organizer:
        round_data["answers"] = [{"id": person, "name": name, "slots": sorted(view.responses[person]) if person in view.responses else None} for person, name in view.names.items()]
    result["round"] = round_data
    return result


def integer(value, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise APIError(400, f"Некорректное значение: {label}.")
    return value


def group_number(value) -> int:
    if type(value) is not int or value >= 0:
        raise APIError(400, "Выберите Telegram-группу.")
    return value


def slot_list(value) -> list[int]:
    if not isinstance(value, list) or len(value) > 336 or any(type(item) is not int or item <= 0 for item in value):
        raise APIError(400, "Некорректный список интервалов.")
    return sorted(set(value))


def act(app: Application, user: dict, body: dict) -> int | None:
    uid, action = user["id"], body.get("action")
    if action == "delete_meeting":
        app.delete_meeting(uid, group_number(body.get("group")), integer(body.get("meeting"), "встреча"),
                           integer(body.get("round"), "подбор"))
        return None
    if action == "create":
        gid = group_number(body.get("group", app.config.group_id))
        app.organizer(uid, gid)
        mid = integer(body["meeting"], "встреча") if body.get("meeting") is not None else None
        if mid is not None and app.meeting(mid)["group_id"] != gid:
            raise RuleError("Эта встреча находится в другой группе.")
        try:
            request_id = str(uuid.UUID(body.get("request_id", "")))
        except (ValueError, TypeError, AttributeError):
            raise APIError(400, "Не удалось проверить создание. Обновите форму.") from None
        key = f"web-create:{uid}:{request_id}"
        existing = app.db.one("SELECT value FROM metadata WHERE key=?", (key,))
        if existing:
            if not app.db.one("SELECT 1 FROM sessions WHERE id=?", (int(existing[0]),)):
                raise RuleError("Эта встреча уже удалена. Создайте новую встречу.")
            return int(existing[0])
        people = body.get("participants")
        if not isinstance(people, list) or len(people) > 30:
            raise APIError(400, "Выберите от 1 до 30 участников.")
        parsed = []
        for person in people:
            if not isinstance(person, dict) or not isinstance(person.get("name"), str):
                raise APIError(400, "Проверьте список участников.")
            parsed.append({"id": integer(person.get("id"), "участник"), "name": " ".join(person["name"].split())[:48] or str(person["id"])})
        extra = body.get("extra_participants", "")
        if not isinstance(extra, str) or len(extra) > 2000:
            raise APIError(400, "Проверьте дополнительных участников.")
        if extra.strip():
            parsed.extend(app.parse_participants(extra, gid))
        raw_deadline = body.get("deadline")
        try:
            deadline = datetime.strptime(raw_deadline, "%Y-%m-%dT%H:%M").strftime("%d.%m.%Y %H:%M")
        except (ValueError, TypeError):
            raise APIError(400, "Укажите дату и время окончания сбора.") from None
        windows = body.get("windows")
        if not isinstance(windows, str) or len(windows) > 2000:
            raise APIError(400, "Проверьте диапазоны времени.")
        title = body.get("title", "Еженедельная встреча")
        if not isinstance(title, str):
            raise APIError(400, "Укажите название встречи.")
        sid = app.create_round(uid, parsed, integer(body.get("duration"), "длительность"), windows, parse_deadline(deadline, app.now()),
                               group_id=gid, meeting_id=mid, title=title, new_meeting=mid is None, mode=body.get("mode", "weekly"))
        app.db.execute("INSERT INTO metadata VALUES (?,?)", (key, str(sid)))
        return sid
    sid = integer(body.get("round"), "подбор")
    session = app.session(sid)
    if body.get("group") is not None and group_number(body["group"]) != session["group_id"]:
        raise RuleError("Подбор находится в другой группе.")
    if action == "availability":
        none = body.get("none", False)
        if type(none) is not bool:
            raise APIError(400, "Проверьте ответ «Ни один вариант».")
        app.save_answer(sid, uid, set(slot_list(body.get("slots"))), none)
    elif action == "vote":
        app.cast_vote(sid, uid, integer(body.get("slot"), "вариант голосования"))
    else:
        app.organizer(uid, session["group_id"])
        if action == "close":
            app.close_round(sid)
        elif action == "start_vote":
            nominated = slot_list(body.get("slots"))
            view = app.view(sid)
            if not nominated or len(nominated) > 3 or not set(nominated) <= {candidate.slot.id for candidate in view.top}:
                raise APIError(400, "Выберите от одного до трёх предложенных вариантов.")
            if view.state != "closed":
                raise APIError(409, "Сначала закройте сбор доступности.")
            partial = any(not candidate.common for candidate in view.top if candidate.slot.id in nominated)
            if partial and body.get("allow_partial") is not True:
                raise APIError(409, "Есть отказы или отсутствующие ответы. Подтвердите голосование за частичные варианты.", "partial_confirmation_required")
            app.nominate(sid, uid, nominated)
            app.start_vote(sid, uid, allow_partial=partial)
        elif action == "confirm":
            app.confirm(sid, uid, integer(body.get("slot"), "итоговый вариант"))
        else:
            raise APIError(400, "Неизвестное действие.")
    return sid


class MiniAppServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, config: Config, username: str, wake: threading.Event | None = None, address=None, telegram=None):
        self.config, self.username = config, username
        self.telegram = telegram or TelegramClient(config.token)
        self.wake = wake or threading.Event()
        super().__init__(address or (config.web_host, config.web_port), MiniAppHandler)


class MiniAppHandler(BaseHTTPRequestHandler):
    server_version = "MeetingApp"
    def log_message(self, *_):
        pass  # Do not log query strings, signed user data or request bodies.

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def respond(self, status: int, data: bytes, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' https://telegram.org; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors https://web.telegram.org https://*.telegram.org; base-uri 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(data)

    def json_response(self, status: int, data: dict):
        self.respond(status, json.dumps(data, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def do_GET(self):
        path = urlsplit(self.path).path
        assets = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                  "/translations.js": ("translations.js", "text/javascript; charset=utf-8"),
                  "/i18n.js": ("i18n.js", "text/javascript; charset=utf-8"),
                  "/availability.js": ("availability.js", "text/javascript; charset=utf-8"),
                  "/app.css": ("app.css", "text/css; charset=utf-8"), "/favicon.svg": ("favicon.svg", "image/svg+xml"),
                  "/manrope.ttf": ("manrope.ttf", "font/ttf"), "/OFL.txt": ("OFL.txt", "text/plain; charset=utf-8")}
        if path in assets:
            name, content_type = assets[path]
            self.respond(200, (ASSETS / name).read_bytes(), content_type)
        elif path == "/api/config":
            self.json_response(200, {"bot_username": self.server.username, "direct_links": self.server.config.webapp_direct})
        elif path == "/health":
            self.json_response(200, {"ok": True})
        elif path == "/api/state":
            self.api()
        else:
            self.json_response(404, {"error": "Страница не найдена."})

    def do_POST(self):
        if urlsplit(self.path).path == "/api/action":
            self.api()
        else:
            self.json_response(404, {"error": "Действие не найдено."})

    def api(self):
        db = None
        try:
            origin = self.headers.get("Origin")
            expected = urlsplit(self.server.config.webapp_url)
            if origin and expected.netloc and origin != f"{expected.scheme}://{expected.netloc}":
                raise APIError(403, "Недопустимый источник запроса.")
            user = verify_init_data(self.headers.get("X-Telegram-Init-Data", ""), self.server.config.token, utc_now())
            db = Database(self.server.config.database, initialize=False)
            app = Application(self.server.config, db, self.server.username)
            sid, gid, mid = None, None, None
            if self.command == "POST":
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                    if not 0 < size <= 65536 or self.headers.get_content_type() != "application/json":
                        raise ValueError
                    body = json.loads(self.rfile.read(size))
                    if not isinstance(body, dict):
                        raise ValueError
                except (ValueError, UnicodeError):
                    raise APIError(400, "Некорректный запрос.") from None
                if body.get("action") == "prepare_group":
                    with db.transaction():
                        app.remember(user)
                        button = app.group_request_button(user["id"])
                    prepared = self.server.telegram.call("savePreparedKeyboardButton", user_id=user["id"], button=button)
                    self.json_response(200, {"prepared_request_id": prepared["id"]})
                    return
                if body.get("action") == "join_group":
                    gid = group_number(body.get("group"))
                    app.group(gid)
                    if not app.can_access_group(user["id"], gid):
                        member = self.server.telegram.call("getChatMember", chat_id=gid, user_id=user["id"])
                        if member.get("status") not in ("creator", "administrator", "member") and not (member.get("status") == "restricted" and member.get("is_member")):
                            raise APIError(403, "Присоединиться могут только участники этой Telegram-группы.")
                    with db.transaction():
                        app.remember(user)
                        db.execute("INSERT OR IGNORE INTO group_members VALUES (?,?)", (gid, user["id"]))
                    with db.transaction():
                        snapshot = state_for(app, user, group_id=gid)
                    self.json_response(200, snapshot)
                    return
                with db.transaction():
                    app.remember(user)
                    sid = act(app, user, body)
                    if body.get("action") == "delete_meeting":
                        gid = group_number(body["group"])
                self.server.wake.set()
            else:
                params = parse_qs(urlsplit(self.path).query)
                try:
                    if "round" in params:
                        sid = integer(int(params["round"][0]), "подбор")
                    if "group" in params:
                        gid = group_number(int(params["group"][0]))
                    if "meeting" in params:
                        mid = integer(int(params["meeting"][0]), "встреча")
                except ValueError:
                    raise APIError(400, "Некорректная группа, встреча или номер подбора.") from None
                with db.transaction():
                    app.remember(user)
            with db.transaction():
                snapshot = state_for(app, user, sid, gid, mid)
            self.json_response(200, snapshot)
        except APIError as exc:
            self.json_response(exc.status, {"error": str(exc), "code": exc.code})
        except RuleError as exc:
            self.json_response(400, {"error": str(exc), "code": "rule_error"})
        except TelegramError:
            self.json_response(503, {"error": "Telegram пока не подтвердил запрос. Попробуйте снова. Для входа в группу можно отправить /app от своего имени в самой группе.", "code": "telegram_unavailable"})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            log.exception("Mini App request failed")
            self.json_response(500, {"error": "Не удалось выполнить действие. Попробуйте ещё раз.", "code": "server_error"})
        finally:
            if db:
                db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local Mini App preview (no Telegram polling)")
    parser.add_argument("--port", type=int, default=8087)
    parser.add_argument("--username", default="meeting_bot")
    args = parser.parse_args()
    config = Config.from_env()
    database = Database(config.database)
    database.close()
    server = MiniAppServer(config, args.username, address=("127.0.0.1", args.port))
    print(f"Preview: http://127.0.0.1:{args.port}/?preview=1", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
