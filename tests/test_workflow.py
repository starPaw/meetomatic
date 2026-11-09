from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from bot_calendar.config import Config
from bot_calendar.domain import RuleError
from bot_calendar.service import Application
from bot_calendar.storage import Database
from bot_calendar.telegram import Delivery, TelegramError
from bot_calendar import views


class FakeTelegram:
    def __init__(self):
        self.calls = []
        self.failure = None
        self.counter = 100

    def call(self, method, **payload):
        self.calls.append((method, dict(payload)))
        if self.failure:
            error, self.failure = self.failure, None
            raise error
        self.counter += 1
        return {"message_id": self.counter}


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / "bot.sqlite3")
        self.config = Config("123:test", frozenset({1}), -100, self.path)
        self.time = datetime(2026, 10, 22, 12, tzinfo=timezone.utc).timestamp()
        self.db = Database(self.path)
        self.app = Application(self.config, self.db, "meeting_test_bot", now=lambda: self.time)
        self.telegram = FakeTelegram()
        self.delivery = Delivery(self.app, self.telegram)
        self.update_id = 0

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def create(self, people=None, windows="вт 18:00-20:00"):
        with self.db.transaction():
            return self.app.create_round(1, people or [{"id": 2, "name": "Анна"}, {"id": 3, "name": "Борис"}],
                                         60, windows, self.time + 7200)

    def save(self, sid, uid, selected, none=False):
        with self.db.transaction():
            self.app.save_answer(sid, uid, set(selected), none)

    def message(self, uid, text, group=False, **extra):
        self.update_id += 1
        update = {"update_id": self.update_id, "message": {"message_id": self.update_id,
                  "from": {"id": uid, "is_bot": False, "first_name": f"User {uid}"},
                  "chat": {"id": -100 if group else uid, "type": "supergroup" if group else "private"},
                  "text": text, **extra}}
        self.app.process(update)
        return update

    def callback(self, uid, data, group=False):
        self.update_id += 1
        update = {"update_id": self.update_id, "callback_query": {"id": str(self.update_id),
                  "from": {"id": uid}, "data": data,
                  "message": {"message_id": 80, "chat": {"id": -100 if group else uid,
                              "type": "supergroup" if group else "private"}}}}
        self.app.process(update)
        return update

    def restart(self):
        self.db.close()
        self.db = Database(self.path)
        self.app = Application(self.config, self.db, "meeting_test_bot", now=lambda: self.time)
        self.delivery = Delivery(self.app, self.telegram)

    def begin_vote(self, sid, nominated, partial=False):
        self.message(1, "/close")
        for slot in nominated:
            self.callback(1, f"nominate:{sid}:{slot}")
        self.callback(1, f"permit:{sid}:{','.join(map(str, nominated))}" if partial else f"launch:{sid}")

    def test_common_time_and_complete_first_selection(self):
        sid = self.create(windows="ср 19:00-20:30")
        self.save(sid, 2, {1, 2})
        self.save(sid, 3, {1})
        view = self.app.view(sid)
        self.assertTrue(view.top[0].common)
        self.assertEqual([c.slot.id for c in view.top], [1])
        self.begin_vote(sid, [1])
        self.callback(2, f"vote:{sid}:1", group=True)
        self.callback(3, f"vote:{sid}:1", group=True)
        self.assertEqual(self.app.session(sid)["state"], "voting")
        self.callback(1, f"confirm:{sid}:1")
        self.delivery.flush()
        final = [body["text"] for method, body in self.telegram.calls if method == "sendMessage" and body.get("chat_id") == -100 and "Встречаемся" in body.get("text", "")]
        self.assertEqual(len(final), 1)
        self.assertIn("каждую среду, 19:00–20:00 по Праге", final[0])
        self.assertEqual(self.app.session(sid)["state"], "final")
        self.assertEqual(self.db.one("SELECT duration FROM schedules")[0], 60)

    def test_no_common_time_requires_explicit_partial_vote_decision(self):
        sid = self.create()
        self.save(sid, 2, {1})
        self.save(sid, 3, {2})
        self.assertIn("Общего времени нет", views.result_text(self.app.view(sid)))
        self.begin_vote(sid, [1, 2])
        self.assertEqual(self.app.session(sid)["state"], "closed")
        self.assertFalse(self.app.session(sid)["partial_approved"])
        self.callback(1, f"permit:{sid}:1,2")
        self.assertEqual(self.app.session(sid)["state"], "voting")
        self.assertTrue(self.app.session(sid)["partial_approved"])

    def test_partial_approval_is_bound_to_current_nominations(self):
        sid = self.create()
        self.save(sid, 2, {1})
        self.save(sid, 3, {2})
        self.begin_vote(sid, [1])
        self.callback(1, f"nominate:{sid}:2")
        self.callback(1, f"permit:{sid}:1")
        self.assertEqual(self.app.session(sid)["state"], "closed")
        self.callback(1, f"permit:{sid}:1,2")
        self.assertEqual(self.app.session(sid)["state"], "voting")

    def test_missing_answer_is_preliminary_not_unavailable(self):
        sid = self.create()
        self.save(sid, 2, {1})
        view = self.app.view(sid)
        self.assertEqual(view.missing, [3])
        self.assertEqual(view.top[0].unavailable, ())
        self.assertFalse(view.top[0].common)
        text = views.result_text(view, details=True)
        self.assertIn("Предварительный", text)
        self.assertIn("Нет ответа: Борис", text)
        self.assertNotIn("подходит всем", text)
        self.assertIn("Ждём: Борис", views.progress_text(view))
        self.begin_vote(sid, [1])
        self.assertEqual(self.app.session(sid)["state"], "closed")

    def test_explicit_none_counts_as_response_and_never_as_common(self):
        sid = self.create()
        self.save(sid, 2, {1})
        self.save(sid, 3, set(), none=True)
        view = self.app.view(sid)
        self.assertEqual(view.missing, [])
        self.assertEqual(view.top[0].unavailable, (3,))
        self.assertFalse(view.top[0].common)
        self.assertIn("Не могут: Борис", views.result_text(view, True))

    def test_latest_saved_answer_replaces_previous_and_drafts_do_not(self):
        sid = self.create()
        self.save(sid, 2, {1})
        self.save(sid, 3, {1})
        self.callback(3, f"toggle:{sid}:1:0")
        self.callback(3, f"toggle:{sid}:2:0")
        self.assertTrue(self.app.view(sid).top[0].common)
        self.callback(3, f"save:{sid}:0")
        self.assertEqual(self.app.view(sid).responses[3], {2})
        self.assertFalse(any(c.common for c in self.app.view(sid).candidates))

    def test_empty_selection_is_not_implicit_refusal(self):
        sid = self.create()
        self.callback(2, f"save:{sid}:0")
        self.assertNotIn(2, self.app.view(sid).responses)
        self.callback(2, f"none:{sid}:0")
        self.assertEqual(self.app.view(sid).responses[2], set())

    def test_tied_votes_are_resolved_by_organizer(self):
        sid = self.create()
        self.save(sid, 2, {1, 2})
        self.save(sid, 3, {1, 2})
        self.begin_vote(sid, [1, 2])
        self.callback(2, f"vote:{sid}:1", group=True)
        self.callback(3, f"vote:{sid}:2", group=True)
        text, markup = views.decision_view(self.app.view(sid))
        self.assertIn("поровну", text)
        self.assertEqual(len(markup["inline_keyboard"]), 2)
        self.callback(3, f"confirm:{sid}:2")
        self.assertEqual(self.app.session(sid)["state"], "voting")
        self.callback(1, f"confirm:{sid}:2")
        self.assertEqual(self.app.session(sid)["chosen_slot"], 2)

    def test_stale_confirmation_cannot_pick_a_non_leader(self):
        sid = self.create()
        self.save(sid, 2, {1, 2})
        self.save(sid, 3, {1, 2})
        self.begin_vote(sid, [1, 2])
        self.callback(2, f"vote:{sid}:1", group=True)
        self.callback(3, f"vote:{sid}:2", group=True)
        self.callback(2, f"vote:{sid}:2", group=True)
        self.callback(1, f"confirm:{sid}:1")
        self.assertEqual(self.app.session(sid)["state"], "voting")
        self.callback(1, f"confirm:{sid}:2")
        self.assertEqual(self.app.session(sid)["state"], "final")

    def test_votes_answers_drafts_and_update_dedup_survive_restart(self):
        sid = self.create()
        self.save(sid, 2, {1, 2})
        self.save(sid, 3, {1, 2})
        update = self.callback(2, f"toggle:{sid}:3:0")
        self.restart()
        self.app.process(update)
        self.assertEqual(self.app.selection(sid, 2), {1, 2, 3})
        self.assertEqual(self.app.view(sid).responses[2], {1, 2})
        self.begin_vote(sid, [1, 2])
        self.callback(2, f"vote:{sid}:1", group=True)
        self.restart()
        self.assertEqual(self.app.view(sid).votes, {2: 1})
        self.assertEqual(self.app.session(sid)["state"], "voting")

    def test_polling_accepts_randomized_lower_update_id_after_week_of_inactivity(self):
        self.update_id = 100000
        self.message(1, "/help")
        self.assertEqual(self.app.poll_offset(), 100002)
        self.time += 7 * 86400 + 1
        self.assertEqual(self.app.poll_offset(), 0)
        self.update_id = 10
        self.message(1, "/new")
        self.assertIsNotNone(self.db.one("SELECT 1 FROM wizards WHERE user_id=1"))
        self.assertEqual(self.db.offset, 12)

    def test_schedule_survives_restart_and_repeat(self):
        sid = self.create()
        self.save(sid, 2, {1})
        self.save(sid, 3, {1})
        self.begin_vote(sid, [1])
        self.callback(2, f"vote:{sid}:1", group=True)
        self.callback(1, f"confirm:{sid}:1")
        self.restart()
        self.assertEqual(self.db.one("SELECT session_id FROM schedules")[0], sid)
        self.create()
        self.assertEqual(self.db.one("SELECT session_id FROM schedules")[0], sid)

    def test_deadline_closes_and_refuses_answers_even_before_timer(self):
        sid = self.create()
        self.time += 7200
        with self.assertRaises(RuleError):
            self.save(sid, 2, {1})
        self.app.tick()
        self.assertEqual(self.app.session(sid)["state"], "closed")
        self.assertEqual(self.app.view(sid).missing, [2, 3])
        self.assertFalse(self.db.one("SELECT 1 FROM outbox WHERE kind='reminder'"))

    def test_one_reminder_only_for_missing_and_no_late_reminder_after_restart(self):
        sid = self.create()
        self.save(sid, 2, {1})
        self.time += 3601
        self.app.tick()
        self.restart()
        self.app.tick()
        self.delivery.flush()
        reminders = [body["text"] for _, body in self.telegram.calls if "Напоминание" in body.get("text", "")]
        self.assertEqual(len(reminders), 1)
        self.assertIn("Борис", reminders[0])
        self.assertNotIn("Анна", reminders[0])
        self.app.tick()
        self.delivery.flush()
        self.assertEqual(self.db.one("SELECT COUNT(*) FROM outbox WHERE kind='reminder'")[0], 1)

    def test_queued_reminder_is_suppressed_after_deadline(self):
        self.create()
        self.time += 3601
        self.app.tick()
        self.time += 3600
        self.app.tick()
        self.delivery.flush()
        self.assertFalse(any("Напоминание" in body.get("text", "") for _, body in self.telegram.calls))

    def test_uncertain_reminder_is_not_sent_twice(self):
        self.create()
        self.delivery.flush()
        self.telegram.calls.clear()
        self.time += 3601
        self.app.tick()
        self.telegram.failure = TelegramError(0, "Network request failed")
        self.delivery.flush()
        self.restart()
        self.time += 30
        self.delivery.flush()
        reminders = [body for _, body in self.telegram.calls if "Напоминание" in body.get("text", "")]
        self.assertEqual(len(reminders), 1)
        self.assertEqual(self.db.one("SELECT state FROM outbox WHERE kind='reminder'")[0], "uncertain")

    def test_interrupted_reminder_claim_is_not_replayed_after_restart(self):
        self.create()
        self.time += 3601
        self.app.tick()
        self.db.execute("UPDATE outbox SET state='sending' WHERE kind='reminder'")
        self.restart()
        self.delivery.flush()
        self.assertFalse(any("Напоминание" in body.get("text", "") for _, body in self.telegram.calls))

    def test_telegram_rate_limited_reminder_can_retry_before_deadline(self):
        self.create()
        self.delivery.flush()
        self.time += 3601
        self.app.tick()
        self.telegram.failure = TelegramError(429, "Too many requests", 5)
        self.delivery.flush()
        self.assertEqual(self.db.one("SELECT state FROM outbox WHERE kind='reminder'")[0], "pending")
        self.time += 10
        self.delivery.flush()
        self.assertEqual(self.db.one("SELECT state FROM outbox WHERE kind='reminder'")[0], "sent")

    def test_organizer_commands_and_private_details_are_protected(self):
        sid = self.create()
        self.message(2, "/close", group=True)
        self.message(2, "/new")
        self.message(1, "/answers", group=True)
        self.callback(2, f"close:{sid}")
        self.assertEqual(self.app.session(sid)["state"], "open")
        self.assertFalse(self.db.one("SELECT 1 FROM wizards"))
        self.delivery.flush()
        group_text = "\n".join(body.get("text", "") for _, body in self.telegram.calls if body.get("chat_id") == -100)
        self.assertNotIn("Обозначения вариантов", group_text)
        self.assertNotIn("Не могут:", group_text)

    def test_unexpected_people_cannot_answer_or_vote(self):
        sid = self.create()
        self.callback(99, f"none:{sid}:0")
        self.assertEqual(self.app.view(sid).responses, {})
        self.save(sid, 2, {1})
        self.save(sid, 3, {1})
        self.begin_vote(sid, [1])
        self.callback(99, f"vote:{sid}:1", group=True)
        self.assertEqual(self.app.view(sid).votes, {})

    def test_wizard_persists_and_publish_button_is_idempotent(self):
        self.message(1, "/new")
        self.message(1, "2:Анна; 3:Борис")
        self.restart()
        self.message(1, "-")
        self.message(1, "ср 19:00-21:00")
        self.message(1, "23.10.2026 20:00")
        row = self.db.one("SELECT * FROM wizards")
        self.assertEqual(row["step"], "preview")
        update = self.callback(1, f"publish:{row['token']}")
        self.restart()
        self.app.process(update)
        self.callback(1, f"publish:{row['token']}")
        self.assertEqual(self.db.one("SELECT COUNT(*) FROM sessions")[0], 1)
        self.assertEqual(len(self.app.view(1).slots), 3)

    def test_native_user_selection_and_recycled_username(self):
        self.message(2, "/join", group=True, **{"from": {"id": 2, "first_name": "Анна", "username": "anna"}})
        self.assertEqual(self.app.parse_participants("@ANNA")[0]["id"], 2)
        self.message(3, "/join", group=True, **{"from": {"id": 3, "first_name": "Другая", "username": "anna"}})
        self.assertEqual(self.app.parse_participants("@anna")[0]["id"], 3)
        self.message(1, "/new")
        row = self.db.one("SELECT * FROM wizards")
        self.message(1, "", users_shared={"request_id": int(row["token"], 16) % 2147483647,
                                        "users": [{"user_id": 2, "first_name": "Анна"}, {"user_id": 3, "first_name": "Борис"}]})
        self.assertEqual(self.db.one("SELECT step FROM wizards")[0], "duration")

    def test_repeat_replaces_active_round_preserving_old_answers(self):
        sid = self.create()
        self.save(sid, 2, {1})
        self.message(1, "/repeat")
        self.message(1, "вт 18:00-22:00")
        self.message(1, "24.10.2026 20:00")
        token = self.db.one("SELECT token FROM wizards")[0]
        self.callback(1, f"publish:{token}")
        self.assertEqual(self.app.session(sid)["state"], "cancelled")
        self.assertEqual(self.app.view(sid).responses[2], {1})
        self.assertEqual(self.app.latest()["state"], "open")
        self.callback(2, f"none:{sid}:0")
        self.assertEqual(self.app.view(sid).responses[2], {1})

    def test_transport_failure_retries_durable_publication_after_restart(self):
        sid = self.create()
        self.telegram.failure = TelegramError(0, "Network request failed")
        self.delivery.flush()
        self.assertIsNone(self.app.session(sid)["progress_message_id"])
        self.restart()
        self.time += 10
        self.delivery.flush()
        self.assertIsNotNone(self.app.session(sid)["progress_message_id"])
        self.save(sid, 2, {1})
        self.delivery.flush()
        self.assertTrue(any(method == "editMessageText" for method, _ in self.telegram.calls))

    def test_malformed_callbacks_are_rejected_without_corrupting_state(self):
        sid = self.create()
        for data in ("toggle", f"toggle:{sid}:-1:0", f"save:{sid}", "launch:abc", "garbage:1"):
            with self.subTest(data=data):
                self.callback(2, data)
        self.assertEqual(self.app.view(sid).responses, {})

    def test_cancelled_new_wizard_does_not_change_live_round(self):
        sid = self.create()
        self.message(1, "/new")
        self.message(1, "/cancel")
        self.assertFalse(self.db.one("SELECT 1 FROM wizards"))
        self.assertEqual(self.app.session(sid)["state"], "open")

    def test_html_in_names_is_escaped(self):
        sid = self.create(people=[{"id": 2, "name": "<script>&Анна"}])
        self.assertIn("&lt;script&gt;&amp;Анна", views.progress_text(self.app.view(sid)))
        self.assertNotIn("<script>", views.progress_text(self.app.view(sid)))

    def test_discovery_group_picker_works_without_group_commands(self):
        self.app.discovery = True
        self.message(1, "/group")
        prompt = json.loads(self.db.one("SELECT payload FROM outbox ORDER BY id DESC LIMIT 1")[0])
        self.assertEqual(prompt["reply_markup"]["keyboard"][0][0]["request_chat"]["chat_is_channel"], False)
        self.message(1, "", chat_shared={"request_id": 402, "chat_id": -200, "title": "Наша группа"})
        selected = json.loads(self.db.one("SELECT value FROM metadata WHERE key='setup_group'")[0])
        self.assertEqual(selected["chat_id"], -200)
        self.assertEqual(selected["user_id"], 1)
        self.assertFalse(self.db.one("SELECT 1 FROM sessions"))
        self.message(2, "", chat_shared={"request_id": 402, "chat_id": -999, "title": "Чужая группа"})
        self.assertEqual(json.loads(self.db.one("SELECT value FROM metadata WHERE key='setup_group'")[0])["chat_id"], -200)


if __name__ == "__main__":
    unittest.main()
