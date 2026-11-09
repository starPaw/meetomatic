import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from bot_calendar.__main__ import preflight, process_lock
from bot_calendar.config import Config
from bot_calendar.telegram import TelegramClient, TelegramError


class RuntimeTests(unittest.TestCase):
    def test_configuration_allows_group_onboarding_without_legacy_ids(self):
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "123:test"}, clear=True), patch("bot_calendar.config.load_env"):
            self.assertEqual(Config.from_env(discovery=True).group_id, 0)
            self.assertEqual(Config.from_env().group_id, 0)
        values = {"TELEGRAM_BOT_TOKEN": "123:test", "ORGANIZER_IDS": "1,2", "GROUP_CHAT_ID": "-100"}
        with patch.dict(os.environ, values, clear=True), patch("bot_calendar.config.load_env"):
            self.assertEqual(Config.from_env().organizers, {1, 2})
            self.assertFalse(Config.from_env().webapp_direct)
        with patch.dict(os.environ, {**values, "WEBAPP_URL": "https://meeting.example", "WEBAPP_DIRECT_LINKS": "1"}, clear=True), patch("bot_calendar.config.load_env"):
            self.assertTrue(Config.from_env().webapp_direct)
        with patch.dict(os.environ, {**values, "ORGANIZER_IDS": ""}, clear=True), patch("bot_calendar.config.load_env"), self.assertRaises(ValueError):
            Config.from_env()

    def test_only_one_process_can_lock_database(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "bot.sqlite3")
            with process_lock(path):
                with self.assertRaises(ValueError):
                    with process_lock(path):
                        self.fail("A second process acquired the lock")
            with process_lock(path):
                pass

    def test_unavailable_legacy_group_does_not_block_other_groups_at_startup(self):
        class Client:
            def call(self, method, **payload):
                if method == "getMe":
                    return {"id": 123, "username": "meeting_bot"}
                if method == "getWebhookInfo":
                    return {}
                raise TelegramError(403, "Legacy group no longer available")
        identity = preflight(Client(), Config("123:test", frozenset({1}), -100))
        self.assertEqual(identity["id"], 123)

    def test_network_errors_never_expose_token(self):
        token = "123:secret-test-token"
        client = TelegramClient(token)
        with patch("bot_calendar.telegram.urlopen", side_effect=URLError("Failed https://api.telegram.org/bot" + token)):
            with self.assertRaises(TelegramError) as caught:
                client.call("getMe")
        self.assertNotIn(token, str(caught.exception))
        self.assertNotIn(token, caught.exception.description)

    def test_http_rate_limit_preserves_retry_after_and_redacts_description(self):
        token = "123:secret-test-token"
        body = {"ok": False, "error_code": 429, "description": "limited " + token, "parameters": {"retry_after": 7}}
        error = HTTPError("https://api.telegram.org/bot" + token, 429, "limited", {}, io.BytesIO(json.dumps(body).encode()))
        with patch("bot_calendar.telegram.urlopen", side_effect=error):
            with self.assertRaises(TelegramError) as caught:
                TelegramClient(token).call("sendMessage", chat_id=-100, text="test")
        self.assertEqual(caught.exception.retry_after, 7)
        self.assertNotIn(token, caught.exception.description)


if __name__ == "__main__":
    unittest.main()
