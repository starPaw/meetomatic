import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from bot_calendar.config import Config
from bot_calendar.domain import RuleError
from bot_calendar.service import Application
from bot_calendar.storage import Database, SCHEMA
from bot_calendar.telegram import Delivery
from bot_calendar.web import act, state_for


class FakeTelegram:
    def __init__(self, admin=20):
        self.admin = admin
        self.calls = []
        self.counter = 100

    def call(self, method, **body):
        self.calls.append((method, dict(body)))
        if method == "getChat":
            return {"id": body["chat_id"], "type": "supergroup", "title": "Новая группа"}
        if method == "getChatMember":
            return {"status": "member"}
        if method == "getChatAdministrators":
            return [{"status": "creator", "user": {"id": self.admin}}]
        self.counter += 1
        return {"message_id": self.counter}


class GroupWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / "bot.sqlite3")
        self.config = Config("123:offline", frozenset({1}), -100, self.path,
                             webapp_url="https://meeting.example", webapp_direct=True)
        self.db = Database(self.path)
        self.time = 1792670000.0
        self.app = Application(self.config, self.db, "meeting_bot", now=lambda: self.time)
        with self.db.transaction():
            for uid, name in [(1, "Организатор A"), (2, "Анна"), (3, "Борис"), (10, "Организатор C"), (11, "Катя"), (99, "Посторонний")]:
                self.app.remember({"id": uid, "first_name": name, "username": f"person{uid}"})
            self.app.connect_group(-200, "Другая группа", 10)
            self.a = self.app.create_round(1, [{"id": 2, "name": "Анна"}, {"id": 3, "name": "Борис"}], 60, "ср 18:00-20:00", self.time + 7200, title="Завтрак", new_meeting=True)
            self.b = self.app.create_round(1, [{"id": 2, "name": "Анна"}], 60, "чт 18:00-20:00", self.time + 7200, title="Книжный клуб", new_meeting=True)
            self.c = self.app.create_round(10, [{"id": 11, "name": "Катя"}], 60, "пт 18:00-20:00", self.time + 7200, group_id=-200, title="Прогулка", new_meeting=True)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def action(self, uid, sid, action, **body):
        with self.db.transaction():
            return act(self.app, {"id": uid}, {"action": action, "round": sid, **body})

    def finish(self, sid, uid):
        for participant in self.app.view(sid).names:
            self.action(participant, sid, "availability", slots=[1], none=False)
        self.action(uid, sid, "close")
        self.action(uid, sid, "start_vote", slots=[1])
        for participant in self.app.view(sid).names:
            self.action(participant, sid, "vote", slot=1)
        self.action(uid, sid, "confirm", slot=1)

    def test_multiple_live_meetings_do_not_replace_one_another(self):
        self.assertEqual([self.app.session(sid)["state"] for sid in (self.a, self.b, self.c)], ["open"] * 3)
        self.action(2, self.a, "availability", slots=[1], none=False)
        self.action(2, self.b, "availability", slots=[2], none=False)
        self.assertEqual(self.app.view(self.a).responses[2], {1})
        self.assertEqual(self.app.view(self.b).responses[2], {2})
        self.assertFalse(self.app.view(self.c).responses)

    def test_repeating_one_meeting_preserves_other_meetings_and_old_answers(self):
        self.action(2, self.a, "availability", slots=[1], none=False)
        mid = self.app.session(self.a)["meeting_id"]
        with self.db.transaction():
            replacement = self.app.create_round(1, [{"id": 2, "name": "Анна"}], 90, "ср 18:00-22:00", self.time + 9000, meeting_id=mid)
        self.assertEqual(self.app.session(self.a)["state"], "cancelled")
        self.assertEqual(self.app.view(self.a).responses[2], {1})
        self.assertEqual(self.app.session(replacement)["meeting_id"], mid)
        self.assertEqual([self.app.session(sid)["state"] for sid in (self.b, self.c)], ["open", "open"])

    def test_schedules_and_publications_belong_to_each_meeting_and_actual_group(self):
        self.finish(self.a, 1)
        self.finish(self.b, 1)
        self.finish(self.c, 10)
        self.assertEqual(self.db.one("SELECT COUNT(*) FROM schedules")[0], 3)
        self.assertEqual(self.db.one("SELECT COUNT(*) FROM schedules WHERE group_id=-100")[0], 2)
        for sid, gid, title in [(self.a, -100, "Завтрак"), (self.b, -100, "Книжный клуб"), (self.c, -200, "Прогулка")]:
            message = json.loads(self.db.one("SELECT payload FROM outbox WHERE dedupe_key=?", (f"final:{sid}",))[0])
            self.assertEqual(message["chat_id"], gid)
            self.assertIn(title, message["text"])
            self.assertIn("по Праге", message["text"])
        mid = self.app.session(self.a)["meeting_id"]
        with self.db.transaction():
            self.app.create_round(1, [{"id": 2, "name": "Анна"}], 60, "ср 18:00-20:00", self.time + 9000, meeting_id=mid)
        self.assertEqual(self.db.one("SELECT session_id FROM schedules WHERE meeting_id=?", (mid,))[0], self.a)

    def test_organizer_role_is_scoped_to_connected_group(self):
        for action, body in [("close", {}), ("start_vote", {"slots": [1]}), ("confirm", {"slot": 1})]:
            with self.subTest(action=action), self.assertRaises(RuleError):
                self.action(1, self.c, action, **body)
        with self.assertRaises(RuleError):
            self.action(2, self.c, "availability", slots=[1], none=False)
        self.assertEqual(self.app.session(self.c)["state"], "open")
        self.assertFalse(self.app.view(self.c).responses)
        self.assertFalse(self.app.is_organizer(1, -200))
        self.assertTrue(self.app.is_organizer(10, -200))

    def test_delete_finished_meeting_removes_all_rounds_and_preserves_other_meetings(self):
        self.finish(self.a, 1)
        mid = self.app.session(self.a)["meeting_id"]
        with self.db.transaction():
            replacement = self.app.create_round(1, [{"id": 2, "name": "Анна"}], 60,
                "ср 18:00-20:00", self.time + 9000, meeting_id=mid)
        self.finish(replacement, 1)
        others = {sid: dict(self.app.session(sid)) for sid in (self.b, self.c)}
        self.action(1, replacement, "delete_meeting", group=-100, meeting=mid)
        for table in ("sessions", "schedules"):
            self.assertEqual(self.db.one(f"SELECT COUNT(*) FROM {table} WHERE meeting_id=?", (mid,))[0], 0)
        for table in ("participants", "slots", "answers", "availability", "drafts", "votes"):
            self.assertEqual(self.db.one(f"SELECT COUNT(*) FROM {table} WHERE session_id IN (?,?)", (self.a, replacement))[0], 0)
        self.assertIsNone(self.db.one("SELECT id FROM meetings WHERE id=?", (mid,)))
        self.assertEqual({sid: dict(self.app.session(sid)) for sid in others}, others)
        self.assertTrue(self.db.one("SELECT 1 FROM group_members WHERE group_id=-100 AND user_id=2"))
        self.assertEqual(self.db.all("PRAGMA foreign_key_check"), [])
        for sid in (self.a, replacement):
            self.assertIsNone(self.db.one("SELECT id FROM outbox WHERE dedupe_key=?", (f"final:{sid}",)))
            self.assertIsNone(self.db.one("SELECT id FROM outbox WHERE json_extract(payload,'$.session_id')=?", (sid,)))
            with self.assertRaises(RuleError):
                state_for(self.app, {"id": 1}, sid=sid)
        with self.assertRaises(RuleError):
            state_for(self.app, {"id": 1}, meeting_id=mid)
        self.action(1, replacement, "delete_meeting", group=-100, meeting=mid)
        another = Database(self.path, initialize=False)
        try:
            reopened = Application(self.config, another, "meeting_bot", now=lambda: self.time)
            self.assertEqual([m["title"] for m in state_for(reopened, {"id": 1}, group_id=-100)["meetings"]], ["Книжный клуб"])
        finally:
            another.close()

    def test_delete_requires_group_organizer_and_current_finished_round(self):
        mid = self.app.session(self.a)["meeting_id"]
        for state in ("open", "closed", "voting"):
            with self.db.transaction():
                self.db.execute("UPDATE sessions SET state=? WHERE id=?", (state, self.a))
            with self.subTest(state=state), self.assertRaises(RuleError):
                self.action(1, self.a, "delete_meeting", group=-100, meeting=mid)
        with self.db.transaction():
            self.db.execute("UPDATE sessions SET state='open' WHERE id=?", (self.a,))
        self.finish(self.a, 1)
        for uid, gid in ((2, -100), (10, -100), (1, -200), (10, -200)):
            with self.subTest(uid=uid, group=gid), self.assertRaises(RuleError):
                self.action(uid, self.a, "delete_meeting", group=gid, meeting=mid, user_id=1)
        with self.db.transaction():
            replacement = self.app.create_round(1, [{"id": 2, "name": "Анна"}], 60,
                "ср 18:00-20:00", self.time + 9000, meeting_id=mid)
        with self.assertRaises(RuleError):
            self.action(1, self.a, "delete_meeting", group=-100, meeting=mid)
        self.finish(replacement, 1)
        with self.assertRaises(RuleError):
            self.action(1, self.a, "delete_meeting", group=-100, meeting=mid)
        self.assertEqual(self.app.session(replacement)["state"], "final")

    def test_delete_rolls_back_everything_if_storage_fails(self):
        self.finish(self.a, 1)
        mid = self.app.session(self.a)["meeting_id"]
        before = list(self.db.connection.iterdump())
        self.db.execute("CREATE TEMP TRIGGER fail_delete BEFORE DELETE ON meetings BEGIN SELECT RAISE(ABORT,'test failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.action(1, self.a, "delete_meeting", group=-100, meeting=mid)
        self.assertEqual(list(self.db.connection.iterdump()), before)

    def test_deleted_creation_request_cannot_recreate_the_meeting(self):
        body = {"action": "create", "request_id": "22222222-2222-4222-8222-222222222222", "group": -100,
                "title": "Временная встреча", "participants": [{"id": 2, "name": "Анна"}],
                "duration": 60, "windows": "ср 18:00-20:00", "deadline": "2027-01-25T20:00"}
        with self.db.transaction():
            sid = act(self.app, {"id": 1}, body)
        self.finish(sid, 1)
        self.action(1, sid, "delete_meeting", group=-100, meeting=self.app.session(sid)["meeting_id"])
        with self.assertRaisesRegex(RuleError, "уже удалена"), self.db.transaction():
            act(self.app, {"id": 1}, body)
        self.assertEqual(self.db.one("SELECT COUNT(*) FROM meetings")[0], 3)

    def test_delivery_batch_survives_meeting_deletion_during_network_io(self):
        self.finish(self.a, 1)
        mid = self.app.session(self.a)["meeting_id"]
        fake = FakeTelegram()
        original_call = fake.call
        def call_and_delete(method, **body):
            result = original_call(method, **body)
            if len(fake.calls) == 1:
                self.action(1, self.a, "delete_meeting", group=-100, meeting=mid)
            return result
        fake.call = call_and_delete
        Delivery(self.app, fake).flush()
        self.assertIsNone(self.db.one("SELECT id FROM sessions WHERE id=?", (self.a,)))
        self.assertTrue(self.db.one("SELECT progress_message_id FROM sessions WHERE id=?", (self.b,))[0])

    def test_group_selectors_rosters_and_private_answers_do_not_leak(self):
        owner = state_for(self.app, {"id": 1}, self.a)
        self.assertEqual([group["id"] for group in owner["groups"]], [-100])
        self.assertEqual({meeting["title"] for meeting in owner["meetings"]}, {"Завтрак", "Книжный клуб"})
        self.assertEqual({person["id"] for person in owner["people"]}, {1, 2, 3})
        other = state_for(self.app, {"id": 10}, self.c)
        self.assertEqual({person["id"] for person in other["people"]}, {10, 11})
        outsider = state_for(self.app, {"id": 1}, self.c)
        self.assertTrue(outsider["not_invited"])
        self.assertIsNone(outsider["round"])
        self.assertIsNone(outsider["schedule"])
        self.assertEqual(outsider["meetings"], [])
        participant = state_for(self.app, {"id": 2}, self.a)
        self.assertFalse(participant["is_organizer"])
        self.assertNotIn("answers", participant["round"])
        self.assertEqual(participant["people"], [])

    def test_cross_group_meeting_and_round_parameters_are_rejected_atomically(self):
        with self.assertRaises(RuleError):
            state_for(self.app, {"id": 1}, self.c, group_id=-100)
        before = self.db.one("SELECT COUNT(*) FROM sessions")[0]
        with self.db.transaction(), self.assertRaises(RuleError):
            self.app.create_round(1, [{"id": 2, "name": "Анна"}], 60, "ср 18:00-20:00", self.time + 9000, meeting_id=self.app.session(self.c)["meeting_id"])
        self.assertEqual(self.db.one("SELECT COUNT(*) FROM sessions")[0], before)

    def test_web_creation_in_another_group_uses_that_groups_organizer_and_context(self):
        body = {"action": "create", "request_id": "11111111-1111-4111-8111-111111111111", "group": -200,
                "title": "Новая прогулка", "participants": [{"id": 11, "name": "Катя"}],
                "duration": 60, "windows": "пт 18:00-20:00", "deadline": "2027-01-25T20:00"}
        with self.db.transaction():
            sid = act(self.app, {"id": 10}, body)
        with self.db.transaction():
            again = act(self.app, {"id": 10}, body)
        self.assertEqual(sid, again)
        state = state_for(self.app, {"id": 10}, sid)
        self.assertEqual(state["group_id"], -200)
        self.assertEqual(state["round"]["title"], "Новая прогулка")
        self.assertEqual({meeting["title"] for meeting in state["meetings"]}, {"Новая прогулка", "Прогулка"})
        self.assertEqual(self.app.session(self.c)["state"], "open")

    def test_reminders_and_deadlines_work_in_all_groups(self):
        self.time += 3601
        self.app.tick()
        fake = FakeTelegram()
        Delivery(self.app, fake).flush()
        reminders = [body for method, body in fake.calls if "Напоминание" in body.get("text", "")]
        self.assertEqual(sorted(body["chat_id"] for body in reminders), [-200, -100, -100])
        self.assertTrue(any("Прогулка" in body["text"] and body["chat_id"] == -200 for body in reminders))
        self.time += 3600
        self.app.tick()
        self.assertEqual([self.app.session(sid)["state"] for sid in (self.a, self.b, self.c)], ["closed"] * 3)

    def test_legacy_vote_callback_must_come_from_its_actual_group(self):
        self.action(11, self.c, "availability", slots=[1], none=False)
        self.action(10, self.c, "close")
        self.action(10, self.c, "start_vote", slots=[1])
        callback = {"id": "test", "from": {"id": 11}, "data": f"vote:{self.c}:1",
                    "message": {"message_id": 42, "chat": {"id": -100, "type": "supergroup"}}}
        self.app.process({"update_id": 1, "callback_query": callback})
        self.assertFalse(self.app.view(self.c).votes)
        callback["message"]["chat"]["id"] = -200
        self.app.process({"update_id": 2, "callback_query": callback})
        self.assertEqual(self.app.view(self.c).votes, {11: 1})

    def test_valid_chat_selection_is_verified_by_telegram_before_group_access(self):
        with self.db.transaction():
            button = self.app.group_request_button(20)
        shared = {"chat": {"id": 20, "type": "private"}, "from": {"id": 20, "first_name": "Новый организатор"},
                  "chat_shared": {"request_id": button["request_chat"]["request_id"], "chat_id": -300, "title": "Поддельный заголовок"}}
        self.app.process({"update_id": 1, "message": shared})
        self.assertIsNone(self.db.one("SELECT 1 FROM groups WHERE id=-300"))
        fake = FakeTelegram(admin=20)
        Delivery(self.app, fake).flush()
        self.assertEqual(self.db.one("SELECT title FROM groups WHERE id=-300")[0], "Новая группа")
        self.assertTrue(self.app.is_organizer(20, -300))
        self.assertFalse(self.app.is_organizer(1, -300))
        self.assertIn("getChatAdministrators", [method for method, _ in fake.calls])
        self.assertTrue(any(body.get("chat_id") == -300 for _, body in fake.calls))

    def test_non_admin_or_replayed_chat_selection_cannot_connect_group(self):
        with self.db.transaction():
            button = self.app.group_request_button(20)
        message = {"chat": {"id": 21, "type": "private"}, "from": {"id": 21, "first_name": "Посторонний"},
                   "chat_shared": {"request_id": button["request_chat"]["request_id"], "chat_id": -300}}
        self.app.process({"update_id": 1, "message": message})
        self.assertFalse(self.db.one("SELECT 1 FROM outbox WHERE kind='connect_group'"))
        message.update(chat={"id": 20, "type": "private"}, **{"from": {"id": 20, "first_name": "Человек"}})
        self.app.process({"update_id": 2, "message": message})
        Delivery(self.app, FakeTelegram(admin=21)).flush()
        self.assertFalse(self.db.one("SELECT 1 FROM groups WHERE id=-300"))
        self.app.process({"update_id": 3, "message": message})
        self.assertEqual(self.db.one("SELECT COUNT(*) FROM outbox WHERE kind='connect_group'")[0], 1)

    def test_bot_removal_disables_access_and_reconnection_preserves_meetings(self):
        self.app.process({"update_id": 1, "my_chat_member": {"chat": {"id": -200, "type": "supergroup"},
                          "from": {"id": 10}, "old_chat_member": {"status": "member"}, "new_chat_member": {"status": "kicked"}}})
        self.assertFalse(self.app.is_organizer(10, -200))
        with self.assertRaises(RuleError):
            self.action(11, self.c, "availability", slots=[1], none=False)
        self.app.process({"update_id": 2, "my_chat_member": {"chat": {"id": -200, "type": "supergroup"},
                          "from": {"id": 10, "first_name": "Организатор"}, "old_chat_member": {"status": "kicked"}, "new_chat_member": {"status": "member"}}})
        Delivery(self.app, FakeTelegram(admin=10)).flush()
        self.assertTrue(self.app.is_organizer(10, -200))
        self.assertEqual(self.app.session(self.c)["state"], "open")

    def test_refresh_during_network_delivery_is_not_lost(self):
        self.db.execute("UPDATE outbox SET state='sent' WHERE kind='refresh'")
        with self.db.transaction():
            self.db.refresh(self.a, "progress", self.time)
        fake = FakeTelegram()
        original = fake.call
        injected = False

        def racing_call(method, **body):
            nonlocal injected
            if not injected and method in ("sendMessage", "editMessageText"):
                injected = True
                another = Database(self.path, initialize=False)
                try:
                    other_app = Application(self.config, another, "meeting_bot", now=lambda: self.time)
                    with another.transaction():
                        other_app.save_answer(self.a, 2, {1})
                finally:
                    another.close()
            return original(method, **body)

        fake.call = racing_call
        delivery = Delivery(self.app, fake)
        delivery.flush()
        self.assertIsNotNone(self.db.one("SELECT 1 FROM outbox WHERE kind='refresh' AND state='pending'"))
        delivery.flush()
        progress = [body["text"] for _, body in fake.calls if "Ответили о доступности" in body.get("text", "")]
        self.assertIn("0 из 2", progress[0])
        self.assertIn("1 из 2", progress[-1])


class MigrationTests(unittest.TestCase):
    def legacy_database(self, folder):
        path = str(Path(folder) / "legacy.sqlite3")
        con = sqlite3.connect(path)
        con.executescript(SCHEMA)
        con.execute("INSERT INTO metadata VALUES ('offset','98765')")
        con.execute("INSERT INTO metadata VALUES ('setup_group',?)", (json.dumps({"chat_id": -100, "title": "JUN"}),))
        con.execute("INSERT INTO users VALUES (2,'Анна','anna')")
        con.execute("INSERT INTO sessions(id,group_id,organizer_id,state,duration,windows,deadline,reminder_at,created_at,nominations,chosen_slot) VALUES (1,-100,1,'final',60,'ср 19:00-20:00',1793000000,1792996400,1792000000,'[1]',1)")
        con.execute("INSERT INTO participants VALUES (1,2,'Анна')")
        con.execute("INSERT INTO slots VALUES (1,1,2,1140)")
        con.execute("INSERT INTO answers VALUES (1,2,0,1792000001)")
        con.execute("INSERT INTO availability VALUES (1,2,1)")
        con.execute("INSERT INTO drafts VALUES (1,2,'[1]')")
        con.execute("INSERT INTO votes VALUES (1,2,1)")
        con.execute("INSERT INTO schedules VALUES (-100,1,2,1140,60,1792000002)")
        con.execute("INSERT INTO outbox(kind,payload,dedupe_key,state,created_at) VALUES ('message','{}','final:1','sent',1792000002)")
        con.commit()
        con.close()
        return path

    def test_v1_upgrade_preserves_answers_votes_schedule_offsets_and_message_queue(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.legacy_database(folder)
            db = Database(path)
            config = Config("123:test", frozenset({1}), -100, path)
            app = Application(config, db, "meeting_bot")
            mid = app.session(1)["meeting_id"]
            self.assertEqual(db.one("PRAGMA user_version")[0], 3)
            self.assertEqual(db.one("SELECT title FROM groups WHERE id=-100")[0], "JUN")
            self.assertEqual(app.view(1).responses, {2: {1}})
            self.assertEqual(app.view(1).votes, {2: 1})
            self.assertEqual(db.one("SELECT selected FROM drafts")[0], "[1]")
            self.assertEqual(db.one("SELECT session_id FROM schedules WHERE meeting_id=?", (mid,))[0], 1)
            self.assertEqual(db.offset, 98765)
            self.assertEqual(db.one("SELECT state FROM outbox WHERE dedupe_key='final:1'")[0], "sent")
            self.assertEqual(db.one("PRAGMA quick_check")[0], "ok")
            self.assertEqual(db.all("PRAGMA foreign_key_check"), [])
            db.close()
            db = Database(path)
            self.assertEqual(db.one("SELECT COUNT(*) FROM meetings")[0], 1)
            self.assertEqual(db.one("SELECT meeting_id FROM sessions WHERE id=1")[0], mid)
            db.close()

    def test_failed_migration_rolls_back_schema_and_keeps_legacy_data(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.legacy_database(folder)
            with sqlite3.connect(path) as con:
                con.execute("DROP INDEX one_active_session")
            with self.assertRaises(sqlite3.OperationalError):
                Database(path)
            with sqlite3.connect(path) as con:
                self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], 1)
                self.assertIsNone(con.execute("SELECT name FROM sqlite_master WHERE name='groups'").fetchone())
                self.assertEqual(con.execute("SELECT COUNT(*) FROM answers").fetchone()[0], 1)
                self.assertNotIn("meeting_id", [row[1] for row in con.execute("PRAGMA table_info(sessions)")])


if __name__ == "__main__":
    unittest.main()
