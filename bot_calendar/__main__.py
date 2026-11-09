"""Run with python3 -m bot_calendar. Only one process may own the database."""

import argparse
from contextlib import contextmanager
import fcntl
import logging
import os
from pathlib import Path
import signal
import sys
import threading

from .config import Config, load_env
from .service import Application
from .storage import Database
from .telegram import Delivery, TelegramClient, TelegramError


log = logging.getLogger(__name__)


@contextmanager
def process_lock(database: str):
    path = Path(database + ".lock")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Another bot process already owns this database") from None
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def preflight(client: TelegramClient, config: Config) -> dict:
    identity = client.call("getMe")
    info = client.call("getWebhookInfo")
    if info.get("url"):
        raise ValueError("A webhook is configured; remove it explicitly before using long polling")
    # Groups are verified independently when connected. Losing a legacy group
    # must not prevent the bot from serving its other connected groups.
    return identity


def run(config: Config, discovery: bool, identity: dict, client: TelegramClient):
    stop = threading.Event()
    wake = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    with process_lock(config.database):
        db = Database(config.database)
        web_server, web_thread, delivery_thread = None, None, None
        worker_errors = []
        try:
            app = Application(config, db, identity["username"], discovery=discovery)
            def deliver_messages():
                worker_db = None
                try:
                    worker_db = Database(config.database, initialize=False)
                    worker_app = Application(config, worker_db, identity["username"], discovery=discovery)
                    delivery = Delivery(worker_app, client)
                    while not stop.is_set():
                        worker_app.tick()
                        delivery.flush()
                        wake.wait(1)
                        wake.clear()
                except Exception as exc:
                    log.exception("Delivery worker failed")
                    worker_errors.append(exc)
                    stop.set()
                finally:
                    if worker_db:
                        worker_db.close()
            delivery_thread = threading.Thread(target=deliver_messages, name="delivery", daemon=True)
            delivery_thread.start()
            if config.webapp_url and not discovery:
                from .web import MiniAppServer
                web_server = MiniAppServer(config, identity["username"], wake, telegram=client)
                web_thread = threading.Thread(target=web_server.serve_forever, name="mini-app", daemon=True)
                web_thread.start()
                client.call("setChatMenuButton", menu_button={"type": "web_app", "text": "Встреча", "web_app": {"url": config.webapp_url + "/"}})
                log.info("Mini App listening on %s:%s", config.web_host, config.web_port)
            commands = [("whoami", "Ваш ID и ID чата"), ("group", "Выбрать группу для настройки")] if discovery else [
                ("help", "Инструкция"), ("join", "Зарегистрироваться"), ("whoami", "ID пользователя и чата"),
                ("status", "Прогресс ответов"), ("schedule", "Расписание"), ("new", "Новый подбор: организатор"),
                ("results", "Результаты: организатор"), ("answers", "Подробные ответы: организатор"),
                ("close", "Закрыть сбор: организатор"), ("vote", "Начать голосование: организатор"),
                ("confirm", "Подтвердить время: организатор"), ("repeat", "Повторить подбор: организатор"),
                ("cancel", "Отменить создание"),
            ]
            if config.webapp_url and not discovery:
                commands = [("app", "Встречи и выбор времени"), ("group", "Подключить группу"), ("help", "Открыть приложение"), ("whoami", "Ваш ID и ID чата")]
            client.call("setMyCommands", commands=[{"command": cmd, "description": description} for cmd, description in commands])
            log.info("Bot @%s started (%s)", identity["username"], "discovery" if discovery else "normal")
            while not stop.is_set():
                try:
                    updates = client.call("getUpdates", offset=app.poll_offset(), timeout=20, limit=50,
                                          allowed_updates=["message", "callback_query", "my_chat_member"])
                except TelegramError as exc:
                    if exc.code in (401, 403, 409):
                        raise
                    log.warning("Polling failed, code=%s; will retry", exc.code)
                    stop.wait(max(3, min(exc.retry_after, 30)))
                    continue
                for update in updates:
                    app.process(update)
                if updates:
                    wake.set()
            if worker_errors:
                raise RuntimeError("Delivery worker stopped unexpectedly") from worker_errors[0]
            log.info("Bot stopped cleanly")
        finally:
            stop.set()
            wake.set()
            if web_server:
                web_server.shutdown()
                web_server.server_close()
            if web_thread:
                web_thread.join(5)
            if delivery_thread:
                delivery_thread.join(40)
            db.close()


def main() -> int:
    os.umask(0o077)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    parser = argparse.ArgumentParser(description="Prague weekly meeting bot")
    parser.add_argument("--discover", action="store_true", help="Only answer /whoami and /start with setup IDs")
    parser.add_argument("--check", action="store_true", help="Validate configuration and Telegram access; do not poll or send messages")
    args = parser.parse_args()
    try:
        load_env()
        discovery = args.discover or os.environ.get("BOT_DISCOVERY") == "1"
        config = Config.from_env(discovery=discovery)
        client = TelegramClient(config.token)
        identity = preflight(client, config)
        if args.check:
            print(f"Telegram OK: @{identity['username']}; webhook absent; mode={'discovery' if discovery else 'normal'}")
            return 0
        run(config, discovery, identity, client)
        return 0
    except (ValueError, TelegramError) as exc:
        log.error("%s", exc)
        return 1
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
