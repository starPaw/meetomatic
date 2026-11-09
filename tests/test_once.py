from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import uuid

from bot_calendar.config import Config
from bot_calendar.domain import PRAGUE, RuleError, parse_windows
from bot_calendar.service import Application
from bot_calendar.storage import Database, SCHEMA, MIGRATION_2
from bot_calendar.web import act, state_for
from bot_calendar import views


NOW = datetime(2026, 10, 28, 12, tzinfo=timezone.utc).timestamp()


class OnceDomainTests(unittest.TestCase):
    def test_same_weekday_dates_are_independent_and_duplicates_are_merged(self):
        slots = parse_windows("2026-11-09 18:00-19:00; 2026-11-02 18:00-19:00; 2026-11-02 18:00-19:00", 60, "once", NOW)
        self.assertEqual([slot.date for slot in slots], ["2026-11-02", "2026-11-09"])
        self.assertEqual([slot.day for slot in slots], [date(2026, 11, 2).toordinal(), date(2026, 11, 9).toordinal()])
        self.assertIn("02.11.2026", slots[0].label)
        self.assertIn("понедельник", slots[0].label)
        self.assertNotEqual(slots[0].day, slots[1].day)

    def test_invalid_dates_bounds_and_mode_are_rejected(self):
        for windows in ("2026-02-30 18:00-19:00", "2026-10-27 18:00-19:00", "2026-10-28 12:00-13:00", "2027-10-29 18:00-19:00", "2026-11-02 23:30-24:30", "пн 18:00-19:00"):
            with self.subTest(windows=windows), self.assertRaises(RuleError):
                parse_windows(windows, 60, "once", NOW)
        with self.assertRaises(RuleError):
            parse_windows("пн 18:00-19:00", 60, "invalid", NOW)
        eight_dates = "; ".join(f"{date(2026, 11, 1) + timedelta(days=i)} 18:00-19:00" for i in range(8))
        with self.assertRaises(RuleError):
            parse_windows(eight_dates, 60, "once", NOW)

    def test_midnight_endpoint_and_weekly_compatibility(self):
        slot = parse_windows("2026-11-02 23:00-24:00", 60, "once", NOW)[0]
        self.assertTrue(slot.label.endswith("23:00–24:00"))
        self.assertEqual(datetime.fromtimestamp(slot.starts_at, PRAGUE).hour, 23)
        weekly = parse_windows("пн 18:00-19:00", 60)[0]
        self.assertEqual(weekly.day, 0)
        self.assertIsNone(weekly.date)
        self.assertIsNone(weekly.starts_at)

    def test_dst_gap_fold_and_crossing_are_rejected(self):
        now = datetime(2027, 1, 1, tzinfo=timezone.utc).timestamp()
        for windows in ("2027-03-28 02:00-03:00", "2027-03-28 01:00-04:00", "2027-10-31 02:00-03:00", "2027-10-31 01:00-04:00"):
            with self.subTest(windows=windows), self.assertRaises(RuleError):
                parse_windows(windows, 60, "once", now)
        self.assertEqual(len(parse_windows("2027-03-28 04:00-05:00", 60, "once", now)), 1)
        self.assertEqual(len(parse_windows("2027-10-31 04:00-05:00", 60, "once", now)), 1)


class OnceWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / "bot.sqlite3")
        self.config = Config("123:test", frozenset({1}), -100, self.path)
        self.time = NOW
        self.db = Database(self.path)
        self.app = Application(self.config, self.db, "meeting_test_bot", now=lambda: self.time)
        self.people = [{"id": 1, "name": "Организатор"}, {"id": 2, "name": "Анна"}]

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def create(self, **changes):
        args = dict(uid=1, people=self.people, duration=60,
                    windows="2026-11-02 18:00-19:00; 2026-11-09 18:00-19:00",
                    deadline=self.time + 3600, mode="once", new_meeting=True, title="Разовая встреча")
        args.update(changes)
        with self.db.transaction():
            return self.app.create_round(**args)

    def action(self, sid, uid, action, **body):
        with self.db.transaction():
            return act(self.app, {"id": uid}, {"action": action, "round": sid, "group": -100, **body})

    def voting(self):
        sid = self.create()
        for uid in (1, 2):
            self.action(sid, uid, "availability", slots=[1, 2], none=False)
        self.action(sid, 1, "close")
        self.action(sid, 1, "start_vote", slots=[1, 2])
        return sid

    def test_once_journey_votes_change_tie_privacy_and_date_publication(self):
        sid = self.voting()
        self.action(sid, 1, "vote", slot=1)
        self.action(sid, 1, "vote", slot=1)
        snapshot = state_for(self.app, {"id": 2}, sid)
        self.assertEqual(snapshot["round"]["voted_count"], 1)
        self.assertEqual(snapshot["round"]["voting_missing"], ["Анна"])
        self.assertEqual([p["voted"] for p in snapshot["round"]["participants"]], [True, False])
        self.assertNotIn("id", snapshot["round"]["participants"][0])
        self.assertNotIn("voters", snapshot["round"]["vote_options"][0])
        self.assertEqual(snapshot["round"]["mode"], "once")
        self.assertEqual(snapshot["round"]["slots"][0]["date"], "2026-11-02")
        self.assertEqual(snapshot["meetings"][0]["mode"], "once")
        self.action(sid, 2, "vote", slot=2)
        self.assertEqual(state_for(self.app, {"id": 1}, sid)["round"]["leaders"], [1, 2])
        self.action(sid, 1, "vote", slot=2)
        with self.assertRaises(RuleError):
            self.action(sid, 1, "confirm", slot=1)
        self.action(sid, 1, "confirm", slot=2)
        final = state_for(self.app, {"id": 1}, sid)
        self.assertEqual(final["schedule"]["date"], "2026-11-09")
        self.assertEqual(final["schedule"]["mode"], "once")
        self.assertIn("09.11.2026", final["schedule"]["text"])
        self.assertNotIn("кажд", final["schedule"]["text"])
        notification = json.loads(self.db.one("SELECT payload FROM outbox WHERE dedupe_key=?", (f"final:{sid}",))[0])
        self.assertIn("09.11.2026", notification["text"])
        with self.assertRaises(RuleError):
            self.action(sid, 1, "confirm", slot=2)
        self.assertEqual(self.db.one("SELECT COUNT(*) FROM outbox WHERE dedupe_key=?", (f"final:{sid}",))[0], 1)

    def test_web_creation_idempotence_and_once_deadline(self):
        body = dict(action="create", request_id=str(uuid.uuid4()), group=-100, title="Один раз", participants=self.people,
                    duration=60, windows="2026-11-02 18:00-19:00", deadline="2026-11-01T20:00", mode="once")
        with self.db.transaction():
            sid = act(self.app, {"id": 1}, body)
        with self.db.transaction():
            again = act(self.app, {"id": 1}, body)
        self.assertEqual(sid, again)
        self.assertEqual(self.db.one("SELECT COUNT(*) FROM sessions")[0], 1)
        start = self.app.view(sid).slots[0].starts_at
        for deadline in (start, start + 1):
            with self.subTest(deadline=deadline), self.assertRaises(RuleError):
                self.create(deadline=deadline)
        self.assertEqual(self.db.one("SELECT COUNT(*) FROM meetings")[0], 1)

    def test_past_votes_confirmation_and_availability_do_not_write(self):
        sid = self.voting()
        self.action(sid, 1, "vote", slot=1)
        self.time = self.app.view(sid).slots[0].starts_at
        for uid, action, body in ((2, "vote", {"slot": 1}), (1, "confirm", {"slot": 1}), (2, "availability", {"slots": [2]})):
            with self.subTest(action=action), self.assertRaises(RuleError):
                self.action(sid, uid, action, **body)
        self.assertEqual(self.app.view(sid).votes, {1: 1})
        self.assertEqual(self.app.view(sid).responses, {1: {1, 2}, 2: {1, 2}})
        self.assertIsNone(self.db.one("SELECT 1 FROM schedules"))
        self.assertTrue(state_for(self.app, {"id": 1}, sid)["round"]["vote_options"][0]["expired"])
        self.action(sid, 1, "vote", slot=2)
        self.action(sid, 1, "confirm", slot=2)
        self.assertEqual(self.app.session(sid)["state"], "final")

    def test_cannot_launch_vote_with_past_option(self):
        sid = self.create()
        self.time = self.app.view(sid).slots[0].starts_at
        self.app.tick()
        with self.assertRaises(RuleError):
            self.action(sid, 1, "start_vote", slots=[1], allow_partial=True)
        self.assertEqual(self.app.view(sid).nominations, [])
        self.assertEqual(self.app.session(sid)["state"], "closed")

    def test_repeat_keeps_mode_and_old_result_is_not_replaced_by_new_schedule(self):
        first = self.voting()
        self.action(first, 1, "vote", slot=1)
        self.action(first, 1, "confirm", slot=1)
        mid = self.app.session(first)["meeting_id"]
        with self.assertRaises(RuleError):
            self.create(meeting_id=mid, mode="weekly", windows="пн 18:00-19:00")
        second = self.create(meeting_id=mid, windows="2026-11-10 20:00-21:00")
        self.assertEqual(state_for(self.app, {"id": 1}, second)["schedule"]["session_id"], first)
        for uid in (1, 2):
            self.action(second, uid, "availability", slots=[1], none=False)
        self.action(second, 1, "close")
        self.action(second, 1, "start_vote", slots=[1])
        self.action(second, 1, "vote", slot=1)
        self.action(second, 1, "confirm", slot=1)
        old = state_for(self.app, {"id": 1}, first)
        self.assertEqual(old["schedule"]["date"], "2026-11-02")
        self.assertEqual(old["meetings"][0]["schedule"]["date"], "2026-11-10")
        self.assertEqual(state_for(self.app, {"id": 1}, second)["schedule"]["date"], "2026-11-10")

    def test_once_authorization_and_cancelled_round_guards(self):
        sid = self.voting()
        for uid, action, body in ((99, "vote", {"slot": 1}), (2, "confirm", {"slot": 1}), (99, "availability", {"slots": [1]})):
            with self.subTest(action=action), self.assertRaises(RuleError):
                self.action(sid, uid, action, **body)
        self.create(meeting_id=self.app.session(sid)["meeting_id"])
        for action, body in (("vote", {"slot": 1}), ("confirm", {"slot": 1}), ("availability", {"slots": [1]})):
            with self.subTest(action=action), self.assertRaises(RuleError):
                self.action(sid, 1, action, **body)
        self.assertEqual(self.app.session(sid)["state"], "cancelled")
        self.assertFalse(self.app.view(sid).votes)

    def test_once_views_and_reminder_deadline_keep_date_context(self):
        sid = self.create()
        view = self.app.view(sid)
        self.assertNotIn("обычной недели", views.app_progress_text(view))
        self.assertNotIn("Обычная неделя", views.availability_view(view, set())[0])
        self.assertIn("02.11.2026", views.result_text(view))
        self.time += 1801
        self.app.tick()
        self.assertEqual(self.db.one("SELECT COUNT(*) FROM outbox WHERE kind='reminder'")[0], 1)
        self.time += 1800
        self.app.tick()
        self.assertEqual(self.app.session(sid)["state"], "closed")


class OnceMigrationTests(unittest.TestCase):
    def v2_database(self, path):
        with sqlite3.connect(path) as con:
            con.executescript(SCHEMA)
            con.executescript(MIGRATION_2)
            con.execute("INSERT INTO groups VALUES (-100,'Группа',1,1,1)")
            con.execute("INSERT INTO group_organizers VALUES (-100,1)")
            con.execute("INSERT INTO meetings VALUES (1,-100,'Встреча',1,1)")
            con.execute("INSERT INTO sessions(id,group_id,organizer_id,state,duration,windows,deadline,reminder_at,created_at,meeting_id,nominations,chosen_slot) VALUES (1,-100,1,'final',60,'пн 18:00-19:00',1,1,1,1,'[1]',1)")
            con.execute("INSERT INTO participants VALUES (1,1,'Организатор')")
            con.execute("INSERT INTO slots VALUES (1,1,0,1080)")
            con.execute("INSERT INTO answers VALUES (1,1,0,1)")
            con.execute("INSERT INTO availability VALUES (1,1,1)")
            con.execute("INSERT INTO votes VALUES (1,1,1)")
            con.execute("INSERT INTO schedules VALUES (1,-100,1,0,1080,60,1)")
            con.execute("INSERT INTO metadata VALUES ('offset','123')")
            con.execute("INSERT INTO outbox(kind,payload,dedupe_key,state,created_at) VALUES ('message','{}','final:1','sent',1)")

    def test_v2_upgrade_preserves_results_votes_schedule_and_outbox(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "v2.sqlite3")
            self.v2_database(path)
            db = Database(path)
            try:
                self.assertEqual(db.one("PRAGMA user_version")[0], 3)
                for table in ("meetings", "sessions", "schedules"):
                    self.assertEqual(db.one(f"SELECT mode FROM {table}")[0], "weekly")
                self.assertIsNone(db.one("SELECT date FROM slots")[0])
                self.assertIsNone(db.one("SELECT date FROM schedules")[0])
                self.assertEqual(tuple(db.one("SELECT * FROM votes")), (1, 1, 1))
                self.assertEqual(tuple(db.one("SELECT * FROM availability")), (1, 1, 1))
                self.assertEqual(db.offset, 123)
                self.assertEqual(db.one("SELECT state FROM outbox")[0], "sent")
                self.assertEqual(db.all("PRAGMA foreign_key_check"), [])
            finally:
                db.close()
            Database(path).close()

    def test_failed_v3_migration_is_atomic(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "v2.sqlite3")
            self.v2_database(path)
            with sqlite3.connect(path) as con:
                con.execute("ALTER TABLE slots ADD COLUMN date TEXT")
            with self.assertRaises(sqlite3.OperationalError):
                Database(path)
            with sqlite3.connect(path) as con:
                self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], 2)
                self.assertNotIn("mode", [row[1] for row in con.execute("PRAGMA table_info(meetings)")])
                self.assertEqual(con.execute("SELECT COUNT(*) FROM votes").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
