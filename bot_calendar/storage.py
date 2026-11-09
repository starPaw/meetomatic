"""SQLite schema and small transaction/outbox helpers."""

from contextlib import contextmanager
import json
from pathlib import Path
import secrets
import sqlite3


SCHEMA = """
CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY, name TEXT NOT NULL, username TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS usernames ON users(username) WHERE username IS NOT NULL;
CREATE TABLE IF NOT EXISTS wizards (
    user_id INTEGER PRIMARY KEY, token TEXT NOT NULL, step TEXT NOT NULL, data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, group_id INTEGER NOT NULL,
    organizer_id INTEGER NOT NULL, state TEXT NOT NULL
        CHECK(state IN ('open','closed','voting','final','cancelled')),
    duration INTEGER NOT NULL, windows TEXT NOT NULL, deadline REAL NOT NULL,
    reminder_at REAL NOT NULL, reminder_queued INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL, progress_message_id INTEGER, vote_message_id INTEGER,
    results_visible INTEGER NOT NULL DEFAULT 0, nominations TEXT NOT NULL DEFAULT '[]',
    partial_approved INTEGER NOT NULL DEFAULT 0, chosen_slot INTEGER
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_session ON sessions(group_id)
    WHERE state IN ('open','closed','voting');
CREATE TABLE IF NOT EXISTS participants (
    session_id INTEGER NOT NULL REFERENCES sessions(id), user_id INTEGER NOT NULL,
    name TEXT NOT NULL, PRIMARY KEY(session_id,user_id)
);
CREATE TABLE IF NOT EXISTS slots (
    session_id INTEGER NOT NULL REFERENCES sessions(id), slot_id INTEGER NOT NULL,
    day INTEGER NOT NULL, start INTEGER NOT NULL, PRIMARY KEY(session_id,slot_id)
);
CREATE TABLE IF NOT EXISTS answers (
    session_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
    explicit_none INTEGER NOT NULL CHECK(explicit_none IN (0,1)), updated_at REAL NOT NULL,
    PRIMARY KEY(session_id,user_id),
    FOREIGN KEY(session_id,user_id) REFERENCES participants(session_id,user_id)
);
CREATE TABLE IF NOT EXISTS availability (
    session_id INTEGER NOT NULL, user_id INTEGER NOT NULL, slot_id INTEGER NOT NULL,
    PRIMARY KEY(session_id,user_id,slot_id),
    FOREIGN KEY(session_id,user_id) REFERENCES answers(session_id,user_id),
    FOREIGN KEY(session_id,slot_id) REFERENCES slots(session_id,slot_id)
);
CREATE TABLE IF NOT EXISTS drafts (
    session_id INTEGER NOT NULL, user_id INTEGER NOT NULL, selected TEXT NOT NULL,
    PRIMARY KEY(session_id,user_id),
    FOREIGN KEY(session_id,user_id) REFERENCES participants(session_id,user_id)
);
CREATE TABLE IF NOT EXISTS votes (
    session_id INTEGER NOT NULL, user_id INTEGER NOT NULL, slot_id INTEGER NOT NULL,
    PRIMARY KEY(session_id,user_id),
    FOREIGN KEY(session_id,user_id) REFERENCES participants(session_id,user_id),
    FOREIGN KEY(session_id,slot_id) REFERENCES slots(session_id,slot_id)
);
CREATE TABLE IF NOT EXISTS schedules (
    group_id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL REFERENCES sessions(id),
    day INTEGER NOT NULL, start INTEGER NOT NULL, duration INTEGER NOT NULL,
    confirmed_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, payload TEXT NOT NULL,
    dedupe_key TEXT UNIQUE, attempts INTEGER NOT NULL DEFAULT 0,
    next_attempt REAL NOT NULL DEFAULT 0, state TEXT NOT NULL DEFAULT 'pending',
    last_error TEXT, created_at REAL NOT NULL
);
PRAGMA user_version = 1;
"""


MIGRATION_2 = """
BEGIN IMMEDIATE;
CREATE TABLE groups (
    id INTEGER PRIMARY KEY CHECK(id < 0), title TEXT NOT NULL,
    connected_by INTEGER NOT NULL, created_at REAL NOT NULL, active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE group_organizers (
    group_id INTEGER NOT NULL REFERENCES groups(id), user_id INTEGER NOT NULL,
    PRIMARY KEY(group_id,user_id)
);
CREATE TABLE group_members (
    group_id INTEGER NOT NULL REFERENCES groups(id), user_id INTEGER NOT NULL,
    PRIMARY KEY(group_id,user_id)
);
CREATE TABLE meetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT, group_id INTEGER NOT NULL REFERENCES groups(id),
    title TEXT NOT NULL, created_by INTEGER NOT NULL, created_at REAL NOT NULL
);
INSERT INTO groups(id,title,connected_by,created_at)
    SELECT group_id,'Наша группа',MIN(organizer_id),MIN(created_at) FROM sessions GROUP BY group_id;
INSERT INTO group_organizers SELECT DISTINCT group_id,organizer_id FROM sessions;
INSERT INTO group_members SELECT DISTINCT s.group_id,p.user_id FROM participants p JOIN sessions s ON s.id=p.session_id;
INSERT INTO meetings(group_id,title,created_by,created_at)
    SELECT id,'Еженедельная встреча',connected_by,created_at FROM groups;
ALTER TABLE sessions ADD COLUMN meeting_id INTEGER REFERENCES meetings(id);
UPDATE sessions SET meeting_id=(SELECT id FROM meetings WHERE meetings.group_id=sessions.group_id);
DROP INDEX one_active_session;
CREATE UNIQUE INDEX one_active_meeting_round ON sessions(meeting_id) WHERE state IN ('open','closed','voting');
CREATE INDEX meeting_rounds ON sessions(meeting_id,id);
CREATE TRIGGER session_meeting_group_insert BEFORE INSERT ON sessions
    WHEN NOT EXISTS(SELECT 1 FROM meetings WHERE id=NEW.meeting_id AND group_id=NEW.group_id)
    BEGIN SELECT RAISE(ABORT,'Meeting and group do not match'); END;
CREATE TRIGGER session_meeting_group_update BEFORE UPDATE OF meeting_id,group_id ON sessions
    WHEN NOT EXISTS(SELECT 1 FROM meetings WHERE id=NEW.meeting_id AND group_id=NEW.group_id)
    BEGIN SELECT RAISE(ABORT,'Meeting and group do not match'); END;
ALTER TABLE schedules RENAME TO legacy_schedules;
CREATE TABLE schedules (
    meeting_id INTEGER PRIMARY KEY REFERENCES meetings(id), group_id INTEGER NOT NULL REFERENCES groups(id),
    session_id INTEGER NOT NULL REFERENCES sessions(id), day INTEGER NOT NULL,
    start INTEGER NOT NULL, duration INTEGER NOT NULL, confirmed_at REAL NOT NULL
);
INSERT INTO schedules SELECT s.meeting_id,l.group_id,l.session_id,l.day,l.start,l.duration,l.confirmed_at
    FROM legacy_schedules l JOIN sessions s ON s.id=l.session_id;
DROP TABLE legacy_schedules;
CREATE TRIGGER schedule_meeting_group_insert BEFORE INSERT ON schedules
    WHEN NOT EXISTS(SELECT 1 FROM sessions WHERE id=NEW.session_id AND meeting_id=NEW.meeting_id AND group_id=NEW.group_id)
    BEGIN SELECT RAISE(ABORT,'Schedule and meeting do not match'); END;
CREATE TRIGGER schedule_meeting_group_update BEFORE UPDATE ON schedules
    WHEN NOT EXISTS(SELECT 1 FROM sessions WHERE id=NEW.session_id AND meeting_id=NEW.meeting_id AND group_id=NEW.group_id)
    BEGIN SELECT RAISE(ABORT,'Schedule and meeting do not match'); END;
PRAGMA user_version = 2;
COMMIT;
"""


MIGRATION_3 = """
BEGIN IMMEDIATE;
ALTER TABLE meetings ADD COLUMN mode TEXT NOT NULL DEFAULT 'weekly' CHECK(mode IN ('weekly','once'));
ALTER TABLE sessions ADD COLUMN mode TEXT NOT NULL DEFAULT 'weekly' CHECK(mode IN ('weekly','once'));
ALTER TABLE slots ADD COLUMN date TEXT;
ALTER TABLE schedules ADD COLUMN mode TEXT NOT NULL DEFAULT 'weekly' CHECK(mode IN ('weekly','once'));
ALTER TABLE schedules ADD COLUMN date TEXT;
PRAGMA user_version = 3;
COMMIT;
"""


class Database:
    def __init__(self, path: str, initialize: bool = True):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.connection = sqlite3.connect(path, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA busy_timeout = 5000")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = FULL")
        version = self.connection.execute("PRAGMA user_version").fetchone()[0]
        if version > 3:
            raise RuntimeError("Database schema is newer than this application")
        if initialize:
            if version == 0:
                self.connection.executescript(SCHEMA)
                version = 1
            if version == 1:
                try:
                    self.connection.executescript(MIGRATION_2)
                except BaseException:
                    if self.connection.in_transaction:
                        self.connection.rollback()
                    raise
                version = 2
            if version == 2:
                try:
                    self.connection.executescript(MIGRATION_3)
                except BaseException:
                    if self.connection.in_transaction:
                        self.connection.rollback()
                    raise

    def execute(self, sql: str, params=()):
        return self.connection.execute(sql, params)

    def one(self, sql: str, params=()):
        return self.execute(sql, params).fetchone()

    def all(self, sql: str, params=()):
        return self.execute(sql, params).fetchall()

    @contextmanager
    def transaction(self):
        self.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self.execute("ROLLBACK")
            raise
        else:
            self.execute("COMMIT")

    @property
    def offset(self) -> int:
        row = self.one("SELECT value FROM metadata WHERE key='offset'")
        return int(row[0]) if row else 0

    def set_offset(self, value: int):
        self.execute(
            "INSERT INTO metadata VALUES ('offset',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(value),),
        )

    def enqueue(self, kind: str, payload: dict, now: float, key: str | None = None):
        self.execute(
            "INSERT OR IGNORE INTO outbox(kind,payload,dedupe_key,created_at) VALUES (?,?,?,?)",
            (kind, json.dumps(payload, ensure_ascii=False), key, now),
        )

    def refresh(self, session_id: int, target: str, now: float):
        # An update arriving during network delivery must survive the old acknowledgement.
        payload = json.dumps({"session_id": session_id, "target": target, "revision": secrets.token_hex(8)})
        self.execute("INSERT INTO outbox(kind,payload,dedupe_key,created_at) VALUES ('refresh',?,?,?) "
                     "ON CONFLICT(dedupe_key) DO UPDATE SET payload=excluded.payload,state='pending',next_attempt=0,last_error=NULL",
                     (payload, f"refresh:{session_id}:{target}", now))

    def close(self):
        self.connection.close()
