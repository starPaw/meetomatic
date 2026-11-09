from datetime import datetime, timezone
from dataclasses import replace
import hashlib
import hmac
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import uuid

from bot_calendar.config import Config
from bot_calendar.domain import utc_now
from bot_calendar.service import Application
from bot_calendar.storage import Database
from bot_calendar.telegram import Delivery
from bot_calendar.web import APIError, MiniAppServer, act, state_for, verify_init_data


TOKEN = "123:offline-web-test"


def signed(user, now=None, **extra):
    fields = {"auth_date": str(int(utc_now() if now is None else now)), "user": json.dumps(user, ensure_ascii=False), **extra}
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    check = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
    fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


class AuthenticationTests(unittest.TestCase):
    def test_verified_identity_includes_current_signed_optional_fields(self):
        user = {"id": 2, "first_name": "Анна", "username": "anna"}
        raw = signed(user, signature="signed-extra-field", query_id="test")
        self.assertEqual(verify_init_data(raw, TOKEN, utc_now()), user)

    def test_tampered_expired_future_and_duplicate_auth_are_rejected(self):
        now = utc_now()
        raw = signed({"id": 2, "first_name": "Анна"}, now)
        cases = ["", raw.replace("auth_date=", "auth_date=1"), raw + "&user=forged",
                 signed({"id": 2}, now - 3601), signed({"id": 2}, now + 120), signed({"id": True}, now)]
        for value in cases:
            with self.subTest(value=value[:30]), self.assertRaises(APIError) as caught:
                verify_init_data(value, TOKEN, now)
            self.assertEqual(caught.exception.status, 401)
        with self.assertRaises(APIError):
            verify_init_data(raw, "different:token", now)


class WebWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / "bot.sqlite3")
        self.config = Config(TOKEN, frozenset({1}), -100, self.path, webapp_url="https://meeting.example")
        self.db = Database(self.path)
        self.app = Application(self.config, self.db, "meeting_bot")
        with self.db.transaction():
            self.sid = self.app.create_round(1, [{"id": 1, "name": "Организатор"}, {"id": 2, "name": "Анна"}],
                                             60, "ср 18:00-20:00", utc_now() + 7200)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def action(self, uid, action, **body):
        with self.db.transaction():
            return act(self.app, {"id": uid}, {"action": action, "round": self.sid, **body})

    def test_private_details_are_only_in_organizer_state(self):
        self.action(1, "availability", slots=[1], none=False)
        self.action(2, "availability", slots=[], none=True)
        participant = state_for(self.app, {"id": 2})
        organizer = state_for(self.app, {"id": 1})
        self.assertNotIn("answers", participant["round"])
        self.assertNotIn("unavailable", participant["round"]["candidates"][0])
        self.assertEqual(participant["people"], [])
        self.assertNotIn("id", participant["round"]["participants"][0])
        self.assertEqual(organizer["round"]["candidates"][0]["unavailable"], ["Анна"])
        outsider = state_for(self.app, {"id": 99})
        self.assertTrue(outsider["not_invited"])
        self.assertIsNone(outsider["round"])
        self.assertIsNone(outsider["schedule"])

    def test_web_answer_replaces_bot_answer_and_survives_new_connection(self):
        with self.db.transaction():
            self.app.save_answer(self.sid, 2, {1})
        self.action(2, "availability", slots=[2, 3], none=False)
        another = Database(self.path, initialize=False)
        try:
            other_app = Application(self.config, another, "meeting_bot")
            self.assertEqual(other_app.view(self.sid).responses[2], {2, 3})
        finally:
            another.close()

    def test_partial_confirmation_is_required_and_failure_is_atomic(self):
        self.action(1, "availability", slots=[1], none=False)
        self.action(2, "availability", slots=[2], none=False)
        self.action(1, "close")
        with self.assertRaises(APIError) as caught:
            self.action(1, "start_vote", slots=[1, 2])
        self.assertEqual(caught.exception.code, "partial_confirmation_required")
        self.assertEqual(self.app.session(self.sid)["state"], "closed")
        self.assertEqual(self.app.view(self.sid).nominations, [])
        self.action(1, "start_vote", slots=[1, 2], allow_partial=True)
        self.assertEqual(self.app.session(self.sid)["state"], "voting")
        self.assertTrue(self.app.session(self.sid)["partial_approved"])

    def test_end_to_end_web_vote_tie_and_schedule_persisted(self):
        self.action(1, "availability", slots=[1, 2], none=False)
        self.action(2, "availability", slots=[1, 2], none=False)
        self.action(1, "close")
        self.action(1, "start_vote", slots=[1, 2])
        self.action(1, "vote", slot=1)
        self.action(2, "vote", slot=2)
        self.assertEqual(state_for(self.app, {"id": 1})["round"]["leaders"], [1, 2])
        self.action(1, "confirm", slot=2)
        state = state_for(self.app, {"id": 1})
        self.assertEqual(state["round"]["state"], "final")
        self.assertEqual(state["round"]["publication_state"], "pending")
        self.assertEqual(state["schedule"]["start"], 1110)
        self.assertIsNotNone(self.db.one("SELECT 1 FROM outbox WHERE dedupe_key=?", (f"final:{self.sid}",)))

    def test_creation_is_idempotent_and_uses_prague_time(self):
        key = str(uuid.uuid4())
        body = {"action": "create", "request_id": key, "participants": [{"id": 1, "name": "Организатор"}],
                "duration": 120, "windows": "сб,вс 09:00-23:00", "deadline": "2027-01-25T20:00"}
        with self.db.transaction():
            sid = act(self.app, {"id": 1}, body)
        with self.db.transaction():
            again = act(self.app, {"id": 1}, body)
        self.assertEqual(sid, again)
        self.assertEqual(self.db.one("SELECT COUNT(*) FROM sessions")[0], 2)
        stamp = self.app.session(sid)["deadline"]
        self.assertEqual(datetime.fromtimestamp(stamp, timezone.utc).hour, 19)
        self.assertEqual(self.app.session(self.sid)["state"], "open")
        self.assertNotEqual(self.app.session(sid)["meeting_id"], self.app.session(self.sid)["meeting_id"])

    def test_web_commands_cannot_impersonate_organizer_or_other_participant(self):
        for uid, action, body in [(2, "close", {}), (99, "availability", {"slots": [1]}),
                                  (2, "start_vote", {"slots": [1]}), (2, "confirm", {"slot": 1})]:
            with self.subTest(uid=uid, action=action), self.assertRaises(ValueError):
                self.action(uid, action, **body)
        self.assertEqual(self.app.session(self.sid)["state"], "open")
        self.assertEqual(self.app.view(self.sid).responses, {})

    def test_bot_opens_mini_app_and_preserves_existing_round(self):
        self.app.process({"update_id": 1, "message": {"chat": {"id": 1, "type": "private"},
                          "from": {"id": 1, "first_name": "Организатор"}, "text": "/new"}})
        payload = json.loads(self.db.one("SELECT payload FROM outbox ORDER BY id DESC LIMIT 1")[0])
        self.assertEqual(payload["reply_markup"]["inline_keyboard"][0][0]["web_app"]["url"], "https://meeting.example/?open=create")
        self.assertFalse(self.db.one("SELECT 1 FROM wizards"))
        self.assertEqual(self.app.session(self.sid)["state"], "open")
        self.app.process({"update_id": 2, "message": {"chat": {"id": 2, "type": "private"},
                          "from": {"id": 2, "first_name": "Анна"}, "text": f"/start availability_{self.sid}"}})
        payload = json.loads(self.db.one("SELECT payload FROM outbox ORDER BY id DESC LIMIT 1")[0])
        self.assertEqual(payload["reply_markup"]["inline_keyboard"][0][0]["web_app"]["url"], f"https://meeting.example/?round={self.sid}")

    def test_group_entry_supports_anonymous_admin_without_granting_organizer_rights(self):
        self.app = Application(replace(self.config, webapp_direct=True), self.db, "meeting_bot")
        anonymous = {"chat": {"id": -100, "type": "supergroup"}, "sender_chat": {"id": -100},
                     "from": {"id": 999, "is_bot": True}, "text": "/app@meeting_bot"}
        self.app.process({"update_id": 1, "message": anonymous})
        payload = json.loads(self.db.one("SELECT payload FROM outbox ORDER BY id DESC LIMIT 1")[0])
        self.assertEqual(payload["chat_id"], -100)
        self.assertEqual(payload["reply_markup"]["inline_keyboard"][0][0]["url"], "https://t.me/meeting_bot?startapp=group_100")
        self.app.process({"update_id": 2, "message": {**anonymous, "text": "/close@meeting_bot"}})
        self.assertEqual(self.app.session(self.sid)["state"], "open")
        self.assertFalse(self.db.one("SELECT 1 FROM users WHERE user_id=999"))
        self.assertFalse(self.db.one("SELECT 1 FROM wizards"))
        count = self.db.one("SELECT COUNT(*) FROM outbox")[0]
        self.app.process({"update_id": 3, "message": {**anonymous, "sender_chat": {"id": -200}}})
        self.assertEqual(self.db.one("SELECT COUNT(*) FROM outbox")[0], count)
        self.app.process({"update_id": 4, "message": {"chat": {"id": -100, "type": "supergroup"},
                          "from": {"id": 2, "first_name": "Анна"}, "text": "/app@meeting_bot"}})
        self.assertEqual(self.db.one("SELECT COUNT(*) FROM outbox")[0], count + 1)

    def test_existing_group_messages_refresh_to_mini_app_links(self):
        self.app = Application(replace(self.config, webapp_direct=True), self.db, "meeting_bot")
        self.action(1, "availability", slots=[1], none=False)
        self.action(2, "availability", slots=[1], none=False)
        self.action(1, "close")
        self.action(1, "start_vote", slots=[1])
        self.db.execute("UPDATE sessions SET progress_message_id=66,vote_message_id=77 WHERE id=?", (self.sid,))
        client = Mock()
        client.call.return_value = {"message_id": 1000}
        Delivery(self.app, client).flush()
        edits = [call.kwargs for call in client.call.call_args_list if call.args == ("editMessageText",)]
        self.assertEqual({body["message_id"] for body in edits}, {66, 77})
        for body in edits:
            self.assertIn(f"?startapp=round_{self.sid}", body["reply_markup"]["inline_keyboard"][0][0]["url"])
            self.assertNotIn("callback_data", body["reply_markup"]["inline_keyboard"][0][0])
        self.action(2, "vote", slot=1)
        self.assertIsNotNone(self.db.one("SELECT 1 FROM outbox WHERE kind='refresh' AND json_extract(payload,'$.target')='progress'"))

    def test_organizer_outside_expected_list_manages_but_cannot_vote(self):
        with self.db.transaction():
            self.sid = self.app.create_round(1, [{"id": 2, "name": "Анна"}], 60, "ср 18:00-20:00", utc_now() + 7200)
        self.action(2, "availability", slots=[1], none=False)
        self.action(1, "close")
        self.action(1, "start_vote", slots=[1])
        self.assertFalse(state_for(self.app, {"id": 1})["round"]["is_expected"])
        with self.assertRaises(ValueError):
            self.action(1, "vote", slot=1)
        self.assertFalse(self.app.view(self.sid).votes)
        self.action(2, "vote", slot=1)
        self.action(1, "confirm", slot=1)
        self.assertEqual(self.app.session(self.sid)["state"], "final")


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.path = str(Path(cls.temp.name) / "bot.sqlite3")
        cls.config = Config(TOKEN, frozenset({1}), -100, cls.path, webapp_url="https://meeting.example")
        db = Database(cls.path)
        app = Application(cls.config, db, "meeting_bot")
        with db.transaction():
            cls.sid = app.create_round(1, [{"id": 1, "name": "Организатор"}, {"id": 2, "name": "Анна"}],
                                       60, "ср 18:00-20:00", utc_now() + 7200)
        db.close()
        cls.server = MiniAppServer(cls.config, "meeting_bot", address=("127.0.0.1", 0))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(3)
        cls.temp.cleanup()

    def request(self, path, uid=None, body=None, origin=None):
        headers = {"Content-Type": "application/json"}
        if uid:
            headers["X-Telegram-Init-Data"] = signed({"id": uid, "first_name": "Тест"})
        if origin:
            headers["Origin"] = origin
        request = Request(self.url + path, headers=headers, data=json.dumps(body).encode() if body else None)
        try:
            with urlopen(request, timeout=5) as response:
                return response.status, response.headers, response.read()
        except HTTPError as exc:
            return exc.code, exc.headers, exc.read()

    def test_assets_and_public_config_contain_no_token_or_private_group_state(self):
        for path in ("/", "/app.js", "/availability.js", "/translations.js", "/i18n.js", "/app.css", "/favicon.svg", "/manrope.ttf", "/OFL.txt"):
            with self.subTest(path=path):
                status, headers, content = self.request(path)
                self.assertEqual(status, 200)
                self.assertNotIn(TOKEN.encode(), content)
                self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(json.loads(self.request('/api/config')[2]), {"bot_username": "meeting_bot", "direct_links": False})
        for path in ("/.env", "/../.env", "/data/bot.sqlite3"):
            self.assertEqual(self.request(path)[0], 404)

    def test_api_requires_signed_identity_and_rejects_foreign_origin(self):
        self.assertEqual(self.request('/api/state')[0], 401)
        self.assertEqual(self.request('/api/state', uid=1, origin='https://evil.example')[0], 403)
        status, _, content = self.request('/api/state', uid=1, origin='https://meeting.example')
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(content)["is_organizer"])

    def test_http_save_ignores_forged_actor_and_wakes_delivery(self):
        status, _, content = self.request('/api/action', uid=2, body={"action": "availability", "round": self.sid, "slots": [1, 2], "none": False, "user_id": 1})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(content)["round"]["my_answer"]["slots"], [1, 2])
        self.assertTrue(self.server.wake.is_set())
        db = Database(self.path, initialize=False)
        try:
            app = Application(self.config, db, "meeting_bot")
            self.assertEqual(app.view(self.sid).responses.get(2), {1, 2})
            self.assertNotIn(1, app.view(self.sid).responses)
        finally:
            db.close()

    def test_native_group_picker_is_prepared_for_the_verified_actor(self):
        fake = Mock()
        fake.call.return_value = {"id": "prepared-group-request"}
        with patch.object(self.server, "telegram", fake):
            status, _, content = self.request('/api/action', uid=2, body={"action": "prepare_group", "user_id": 1})
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(content), {"prepared_request_id": "prepared-group-request"})
            call = fake.call.call_args
            self.assertEqual(call.args, ("savePreparedKeyboardButton",))
            self.assertEqual(call.kwargs["user_id"], 2)
            self.assertTrue(call.kwargs["button"]["request_chat"]["bot_is_member"])
            request_id = call.kwargs["button"]["request_chat"]["request_id"]
        db = Database(self.path, initialize=False)
        try:
            self.assertIsNotNone(db.one("SELECT value FROM metadata WHERE key=?", (f"group-request:2:{request_id}",)))
            self.assertIsNone(db.one("SELECT value FROM metadata WHERE key=?", (f"group-request:1:{request_id}",)))
        finally:
            db.close()

    def test_group_join_requires_actual_membership_and_does_not_grant_organizer_role(self):
        fake = Mock()
        fake.call.return_value = {"status": "left"}
        with patch.object(self.server, "telegram", fake):
            status, _, _ = self.request('/api/action', uid=98, body={"action": "join_group", "group": -100, "user_id": 1})
            self.assertEqual(status, 403)
            fake.call.return_value = {"status": "member"}
            status, _, content = self.request('/api/action', uid=98, body={"action": "join_group", "group": -100, "user_id": 1})
            self.assertEqual(status, 200)
            state = json.loads(content)
            self.assertFalse(state["is_organizer"])
            self.assertIsNone(state["round"])
            self.assertEqual(state["people"], [])
            self.assertEqual([group["id"] for group in state["groups"]], [-100])
            self.assertEqual(fake.call.call_args.kwargs["user_id"], 98)

    def test_round_and_group_context_cannot_be_forged(self):
        status, _, _ = self.request(f'/api/state?round={self.sid}&group=-999', uid=1)
        self.assertEqual(status, 400)
        status, _, _ = self.request('/api/action', uid=2, body={"action": "availability", "round": self.sid, "group": -999, "slots": [1], "none": False})
        self.assertEqual(status, 400)

    def test_http_repeat_targets_the_selected_meeting_and_preserves_other_events(self):
        first = {"action": "create", "request_id": str(uuid.uuid4()), "group": -100, "title": "Отдельная встреча",
                 "participants": [{"id": 1, "name": "Организатор"}], "duration": 60,
                 "windows": "ср 18:00-20:00", "deadline": "2027-01-25T20:00"}
        status, _, content = self.request('/api/action', uid=1, body=first)
        self.assertEqual(status, 200)
        created = json.loads(content)
        mid, sid = created["meeting_id"], created["round"]["id"]
        self.assertEqual(created["round"]["title"], "Отдельная встреча")
        repeat = {**first, "request_id": str(uuid.uuid4()), "meeting": mid}
        status, _, content = self.request('/api/action', uid=1, body=repeat)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(content)["meeting_id"], mid)
        db = Database(self.path, initialize=False)
        try:
            self.assertEqual(db.one("SELECT state FROM sessions WHERE id=?", (sid,))[0], "cancelled")
            self.assertEqual(db.one("SELECT state FROM sessions WHERE id=?", (self.sid,))[0], "open")
        finally:
            db.close()

    def test_http_delete_last_meeting_in_another_group_returns_that_empty_group(self):
        db = Database(self.path, initialize=False)
        try:
            app = Application(self.config, db, "meeting_bot")
            with db.transaction():
                app.connect_group(-300, "Законченные встречи", 1)
                sid = app.create_round(1, [{"id": 1, "name": "Организатор"}], 60,
                    "ср 18:00-20:00", utc_now() + 7200, group_id=-300, title="Архив", new_meeting=True)
                app.save_answer(sid, 1, {1})
                app.close_round(sid)
                app.nominate(sid, 1, [1])
                app.start_vote(sid, 1)
                app.cast_vote(sid, 1, 1)
                app.confirm(sid, 1, 1)
                mid = app.session(sid)["meeting_id"]
            body = {"action": "delete_meeting", "group": -300, "meeting": mid, "round": sid, "user_id": 1}
            self.assertEqual(self.request('/api/action', uid=2, body=body)[0], 400)
            for _ in range(2):
                status, _, content = self.request('/api/action', uid=1, body=body)
                self.assertEqual(status, 200, content)
                snapshot = json.loads(content)
                self.assertEqual(snapshot["group_id"], -300)
                self.assertEqual(snapshot["meetings"], [])
                self.assertIsNone(snapshot["round"])
                self.assertIsNone(snapshot["schedule"])
                self.assertIsNone(snapshot["meeting_id"])
            self.assertEqual(self.request(f'/api/state?round={sid}', uid=1)[0], 400)
            self.assertEqual(app.session(self.sid)["state"], "open")
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
