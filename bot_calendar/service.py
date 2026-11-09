"""Transactional bot workflow. No network calls happen in update handlers."""

from html import escape
from contextlib import nullcontext
import json
import re
import secrets
from urllib.parse import urlencode

from .config import Config
from .domain import RuleError, Slot, deadline_label, parse_deadline, parse_duration, parse_windows, utc_now
from .storage import Database
from . import views


HELP = (
    "<b>Подбор времени еженедельной встречи</b>\n"
    "Всё время — по Праге, для обычной недели.\n\n"
    "/join — сообщить боту своё имя и ID\n"
    "/whoami — ваши ID и ID чата\n"
    "/status — прогресс и кого ждём\n"
    "/schedule — выбранное расписание\n\n"
    "Организатор в личном чате:\n"
    "/new — создать подбор пошагово\n"
    "/results — пересечения и варианты голосования\n"
    "/answers — подробные ответы\n"
    "/close — закрыть сбор (также можно в группе)\n"
    "/vote — выбрать варианты финального голосования\n"
    "/confirm — подтвердить победителя или разрешить ничью\n"
    "/repeat — повторить с прежними участниками\n"
    "/cancel — отменить незавершённое создание"
)


class Application:
    def __init__(self, config: Config, db: Database, username: str,
                 now=utc_now, discovery: bool = False):
        self.config, self.db, self.username = config, db, username
        self.now, self.discovery = now, discovery
        self.bootstrap_legacy_group()

    def bootstrap_legacy_group(self):
        gid = self.config.group_id
        key = f"legacy-bootstrap:{gid}"
        if gid >= 0 or self.db.one("SELECT 1 FROM metadata WHERE key=?", (key,)):
            return
        with nullcontext() if self.db.connection.in_transaction else self.db.transaction():
            title = "Наша группа"
            setup = self.db.one("SELECT value FROM metadata WHERE key='setup_group'")
            if setup:
                selected = json.loads(setup[0])
                if selected.get("chat_id") == gid:
                    title = selected.get("title") or title
            self.db.execute("INSERT OR IGNORE INTO groups(id,title,connected_by,created_at) VALUES (?,?,?,?)",
                            (gid, title, min(self.config.organizers, default=0), self.now()))
            self.db.execute("UPDATE groups SET title=? WHERE id=?", (title, gid))
            for uid in self.config.organizers:
                self.db.execute("INSERT OR IGNORE INTO group_organizers VALUES (?,?)", (gid, uid))
                self.db.execute("INSERT OR IGNORE INTO group_members VALUES (?,?)", (gid, uid))
            self.db.execute("INSERT OR IGNORE INTO group_members SELECT ?,user_id FROM users", (gid,))
            self.db.execute("INSERT OR IGNORE INTO metadata VALUES (?,?)", (key, "1"))

    def group(self, gid: int):
        row = self.db.one("SELECT * FROM groups WHERE id=? AND active=1", (gid,))
        if not row:
            raise RuleError("Группа не подключена. Администратор может добавить её в приложении.")
        return row

    def is_organizer(self, uid: int, gid: int | None = None) -> bool:
        gid = self.config.group_id if gid is None else gid
        return bool(self.db.one("SELECT 1 FROM group_organizers o JOIN groups g ON g.id=o.group_id WHERE o.group_id=? AND o.user_id=? AND g.active=1", (gid, uid)))

    def can_access_group(self, uid: int, gid: int) -> bool:
        return bool(self.db.one("SELECT 1 FROM groups g WHERE g.id=? AND g.active=1 AND ("
                    "EXISTS(SELECT 1 FROM group_organizers WHERE group_id=g.id AND user_id=?) OR "
                    "EXISTS(SELECT 1 FROM group_members WHERE group_id=g.id AND user_id=?) OR "
                    "EXISTS(SELECT 1 FROM sessions s JOIN participants p ON p.session_id=s.id WHERE s.group_id=g.id AND p.user_id=?))", (gid, uid, uid, uid)))

    def connect_group(self, gid: int, title: str, uid: int):
        """Called only after Telegram transport verifies the actual administrator."""
        if type(gid) is not int or gid >= 0 or type(uid) is not int or uid <= 0:
            raise RuleError("Некорректная группа или организатор.")
        title = " ".join(title.split())[:100] or "Наша группа"
        self.db.execute("INSERT INTO groups(id,title,connected_by,created_at) VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,active=1", (gid, title, uid, self.now()))
        self.db.execute("INSERT OR IGNORE INTO group_organizers VALUES (?,?)", (gid, uid))
        self.db.execute("INSERT OR IGNORE INTO group_members VALUES (?,?)", (gid, uid))

    def group_request_button(self, uid: int) -> dict:
        request_id = secrets.randbelow(2 ** 31 - 1) + 1
        self.db.execute("INSERT INTO metadata VALUES (?,?)", (f"group-request:{uid}:{request_id}", str(self.now() + 600)))
        rights = {key: False for key in ("is_anonymous", "can_delete_messages", "can_manage_video_chats", "can_restrict_members",
                  "can_promote_members", "can_change_info", "can_invite_users", "can_post_stories", "can_edit_stories", "can_delete_stories", "can_send_welcome_messages")}
        rights["can_manage_chat"] = True
        return {"text": "Выбрать группу", "request_chat": {"request_id": request_id, "chat_is_channel": False,
                "bot_is_member": True, "request_title": True, "user_administrator_rights": rights}}

    def request_group(self, uid: int):
        button = self.group_request_button(uid)
        self.say(uid, "<b>Подключить группу</b>\nВыберите группу, где вы администратор и уже добавлен бот.\n"
                 f'Если её нет в списке, <a href="https://t.me/{self.username}?startgroup=connect">добавьте бота в группу</a>, затем вернитесь к выбору.',
                 {"keyboard": [[button]], "resize_keyboard": True, "one_time_keyboard": True})

    def queue_group_connection(self, uid: int, gid: int, reply_chat: int | None = None):
        if self.db.one("SELECT 1 FROM outbox WHERE kind='connect_group' AND state='pending' AND json_extract(payload,'$.user_id')=? AND json_extract(payload,'$.group_id')=?", (uid, gid)):
            return
        self.db.enqueue("connect_group", {"user_id": uid, "group_id": gid, "reply_chat": reply_chat or uid, "expires": self.now() + 600}, self.now())

    def membership_update(self, event: dict):
        chat, actor = event.get("chat", {}), event.get("from", {})
        gid = chat.get("id", 0)
        if gid >= 0 or chat.get("type") not in ("group", "supergroup"):
            return
        old, new = event.get("old_chat_member", {}).get("status"), event.get("new_chat_member", {}).get("status")
        if new in ("left", "kicked"):
            self.db.execute("UPDATE groups SET active=0 WHERE id=?", (gid,))
        elif new in ("member", "administrator") and old in ("left", "kicked") and actor.get("id", 0) > 0 and not actor.get("is_bot"):
            self.remember(actor)
            self.queue_group_connection(actor["id"], gid, gid)

    def meeting(self, mid: int):
        row = self.db.one("SELECT * FROM meetings WHERE id=?", (mid,))
        if not row:
            raise RuleError("Встреча не найдена.")
        self.group(row["group_id"])
        return row

    def delete_meeting(self, uid: int, gid: int, mid: int, expected_round: int):
        """Delete a finished meeting inside the caller's write transaction."""
        self.organizer(uid, gid)
        key = f"deleted-meeting:{mid}"
        deleted = self.db.one("SELECT value FROM metadata WHERE key=?", (key,))
        if deleted and deleted[0] == str(gid):
            return  # A retry after a lost response must not affect another meeting.
        meeting = self.meeting(mid)
        if meeting["group_id"] != gid:
            raise RuleError("Эта встреча находится в другой группе.")
        latest = self.latest(meeting_id=mid)
        if latest["id"] != expected_round or latest["state"] != "final":
            raise RuleError("Удалить можно только встречу с завершённым подбором. Обновите список встреч.")
        rounds = self.db.all("SELECT id FROM sessions WHERE meeting_id=?", (mid,))
        for row in rounds:
            sid = row["id"]
            self.db.execute("DELETE FROM outbox WHERE json_extract(payload,'$.session_id')=? "
                            "OR dedupe_key IN (?,?,?)", (sid, f"final:{sid}", f"all-answered:{sid}", f"all-voted:{sid}"))
        self.db.execute("DELETE FROM schedules WHERE meeting_id=?", (mid,))
        for table in ("availability", "votes", "drafts", "answers", "slots", "participants"):
            self.db.execute(f"DELETE FROM {table} WHERE session_id IN (SELECT id FROM sessions WHERE meeting_id=?)", (mid,))
        self.db.execute("DELETE FROM sessions WHERE meeting_id=?", (mid,))
        self.db.execute("DELETE FROM meetings WHERE id=?", (mid,))
        self.db.execute("INSERT INTO metadata VALUES (?,?)", (key, str(gid)))

    def say(self, chat_id: int, text: str, markup: dict | None = None):
        chunks, chunk = [], ""
        for line in text.splitlines():
            if chunk and len(chunk) + len(line) > 3500:
                chunks.append(chunk.rstrip())
                chunk = ""
            chunk += line + "\n"
        if chunk:
            chunks.append(chunk.rstrip())
        for index, content in enumerate(chunks):
            body = {"chat_id": chat_id, "text": content, "parse_mode": "HTML"}
            if index == len(chunks) - 1 and markup is not None:
                body["reply_markup"] = markup
            self.db.enqueue("message", body, self.now())

    def edit(self, chat_id: int, message_id: int, text: str, markup: dict):
        self.db.enqueue("message", {"method": "editMessageText", "chat_id": chat_id,
                                   "message_id": message_id, "text": text,
                                   "parse_mode": "HTML", "reply_markup": markup}, self.now())

    def answer_callback(self, query_id: str, text: str = "", alert: bool = False):
        self.db.enqueue("answer", {"callback_query_id": query_id, "text": text[:200],
                                   "show_alert": alert}, self.now())

    def process(self, update: dict):
        update_id = update["update_id"]
        with self.db.transaction():
            if update_id < self.db.offset:
                return
            self.db.execute("SAVEPOINT action")
            try:
                if "message" in update:
                    self.message(update["message"])
                elif "callback_query" in update and not self.discovery:
                    self.callback(update["callback_query"])
                elif "my_chat_member" in update and not self.discovery:
                    self.membership_update(update["my_chat_member"])
            except RuleError as exc:
                self.db.execute("ROLLBACK TO action")
                if "callback_query" in update:
                    self.answer_callback(update["callback_query"]["id"], str(exc), True)
                else:
                    self.say(update["message"]["chat"]["id"], escape(str(exc)))
            self.db.execute("RELEASE action")
            self.db.set_offset(update_id + 1)
            self.db.execute("INSERT INTO metadata VALUES ('last_update_at',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(self.now()),))

    def poll_offset(self) -> int:
        last = self.db.one("SELECT value FROM metadata WHERE key='last_update_at'")
        if self.db.offset and last and self.now() - float(last[0]) >= 7 * 86400:
            # Telegram may randomize update IDs after a week without updates.
            # Earlier updates have already expired (Telegram retains them for 24 hours).
            with self.db.transaction():
                self.db.set_offset(0)
                self.db.execute("DELETE FROM metadata WHERE key='last_update_at'")
        return self.db.offset

    def remember(self, user: dict):
        uid = user["id"]
        name = " ".join(filter(None, [user.get("first_name"), user.get("last_name")]))
        name = " ".join(name.split())[:48] or str(uid)
        username = user.get("username", "").casefold() or None
        if username:
            self.db.execute("UPDATE users SET username=NULL WHERE username=? AND user_id!=?", (username, uid))
        self.db.execute("INSERT INTO users VALUES (?,?,?) ON CONFLICT(user_id) DO UPDATE SET name=excluded.name,username=excluded.username",
                        (uid, name, username))

    def organizer(self, uid: int, gid: int | None = None):
        if not self.is_organizer(uid, gid):
            raise RuleError("Эта команда доступна только организатору.")

    def private_organizer(self, uid: int, chat_id: int, gid: int | None = None):
        self.organizer(uid, gid)
        if chat_id != uid:
            raise RuleError(f"Для этой команды откройте личный чат: https://t.me/{self.username}")

    def session(self, sid: int):
        row = self.db.one("SELECT s.*,m.title FROM sessions s JOIN meetings m ON m.id=s.meeting_id WHERE s.id=?", (sid,))
        if not row:
            raise RuleError("Подбор не найден.")
        return row

    def latest(self, group_id: int | None = None, meeting_id: int | None = None):
        if meeting_id is not None:
            row = self.db.one("SELECT * FROM sessions WHERE meeting_id=? ORDER BY id DESC LIMIT 1", (meeting_id,))
        else:
            row = self.db.one("SELECT * FROM sessions WHERE group_id=? ORDER BY id DESC LIMIT 1", (self.config.group_id if group_id is None else group_id,))
        if not row:
            raise RuleError("Подборов пока нет. Организатор может начать с /new в личном чате.")
        return row

    def view(self, sid: int) -> views.RoundView:
        row = self.session(sid)
        names = {p["user_id"]: p["name"] for p in self.db.all("SELECT * FROM participants WHERE session_id=? ORDER BY user_id", (sid,))}
        slots = [Slot(s["slot_id"], s["day"], s["start"], row["duration"], s["date"])
                 for s in self.db.all("SELECT * FROM slots WHERE session_id=? ORDER BY slot_id", (sid,))]
        responses = {a["user_id"]: set() for a in self.db.all("SELECT user_id FROM answers WHERE session_id=?", (sid,))}
        for answer in self.db.all("SELECT user_id,slot_id FROM availability WHERE session_id=?", (sid,)):
            responses[answer["user_id"]].add(answer["slot_id"])
        votes = {v["user_id"]: v["slot_id"] for v in self.db.all("SELECT * FROM votes WHERE session_id=?", (sid,))}
        return views.RoundView(sid, row["state"], row["duration"], row["deadline"], names,
                               slots, responses, json.loads(row["nominations"]), votes, bool(row["results_visible"]), row["title"], row["group_id"], row["meeting_id"], row["mode"])

    def expected(self, sid: int, uid: int):
        if not self.db.one("SELECT 1 FROM participants WHERE session_id=? AND user_id=?", (sid, uid)):
            raise RuleError("Вы не включены в список ожидаемых участников этого подбора.")

    def open_for_answer(self, sid: int, uid: int):
        row = self.session(sid)
        self.group(row["group_id"])
        self.expected(sid, uid)
        if row["state"] != "open" or self.now() >= row["deadline"]:
            raise RuleError("Сбор уже закрыт. Изменить доступность нельзя.")

    def selection(self, sid: int, uid: int) -> set[int]:
        row = self.db.one("SELECT selected FROM drafts WHERE session_id=? AND user_id=?", (sid, uid))
        if row:
            return set(json.loads(row[0]))
        selected = self.view(sid).responses.get(uid, set())
        self.set_selection(sid, uid, selected)
        return selected

    def set_selection(self, sid: int, uid: int, selected: set[int]):
        self.db.execute("INSERT INTO drafts VALUES (?,?,?) ON CONFLICT(session_id,user_id) DO UPDATE SET selected=excluded.selected",
                        (sid, uid, json.dumps(sorted(selected))))

    def save_answer(self, sid: int, uid: int, selected: set[int], explicit_none: bool = False):
        self.open_for_answer(sid, uid)
        view = self.view(sid)
        valid = {slot.id for slot in view.slots}
        if not selected <= valid or bool(selected) == explicit_none:
            raise RuleError("Выберите интервалы или явно нажмите «Ни один вариант не подходит».")
        self.db.execute("INSERT INTO answers VALUES (?,?,?,?) ON CONFLICT(session_id,user_id) DO UPDATE SET explicit_none=excluded.explicit_none,updated_at=excluded.updated_at",
                        (sid, uid, int(explicit_none), self.now()))
        self.db.execute("DELETE FROM availability WHERE session_id=? AND user_id=?", (sid, uid))
        for slot_id in sorted(selected):
            self.db.execute("INSERT INTO availability VALUES (?,?,?)", (sid, uid, slot_id))
        self.set_selection(sid, uid, selected)
        self.db.refresh(sid, "progress", self.now())
        if not self.view(sid).missing:
            message = {"chat_id": self.session(sid)["organizer_id"],
                       "text": f"Все ответили на подбор #{sid}. Посмотрите общие варианты в приложении." if self.config.webapp_url else f"Все ответили на подбор #{sid}. Пересечения: /results. Ответы остаются изменяемыми до /close или срока."}
            if self.config.webapp_url:
                message["reply_markup"] = self.web_button(sid=sid, screen="results")
            self.db.enqueue("message", message,
                            self.now(), f"all-answered:{sid}")

    def close_round(self, sid: int):
        row = self.session(sid)
        if row["state"] != "open":
            raise RuleError("Сбор уже закрыт.")
        self.db.execute("UPDATE sessions SET state='closed',results_visible=1 WHERE id=?", (sid,))
        self.db.refresh(sid, "progress", self.now())
        if self.config.webapp_url:
            self.say(row["organizer_id"], f"Сбор #{sid} закрыт. Выберите варианты голосования в приложении.", self.web_button(sid=sid, screen="results"))
        else:
            self.say(row["organizer_id"], views.result_text(self.view(sid), True), views.organizer_keyboard(self.view(sid)))

    def start_vote(self, sid: int, uid: int, allow_partial: bool = False) -> bool:
        row, view = self.session(sid), self.view(sid)
        self.organizer(uid, row["group_id"])
        if row["state"] != "closed":
            raise RuleError("Сначала закройте сбор: /close. Затем выберите варианты в /vote.")
        if not view.nominations:
            raise RuleError("Сначала отметьте от одного до трёх вариантов для голосования.")
        candidates = {c.slot.id: c for c in view.candidates}
        if any(candidates[slot_id].slot.starts_at is not None and candidates[slot_id].slot.starts_at <= self.now() for slot_id in view.nominations):
            raise RuleError("Некоторые варианты уже прошли. Создайте новый подбор с будущими датами.")
        partial = any(not candidates[sid].common for sid in view.nominations)
        if partial and not allow_partial:
            selected_labels = "\n".join(candidates[slot_id].slot.label for slot_id in view.nominations)
            snapshot = ",".join(map(str, view.nominations))
            self.say(uid, "Выбранные варианты не подтверждены всеми: есть отказы или отсутствующие ответы.\n" + selected_labels + "\n"
                     "Запустить голосование можно только по вашему явному решению. Альтернатива — /repeat и более широкий диапазон.",
                     views.keyboard([[views.button("Согласен: голосовать за частичные варианты", f"permit:{sid}:{snapshot}")]]))
            return False
        self.db.execute("UPDATE sessions SET state='voting',partial_approved=? WHERE id=?", (int(partial), sid))
        self.db.refresh(sid, "vote", self.now())
        self.db.refresh(sid, "progress", self.now())
        if self.config.webapp_url:
            self.say(uid, "Финальное голосование запущено. Выбрать и подтвердить итог можно в приложении.", self.web_button(sid=sid, screen="results"))
        else:
            self.say(uid, "Финальное голосование запущено в группе. После голосов откройте /confirm. При ничьей выберите итоговый вариант.")
        return True

    def nominate(self, sid: int, uid: int, selected: list[int]):
        view = self.view(sid)
        self.organizer(uid, view.group_id)
        if view.state != "closed":
            raise RuleError("Варианты можно выбирать только после закрытия сбора.")
        if len(set(selected)) > 3 or not set(selected) <= {c.slot.id for c in view.top}:
            raise RuleError("Выберите до трёх предложенных вариантов.")
        self.db.execute("UPDATE sessions SET nominations=?,partial_approved=0 WHERE id=?", (json.dumps(sorted(set(selected))), sid))

    def web_button(self, label: str = "Открыть приложение", sid: int | None = None, screen: str = "", group_id: int | None = None, meeting_id: int | None = None) -> dict:
        params = {**({"round": sid} if sid else {}), **({"group": group_id} if group_id else {}),
                  **({"meeting": meeting_id} if meeting_id else {}), **({"open": screen} if screen else {})}
        suffix = "?" + urlencode(params) if params else ""
        return views.keyboard([[{"text": label, "web_app": {"url": self.config.webapp_url + "/" + suffix}}]])

    def app_link(self, sid: int | None = None, screen: str = "", group_id: int | None = None, meeting_id: int | None = None) -> str:
        if self.config.webapp_direct:
            target = f"round_{sid}" if sid else f"meeting_{meeting_id}" if meeting_id else f"group_{abs(group_id)}" if group_id else "app"
            if screen:
                target += "_" + screen
            return f"https://t.me/{self.username}?startapp={target}"
        target = f"availability_{sid}" if sid else f"meeting_{meeting_id}" if meeting_id else f"group_{abs(group_id)}" if group_id else "app"
        return f"https://t.me/{self.username}?start={target}"

    def group_button(self, label: str = "Открыть приложение", sid: int | None = None, screen: str = "", group_id: int | None = None, meeting_id: int | None = None) -> dict:
        return views.keyboard([[{"text": label, "url": self.app_link(sid, screen, group_id, meeting_id)}]])

    def group_command(self, command: str, anonymous: bool, group_id: int | None = None) -> bool:
        """Public entry points never infer an organizer identity from sender_chat."""
        entries = {"/app", "/start", "/help", "/settings", "/new", "/repeat",
                   "/results", "/vote", "/confirm", "/answers", "/join", "/status", "/schedule"}
        if anonymous:
            entries |= {"/close", "/cancel", "/whoami"}
        if command not in entries:
            return False
        gid = self.config.group_id if group_id is None else group_id
        self.group(gid)
        row = self.db.one("SELECT id FROM sessions WHERE group_id=? ORDER BY id DESC LIMIT 1", (gid,))
        sid = row["id"] if row else None
        screen = "create" if command in ("/new", "/repeat") else "results" if command in ("/results", "/vote", "/confirm", "/answers", "/close") else ""
        meeting_count = self.db.one("SELECT COUNT(*) FROM meetings WHERE group_id=?", (gid,))[0]
        if command == "/repeat" or (meeting_count > 1 and command != "/new"):
            screen = "meetings"
        if command == "/whoami":
            text = (f"ID группы: <code>{gid}</code>\n"
                    "Сообщение отправлено от имени группы. Ваш личный ID здесь не виден — откройте приложение от своего имени.")
        elif command == "/schedule":
            schedules = self.db.all("SELECT sc.*,m.title FROM schedules sc JOIN meetings m ON m.id=sc.meeting_id WHERE sc.group_id=? ORDER BY m.id", (gid,))
            text = "\n\n".join(f"<b>{escape(schedule['title'])}</b>\n" + views.schedule_text(schedule["day"], schedule["start"], schedule["duration"], schedule["date"]) for schedule in schedules) if schedules else "Время встречи ещё не выбрано. Текущий этап — в приложении."
        elif command in ("/new", "/repeat", "/close", "/cancel", "/answers"):
            text = "Управление подбором — в приложении. Telegram определит ваш личный аккаунт; настройки доступны только организатору."
        elif sid and meeting_count == 1:
            text = views.app_progress_text(self.view(sid))
        else:
            text = f"<b>{escape(self.group(gid)['title'])} · встречи</b>\nВсе встречи группы — в приложении. Для каждой отдельно выбираем участников, время и расписание."
        use_sid = sid if meeting_count == 1 and command not in ("/app", "/start", "/help", "/settings", "/new", "/repeat", "/schedule") else None
        self.say(gid, text, self.group_button(sid=use_sid, screen=screen, group_id=gid))
        return True

    def cast_vote(self, sid: int, uid: int, slot_id: int):
        row = self.session(sid)
        self.group(row["group_id"])
        self.expected(sid, uid)
        if row["state"] != "voting" or slot_id not in json.loads(row["nominations"]):
            raise RuleError("Это голосование закрыто или вариант не включён в него.")
        slot = next(slot for slot in self.view(sid).slots if slot.id == slot_id)
        if slot.starts_at is not None and slot.starts_at <= self.now():
            raise RuleError("Этот вариант уже прошёл. Выберите будущую дату или попросите новый подбор.")
        self.db.execute("INSERT INTO votes VALUES (?,?,?) ON CONFLICT(session_id,user_id) DO UPDATE SET slot_id=excluded.slot_id", (sid, uid, slot_id))
        self.db.refresh(sid, "vote", self.now())
        if self.config.webapp_url:
            self.db.refresh(sid, "progress", self.now())
        view = self.view(sid)
        if len(view.votes) == len(view.names):
            message = {"chat_id": row["organizer_id"], "text": f"Все проголосовали в подборе #{sid}. Подтвердите время в приложении." if self.config.webapp_url else f"Все проголосовали в подборе #{sid}. Подтвердите результат: /confirm."}
            if self.config.webapp_url:
                message["reply_markup"] = self.web_button(sid=sid, screen="results")
            self.db.enqueue("message", message,
                            self.now(), f"all-voted:{sid}")

    def confirm(self, sid: int, uid: int, slot_id: int):
        row, view = self.session(sid), self.view(sid)
        self.organizer(uid, row["group_id"])
        if row["state"] != "voting" or not view.votes:
            raise RuleError("Нужно открытое голосование хотя бы с одним голосом.")
        counts = {candidate: list(view.votes.values()).count(candidate) for candidate in view.nominations}
        if slot_id not in counts or counts[slot_id] != max(counts.values()):
            raise RuleError("Голоса изменились. Откройте /confirm и выберите одного из текущих лидеров.")
        slot = next(slot for slot in view.slots if slot.id == slot_id)
        if slot.starts_at is not None and slot.starts_at <= self.now():
            raise RuleError("Этот вариант уже прошёл. Выберите будущую дату или создайте новый подбор.")
        self.db.execute("UPDATE sessions SET state='final',chosen_slot=? WHERE id=?", (slot_id, sid))
        self.db.execute("INSERT INTO schedules(meeting_id,group_id,session_id,day,start,duration,confirmed_at,mode,date) VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(meeting_id) DO UPDATE SET session_id=excluded.session_id,day=excluded.day,start=excluded.start,duration=excluded.duration,confirmed_at=excluded.confirmed_at,mode=excluded.mode,date=excluded.date",
                        (row["meeting_id"], row["group_id"], sid, slot.day, slot.start, slot.duration, self.now(), row["mode"], slot.date))
        text = f"<b>{escape(row['title'])}</b>\n" + views.schedule_text(slot.day, slot.start, slot.duration, slot.date)
        self.db.enqueue("message", {"chat_id": row["group_id"], "text": text, "parse_mode": "HTML"}, self.now(), f"final:{sid}")
        self.db.refresh(sid, "vote", self.now())
        self.db.refresh(sid, "progress", self.now())
        if self.config.webapp_url:
            self.say(uid, "Расписание сохранено. Итог отправляется в группу.", self.web_button(sid=sid, screen="results"))
        else:
            self.say(uid, "Расписание сохранено и поставлено в очередь публикации в группе. Проверить: /schedule. Новый подбор: /repeat.")

    def tick(self):
        if self.discovery:
            return
        with self.db.transaction():
            for row in self.db.all("SELECT s.* FROM sessions s JOIN groups g ON g.id=s.group_id WHERE s.state='open' AND g.active=1"):
                sid = row["id"]
                if self.now() >= row["deadline"]:
                    self.close_round(sid)
                elif self.now() >= row["reminder_at"] and not row["reminder_queued"]:
                    self.db.execute("UPDATE sessions SET reminder_queued=1 WHERE id=?", (sid,))
                    self.db.enqueue("reminder", {"session_id": sid}, self.now(), f"reminder:{sid}")

    def message(self, message: dict):
        user = message.get("from")
        chat_id = message["chat"]["id"]
        sender_chat = message.get("sender_chat")
        anonymous = bool(sender_chat)
        if anonymous:
            if (self.discovery or chat_id >= 0 or
                    sender_chat.get("id") != chat_id or message.get("is_automatic_forward")):
                return
        elif not user or user.get("is_bot"):
            return
        uid = user["id"] if not anonymous else 0
        private = message["chat"]["type"] == "private" and chat_id == uid
        text = message.get("text", "").strip()
        first, _, args = text.partition(" ")
        command, _, addressed_to = first.partition("@")
        if addressed_to and addressed_to.casefold() != self.username.casefold():
            return
        command = command.casefold()
        if self.discovery:
            if anonymous:
                return
            shared = message.get("chat_shared")
            if private and shared and shared.get("request_id") == 402 and shared.get("chat_id", 0) < 0:
                if self.config.organizers:
                    if uid not in self.config.organizers:
                        raise RuleError("Эта команда доступна только организатору.")
                selection = {"user_id": uid, "chat_id": shared["chat_id"],
                             "title": shared.get("title", ""), "selected_at": self.now()}
                self.db.execute("INSERT INTO metadata VALUES ('setup_group',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                                (json.dumps(selection, ensure_ascii=False),))
                self.say(uid, f"Выбрана группа: {escape(shared.get('title', ''))}\nID группы: <code>{shared['chat_id']}</code>\n"
                         "Выбор сохранён для завершения настройки. Пока подборы не запускаются.", {"remove_keyboard": True})
            elif command in ("/whoami", "/start", "/group"):
                markup = None
                if private:
                    markup = {"keyboard": [[{"text": "Выбрать группу", "request_chat": {
                        "request_id": 402, "chat_is_channel": False, "bot_is_member": True, "request_title": True}}]],
                        "resize_keyboard": True, "one_time_keyboard": True}
                self.say(chat_id, f"Ваш Telegram ID: <code>{uid}</code>\nID чата: <code>{chat_id}</code>\n"
                         "Режим настройки. В личном чате нажмите «Выбрать группу». Если группы нет в списке, сначала добавьте в неё бота. Подборы пока не запускаются.", markup)
            return
        if not private:
            if chat_id >= 0 or message["chat"]["type"] not in ("group", "supergroup"):
                return
            known = self.db.one("SELECT 1 FROM groups WHERE id=? AND active=1", (chat_id,))
            connecting = command in ("/connect", "/group") or (command == "/start" and args == "connect")
            if connecting and not anonymous:
                self.remember(user)
                self.queue_group_connection(uid, chat_id, chat_id)
                return
            if connecting and anonymous:
                self.say(chat_id, "Для подключения группы откройте личный чат с ботом: там Telegram определит ваш аккаунт администратора.",
                         views.keyboard([[{"text": "Подключить группу", "url": f"https://t.me/{self.username}?start=connect"}]]))
                return
            if not known:
                if command == "/whoami":
                    text = f"ID чата: <code>{chat_id}</code>" + ("\nСообщение отправлено от имени группы." if anonymous else f"\nВаш Telegram ID: <code>{uid}</code>")
                    self.say(chat_id, text)
                    return
                if text.startswith("/") and command in ("/app", "/start", "/connect", "/group", "/help", "/new"):
                    self.say(chat_id, "Подключите эту группу: администратор открывает личный чат с ботом и выбирает группу.",
                             views.keyboard([[{"text": "Подключить группу", "url": f"https://t.me/{self.username}?start=connect"}]]))
                return
            if not anonymous:
                self.remember(user)
                self.db.execute("INSERT OR IGNORE INTO group_members VALUES (?,?)", (chat_id, uid))
            if self.config.webapp_url and self.group_command(command, anonymous, chat_id):
                return
            if anonymous:
                return
        else:
            shared = message.get("chat_shared")
            if shared:
                request_id = shared.get("request_id")
                key = f"group-request:{uid}:{request_id}"
                pending = self.db.one("SELECT value FROM metadata WHERE key=?", (key,))
                if not pending or float(pending[0]) < self.now() or type(shared.get("chat_id")) is not int or shared["chat_id"] >= 0:
                    raise RuleError("Этот выбор группы устарел. Откройте «Добавить группу» заново.")
                self.db.execute("DELETE FROM metadata WHERE key=?", (key,))
                self.remember(user)
                self.queue_group_connection(uid, shared["chat_id"])
                self.say(uid, "Проверяю группу и ваши права администратора…", {"remove_keyboard": True})
                return
            if command in ("/connect", "/group") or (command == "/start" and args == "connect"):
                self.remember(user)
                self.request_group(uid)
                return
        if not text.startswith("/"):
            if private and uid in self.config.organizers and self.db.one("SELECT 1 FROM wizards WHERE user_id=?", (uid,)):
                self.wizard_step(uid, message)
            return
        self.remember(user)
        if private and self.config.webapp_url and (
            command in ("/start", "/app", "/help", "/settings", "/new", "/repeat", "/results", "/vote", "/confirm", "/answers")
        ):
            sid, gid, mid = None, None, None
            match = re.fullmatch(r"availability_(\d+)", args) if command == "/start" else None
            if match:
                sid = int(match[1])
                row = self.session(sid)
                if not self.is_organizer(uid, row["group_id"]):
                    self.expected(sid, uid)
            elif command == "/start" and re.fullmatch(r"group_\d+", args):
                gid = -int(args[6:])
            elif command == "/start" and re.fullmatch(r"meeting_\d+", args):
                mid = int(args[8:])
            screen = "create" if command in ("/new", "/repeat") else ("results" if command in ("/results", "/vote", "/confirm", "/answers") else "")
            if command == "/repeat":
                screen = "meetings"
            self.say(uid, "<b>Найдём время для встречи</b>\nВыберите удобные интервалы в приложении. Здесь же — ответы, результаты и голосование.",
                     self.web_button(sid=sid, screen=screen, group_id=gid, meeting_id=mid))
            return
        if command in ("/help", "/settings") or (command == "/start" and not args):
            self.say(chat_id, HELP)
        elif command == "/whoami":
            self.say(chat_id, f"Ваш Telegram ID: <code>{uid}</code>\nID чата: <code>{chat_id}</code>")
        elif command == "/join":
            self.say(chat_id, "Вы зарегистрированы. Организатор сможет добавить вас по @имени или ID. Для ответа используйте кнопку «Выбрать время» под подбором.")
        elif command == "/start" and private:
            match = re.fullmatch(r"availability_(\d+)", args)
            if not match:
                raise RuleError("Неизвестная ссылка. Откройте кнопку текущего подбора в группе.")
            sid = int(match[1])
            self.open_for_answer(sid, uid)
            body, markup = views.availability_view(self.view(sid), self.selection(sid, uid))
            self.say(uid, body, markup)
        elif command in ("/new", "/repeat"):
            self.private_organizer(uid, chat_id)
            self.start_wizard(uid, repeat=command == "/repeat")
        elif command == "/cancel":
            self.private_organizer(uid, chat_id)
            self.db.execute("DELETE FROM wizards WHERE user_id=?", (uid,))
            self.say(uid, "Создание подбора отменено.", {"remove_keyboard": True})
        elif command in ("/results", "/answers", "/vote", "/confirm"):
            self.private_organizer(uid, chat_id)
            row = self.latest()
            view = self.view(row["id"])
            if command == "/confirm":
                if row["state"] != "voting":
                    raise RuleError("Открытого финального голосования пока нет: /vote.")
                body, markup = views.decision_view(view)
                self.say(uid, body, markup)
            elif command == "/answers":
                self.show_answers(uid, view)
            else:
                self.db.execute("UPDATE sessions SET results_visible=1 WHERE id=?", (row["id"],))
                self.db.refresh(row["id"], "progress", self.now())
                self.say(uid, views.result_text(view, True), views.organizer_keyboard(view))
        elif command == "/close":
            row = self.latest(group_id=chat_id if not private else None)
            self.organizer(uid, row["group_id"])
            if self.db.one("SELECT COUNT(*) FROM meetings WHERE group_id=?", (row["group_id"],))[0] > 1:
                raise RuleError("В группе несколько встреч. Выберите нужную встречу в приложении.")
            self.close_round(row["id"])
            if not private:
                self.say(chat_id, "Сбор закрыт. Результаты обновлены, подробности отправлены организатору.")
        elif command in ("/status", "/schedule"):
            row = self.latest()
            if private and uid not in self.config.organizers:
                self.expected(row["id"], uid)
            if command == "/status":
                self.say(chat_id, views.progress_text(self.view(row["id"])))
            else:
                schedule = self.db.one("SELECT * FROM schedules WHERE group_id=?", (self.config.group_id,))
                if not schedule:
                    raise RuleError("Постоянное расписание ещё не выбрано.")
                self.say(chat_id, views.schedule_text(schedule["day"], schedule["start"], schedule["duration"], schedule["date"]))
        else:
            self.say(chat_id, "Неизвестная команда. Список: /help.")

    def callback(self, query: dict):
        uid = query["from"]["id"]
        message = query.get("message", {})
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        if chat_id != uid and not self.db.one("SELECT 1 FROM groups WHERE id=? AND active=1", (chat_id,)):
            raise RuleError("Кнопка недоступна в этом чате.")
        data = query.get("data", "")
        parts = data.split(":")
        action = parts[0]
        if action == "publish" and len(parts) == 2:
            self.private_organizer(uid, chat_id)
            self.publish_wizard(uid, parts[1])
        elif action in ("toggle", "page", "save", "none"):
            if chat_id != uid or not all(p.isdecimal() for p in parts[1:]):
                raise RuleError("Выбор доступности доступен только в личном чате.")
            expected_length = 4 if action == "toggle" else 3
            if len(parts) != expected_length:
                raise RuleError("Некорректная кнопка.")
            sid = int(parts[1])
            self.open_for_answer(sid, uid)
            page = int(parts[-1])
            selected = self.selection(sid, uid)
            if action == "toggle":
                slot_id = int(parts[2])
                if slot_id not in {s.id for s in self.view(sid).slots}:
                    raise RuleError("Вариант не найден.")
                selected.symmetric_difference_update({slot_id})
                self.set_selection(sid, uid, selected)
            elif action in ("save", "none"):
                if action == "none":
                    selected = set()
                self.save_answer(sid, uid, selected, explicit_none=action == "none")
            body, markup = views.availability_view(self.view(sid), selected, page)
            if action in ("save", "none"):
                body = ("✅ Ответ сохранён: ни один вариант не подходит.\n\n" if action == "none" else "✅ Ответ сохранён.\n\n") + body
            self.edit(uid, message["message_id"], body, markup)
        elif action in ("close", "nominate", "launch", "permit", "confirm"):
            expected_length = 3 if action in ("nominate", "confirm", "permit") else 2
            if len(parts) != expected_length or not parts[1].isdecimal() or (action != "permit" and not all(p.isdecimal() for p in parts[1:])):
                raise RuleError("Некорректная кнопка.")
            sid = int(parts[1])
            row = self.session(sid)
            self.private_organizer(uid, chat_id, row["group_id"])
            if action == "close":
                self.close_round(sid)
            elif action == "nominate":
                if row["state"] != "closed":
                    raise RuleError("Варианты можно выбирать только после закрытия сбора.")
                slot_id = int(parts[2])
                view = self.view(sid)
                if slot_id not in {c.slot.id for c in view.top}:
                    raise RuleError("Выберите один из предложенных вариантов.")
                selected = set(view.nominations)
                selected.symmetric_difference_update({slot_id})
                self.nominate(sid, uid, list(selected))
                view = self.view(sid)
                self.edit(uid, message["message_id"], views.result_text(view), views.organizer_keyboard(view))
            elif action in ("launch", "permit"):
                if action == "permit" and parts[2] != ",".join(map(str, self.view(sid).nominations)):
                    raise RuleError("Варианты изменились. Откройте /vote и подтвердите текущий список заново.")
                self.start_vote(sid, uid, allow_partial=action == "permit")
            else:
                self.confirm(sid, uid, int(parts[2]))
        elif action == "vote" and len(parts) == 3 and all(p.isdecimal() for p in parts[1:]):
            sid, slot_id = int(parts[1]), int(parts[2])
            if chat_id != self.session(sid)["group_id"]:
                raise RuleError("Голосуйте в сообщении финального голосования в группе.")
            self.cast_vote(sid, uid, slot_id)
        else:
            raise RuleError("Эта кнопка устарела или недоступна.")
        self.answer_callback(query["id"], "Сохранено" if action in ("vote", "save", "none", "confirm") else "")

    def show_answers(self, uid: int, view: views.RoundView):
        lines = [f"<b>Ответы · #{view.id}</b>"]
        for participant, name in view.names.items():
            if participant not in view.responses:
                value = "нет ответа"
            elif not view.responses[participant]:
                value = "явно: ни один вариант не подходит"
            else:
                value = "варианты №" + ", №".join(map(str, sorted(view.responses[participant])))
            lines.append(f"{escape(name)}: {value}")
        lines.append("\nОбозначения вариантов (по Праге):")
        lines.extend(f"№{slot.id}: {slot.label}" for slot in view.slots)
        self.say(uid, "\n".join(lines))

    def start_wizard(self, uid: int, repeat: bool = False):
        data, step = {}, "participants"
        if repeat:
            row = self.latest()
            if row["mode"] == "once":
                raise RuleError("Для новых дат разовой встречи откройте её в приложении.")
            view = self.view(row["id"])
            data = {"participants": [{"id": person, "name": name} for person, name in view.names.items()],
                    "duration": row["duration"], "windows": row["windows"]}
            step = "windows"
        token = secrets.token_hex(4)
        self.db.execute("INSERT INTO wizards VALUES (?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET token=excluded.token,step=excluded.step,data=excluded.data",
                        (uid, token, step, json.dumps(data, ensure_ascii=False)))
        self.wizard_prompt(uid)

    def wizard_prompt(self, uid: int):
        row = self.db.one("SELECT * FROM wizards WHERE user_id=?", (uid,))
        step, data = row["step"], json.loads(row["data"])
        if step == "participants":
            markup = {"keyboard": [[{"text": "Выбрать участников", "request_users": {
                "request_id": int(row["token"], 16) % 2147483647, "user_is_bot": False,
                "max_quantity": 10, "request_name": True, "request_username": True}}]],
                "resize_keyboard": True, "one_time_keyboard": True}
            self.say(uid, "<b>1/4. Ожидаемые участники</b>\nНажмите кнопку (до 10 человек) или отправьте список (до 30):\n"
                     "<code>123456:Анна; 234567:Борис</code>\n"
                     "Можно использовать @имя, если человек уже отправил боту /join или /start. Включите себя, если ваш ответ тоже нужен.\nОтмена: /cancel.", markup)
        elif step == "duration":
            self.say(uid, "<b>2/4. Длительность</b>\nВведите минуты, например 60. Для 1 часа по умолчанию отправьте «-».\nДопустимо 30–480 минут с шагом 30.", {"remove_keyboard": True})
        elif step == "windows":
            old = f"\nПрежние диапазоны: {escape(data['windows'])}. Для сохранения отправьте «-»." if "windows" in data else ""
            self.say(uid, "<b>3/4. Дни и диапазоны</b>\nНапример:\n<code>вт 18:00-21:00; ср 18:00-21:00</code>\n"
                     "Можно: <code>вт,чт 18:00-21:00</code>. Встреча целиком должна помещаться в диапазон одного дня. Все часы по Праге." + old)
        elif step == "deadline":
            self.say(uid, "<b>4/4. Срок ответа</b>\nВведите дату и время по Праге: <code>ДД.ММ.ГГГГ ЧЧ:ММ</code>.\n"
                     "Один раз перед сроком бот напомнит в группе тем, кто не ответил. В срок сбор закроется автоматически.")
        else:
            self.say(uid, "<b>Проверьте подбор</b>\nУчастники: " + ", ".join(escape(p["name"]) for p in data["participants"]) +
                     f"\nДлительность: {data['duration']} мин. Вариантов: {len(parse_windows(data['windows'], data['duration']))}." +
                     f"\nДиапазоны: {escape(data['windows'])}\nСрок: {deadline_label(data['deadline'])}\n"
                     "Публикация заменит предыдущий незавершённый подбор; его ответы сохранятся в архиве. Выбранное ранее расписание действует до нового подтверждения.",
                     views.keyboard([[views.button("Опубликовать в группе", f"publish:{row['token']}")]]))

    def parse_participants(self, text: str, group_id: int | None = None) -> list[dict]:
        gid = self.config.group_id if group_id is None else group_id
        participants = []
        for item in re.split(r"[;,\n]", text):
            item = item.strip()
            if not item:
                continue
            if item.startswith("@"):
                row = self.db.one("SELECT u.* FROM users u JOIN group_members gm ON gm.user_id=u.user_id WHERE gm.group_id=? AND u.username=?", (gid, item[1:].casefold()))
                if not row:
                    raise RuleError(f"{item} пока неизвестен боту. Попросите отправить /join или укажите числовой ID.")
                participants.append({"id": row["user_id"], "name": row["name"]})
            else:
                match = re.fullmatch(r"(\d+)(?:\s*[: ]\s*(.+))?", item)
                if not match or int(match[1]) <= 0:
                    raise RuleError("Участники: 123456:Анна; 234567:Борис или известные боту @имена.")
                person = int(match[1])
                known = self.db.one("SELECT u.name FROM users u JOIN group_members gm ON gm.user_id=u.user_id WHERE gm.group_id=? AND u.user_id=?", (gid, person))
                participants.append({"id": person, "name": " ".join((match[2] or (known[0] if known else str(person))).split())[:48]})
        return self.validate_participants(participants)

    def validate_participants(self, participants: list[dict]) -> list[dict]:
        unique = {p["id"]: p for p in participants if p["id"] > 0}
        if not 1 <= len(unique) <= 30:
            raise RuleError("Укажите от 1 до 30 участников.")
        return list(unique.values())

    def wizard_step(self, uid: int, message: dict):
        row = self.db.one("SELECT * FROM wizards WHERE user_id=?", (uid,))
        data, step = json.loads(row["data"]), row["step"]
        text = message.get("text", "").strip()
        shared = message.get("users_shared")
        if step == "participants":
            if shared:
                if shared.get("request_id") != int(row["token"], 16) % 2147483647:
                    raise RuleError("Это выбор из прежнего создания. Используйте текущую кнопку.")
                people = [{"id": p["user_id"], "name": (" ".join(filter(None, [p.get("first_name"), p.get("last_name")])) or str(p["user_id"]))[:48]}
                          for p in shared.get("users", [])]
                data["participants"] = self.validate_participants(people)
            else:
                data["participants"] = self.parse_participants(text)
            next_step = "duration"
        elif step == "duration":
            data["duration"] = parse_duration(text)
            next_step = "windows"
        elif step == "windows":
            text = data.get("windows", "") if text == "-" else text
            parse_windows(text, data["duration"])
            data["windows"] = text
            next_step = "deadline"
        elif step == "deadline":
            data["deadline"] = parse_deadline(text, self.now())
            next_step = "preview"
        else:
            raise RuleError("Подбор готов к публикации. Нажмите «Опубликовать в группе» или /cancel.")
        self.db.execute("UPDATE wizards SET step=?,data=? WHERE user_id=?", (next_step, json.dumps(data, ensure_ascii=False), uid))
        self.wizard_prompt(uid)

    def publish_wizard(self, uid: int, token: str):
        row = self.db.one("SELECT * FROM wizards WHERE user_id=? AND token=? AND step='preview'", (uid, token))
        if not row:
            raise RuleError("Это создание уже опубликовано, отменено или заменено новым.")
        data = json.loads(row["data"])
        if data["deadline"] <= self.now():
            raise RuleError("Срок уже прошёл. Начните заново: /new.")
        self.create_round(uid, data["participants"], data["duration"], data["windows"], data["deadline"])
        self.db.execute("DELETE FROM wizards WHERE user_id=?", (uid,))
        self.say(uid, "Подбор создан и поставлен в очередь публикации в группе. Прогресс: /status, результаты: /results, закрыть: /close.", {"remove_keyboard": True})

    def create_round(self, uid: int, people: list[dict], duration: int, windows: str, deadline: float,
                     group_id: int | None = None, meeting_id: int | None = None, title: str = "Еженедельная встреча", new_meeting: bool = False, mode: str = "weekly") -> int:
        gid = self.config.group_id if group_id is None else group_id
        self.organizer(uid, gid)
        people = self.validate_participants(people)
        slots = parse_windows(windows, duration, mode=mode, now=self.now())
        if deadline <= self.now():
            raise RuleError("Срок должен быть в будущем.")
        if mode == "once" and deadline >= min(slot.starts_at for slot in slots):
            raise RuleError("Срок ответа должен быть раньше первого предложенного времени встречи.")
        if meeting_id is not None:
            meeting = self.meeting(meeting_id)
            if meeting["group_id"] != gid:
                raise RuleError("Эта встреча находится в другой группе.")
            if meeting["mode"] != mode:
                raise RuleError("Тип существующей встречи нельзя изменить. Создайте отдельную встречу.")
        else:
            existing = None if new_meeting else self.db.one("SELECT id,mode FROM meetings WHERE group_id=? ORDER BY id LIMIT 1", (gid,))
            if existing:
                if existing["mode"] != mode:
                    raise RuleError("Тип существующей встречи нельзя изменить. Создайте отдельную встречу.")
                meeting_id = existing["id"]
            else:
                title = " ".join(title.split()) if isinstance(title, str) else ""
                if not 1 <= len(title) <= 80:
                    raise RuleError("Укажите название встречи от 1 до 80 символов.")
                meeting_id = self.db.execute("INSERT INTO meetings(group_id,title,created_by,created_at,mode) VALUES (?,?,?,?,?)", (gid, title, uid, self.now(), mode)).lastrowid
        for old in self.db.all("SELECT id,state FROM sessions WHERE meeting_id=? AND state IN ('open','closed','voting')", (meeting_id,)):
            self.db.execute("UPDATE sessions SET state='cancelled' WHERE id=?", (old["id"],))
            self.db.refresh(old["id"], "progress", self.now())
            if old["state"] == "voting":
                self.db.refresh(old["id"], "vote", self.now())
        lead = min(self.config.reminder_minutes * 60, (deadline - self.now()) / 2)
        cursor = self.db.execute("INSERT INTO sessions(group_id,organizer_id,state,duration,windows,deadline,reminder_at,created_at,meeting_id,mode) VALUES (?,?,'open',?,?,?,?,?,?,?)",
                                 (gid, uid, duration, windows, deadline, deadline - lead, self.now(), meeting_id, mode))
        sid = cursor.lastrowid
        for person in people:
            self.db.execute("INSERT INTO participants VALUES (?,?,?)", (sid, person["id"], person["name"]))
            self.db.execute("INSERT OR IGNORE INTO group_members VALUES (?,?)", (gid, person["id"]))
        for slot in slots:
            self.db.execute("INSERT INTO slots(session_id,slot_id,day,start,date) VALUES (?,?,?,?,?)", (sid, slot.id, slot.day, slot.start, slot.date))
        self.db.refresh(sid, "progress", self.now())
        return sid
