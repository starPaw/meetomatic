"""Scheduling rules, independent of Telegram and persistence."""

from dataclasses import dataclass
from datetime import date as Date, datetime, time, timedelta, timezone
import re
from zoneinfo import ZoneInfo


PRAGUE = ZoneInfo("Europe/Prague")
DAYS = ("понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье")
DAY_ACCUSATIVE = ("понедельник", "вторник", "среду", "четверг", "пятницу", "субботу", "воскресенье")
DAY_SHORT = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")


class RuleError(ValueError):
    """An expected validation error that can be shown to a user."""


@dataclass(frozen=True)
class Slot:
    id: int
    day: int
    start: int
    duration: int
    date: str | None = None

    @property
    def label(self) -> str:
        day = f"{Date.fromisoformat(self.date):%d.%m.%Y}, {DAYS[Date.fromisoformat(self.date).weekday()]}" if self.date else DAYS[self.day]
        return f"{day}, {clock(self.start)}–{clock(self.start + self.duration)}"

    @property
    def starts_at(self) -> float | None:
        return local_timestamp(datetime.combine(Date.fromisoformat(self.date), time()) + timedelta(minutes=self.start)) if self.date else None


@dataclass(frozen=True)
class Candidate:
    slot: Slot
    available: tuple[int, ...]
    unavailable: tuple[int, ...]
    missing: tuple[int, ...]

    @property
    def common(self) -> bool:
        return bool(self.available) and not self.unavailable and not self.missing


def clock(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def parse_duration(text: str) -> int:
    if text.strip() in ("-", "По умолчанию"):
        return 60
    try:
        value = int(text)
    except ValueError as exc:
        raise RuleError("Укажите длительность в минутах, например 60.") from exc
    if not 30 <= value <= 480 or value % 30:
        raise RuleError("Длительность: от 30 до 480 минут с шагом 30 минут.")
    return value


def local_timestamp(local: datetime) -> float:
    """Resolve one Prague wall time, rejecting both gaps and repeated hours."""
    instants = set()
    for fold in (0, 1):
        stamp = local.replace(tzinfo=PRAGUE, fold=fold).timestamp()
        if datetime.fromtimestamp(stamp, PRAGUE).replace(tzinfo=None) == local:
            instants.add(stamp)
    if len(instants) != 1:
        raise RuleError("Это время попадает на перевод часов. Выберите однозначное время по Праге.")
    return instants.pop()


def parse_windows(text: str, duration: int, mode: str = "weekly", now: float | None = None) -> list[Slot]:
    parse_duration(str(duration))
    if mode not in ("weekly", "once"):
        raise RuleError("Выберите еженедельную или разовую встречу.")
    times: set[tuple[int, int]] = set()
    dates: dict[int, str] = {}
    current = utc_now() if now is None else now
    today = datetime.fromtimestamp(current, PRAGUE).date()
    for window in re.split(r"[;\n]+", text.strip()):
        match = re.fullmatch(
            (r"\s*(\d{4}-\d{2}-\d{2})\s+(\d{1,2}):(\d{2})\s*[-–—]\s*(\d{1,2}):(\d{2})\s*" if mode == "once" else
             r"\s*([а-яё, ]+)\s+(\d{1,2}):(\d{2})\s*[-–—]\s*(\d{1,2}):(\d{2})\s*"),
            window.lower(),
        )
        if not match:
            raise RuleError("Формат разовой встречи: 2026-11-02 18:00-21:00; 2026-11-09 18:00-21:00." if mode == "once" else "Формат диапазонов: вт 18:00-21:00; ср 18:00-21:00.")
        day_text, h1, m1, h2, m2 = match.groups()
        start, end = int(h1) * 60 + int(m1), int(h2) * 60 + int(m2)
        if int(h1) > 23 or int(h2) > 24 or int(m1) not in (0, 30) or int(m2) not in (0, 30):
            raise RuleError("Время задаётся с шагом 30 минут, от 00:00 до 24:00.")
        if end > 1440 or end - start < duration:
            raise RuleError("Встреча должна помещаться в диапазон одного дня; конец может быть 24:00.")
        if mode == "once":
            try:
                date = Date.fromisoformat(day_text)
            except ValueError as exc:
                raise RuleError("Укажите существующую дату встречи в формате ГГГГ-ММ-ДД.") from exc
            if not today <= date <= today + timedelta(days=365):
                raise RuleError("Выберите даты от сегодня до 365 дней вперёд.")
            day = date.toordinal()
            dates[day] = date.isoformat()
            if len(dates) > 7:
                raise RuleError("Можно предложить не больше 7 разных дат.")
            midnight = datetime.combine(date, time())
            stamps = {minute: local_timestamp(midnight + timedelta(minutes=minute)) for minute in range(start, end + 1, 30)}
            if stamps[start] <= current:
                raise RuleError("Все варианты разовой встречи должны быть в будущем.")
            for minute in range(start, end - duration + 1, 30):
                if stamps[minute + duration] - stamps[minute] != duration * 60:
                    raise RuleError("Встреча пересекает перевод часов. Выберите другой диапазон.")
                times.add((day, minute))
            continue
        for day_name in day_text.split(","):
            day_name = day_name.strip()
            if day_name in DAY_SHORT:
                day = DAY_SHORT.index(day_name)
            elif day_name in DAYS:
                day = DAYS.index(day_name)
            else:
                raise RuleError("Дни недели: пн, вт, ср, чт, пт, сб, вс.")
            times.update((day, minute) for minute in range(start, end - duration + 1, 30))
    if not times:
        raise RuleError("Нужен хотя бы один вариант встречи.")
    return [Slot(i, day, start, duration, dates.get(day)) for i, (day, start) in enumerate(sorted(times), 1)]


def parse_deadline(text: str, now: float) -> float:
    try:
        local = datetime.strptime(text.strip(), "%d.%m.%Y %H:%M")
    except ValueError as exc:
        raise RuleError("Срок по Праге: ДД.ММ.ГГГГ ЧЧ:ММ, например 25.10.2026 20:00.") from exc
    stamp = local_timestamp(local)
    if stamp <= now:
        raise RuleError("Срок ответа должен быть в будущем.")
    return stamp


def deadline_label(stamp: float) -> str:
    return datetime.fromtimestamp(stamp, PRAGUE).strftime("%d.%m.%Y %H:%M") + " по Праге"


def utc_now() -> float:
    return datetime.now(timezone.utc).timestamp()


def rank_candidates(
    slots: list[Slot], participants: list[int], responses: dict[int, set[int]],
) -> list[Candidate]:
    candidates = [
        Candidate(
            slot,
            tuple(uid for uid in participants if slot.id in responses.get(uid, set())),
            tuple(uid for uid in participants if uid in responses and slot.id not in responses[uid]),
            tuple(uid for uid in participants if uid not in responses),
        )
        for slot in slots
    ]
    return sorted(candidates, key=lambda c: (-len(c.available), c.slot.day, c.slot.start))
