"""Russian Telegram views. Participant details stay in private organizer chats."""

from dataclasses import dataclass, field
from html import escape
from datetime import date as Date

from .domain import Candidate, DAYS, DAY_ACCUSATIVE, Slot, clock, deadline_label, rank_candidates


def button(text: str, data: str) -> dict:
    return {"text": text, "callback_data": data}


def keyboard(rows: list[list[dict]]) -> dict:
    return {"inline_keyboard": rows}


@dataclass
class RoundView:
    id: int
    state: str
    duration: int
    deadline: float
    names: dict[int, str]
    slots: list[Slot]
    responses: dict[int, set[int]]
    nominations: list[int] = field(default_factory=list)
    votes: dict[int, int] = field(default_factory=dict)
    results_visible: bool = False
    title: str = "Еженедельная встреча"
    group_id: int = 0
    meeting_id: int = 0
    mode: str = "weekly"

    @property
    def candidates(self) -> list[Candidate]:
        return rank_candidates(self.slots, list(self.names), self.responses)

    @property
    def top(self) -> list[Candidate]:
        candidates = self.candidates
        common = [candidate for candidate in candidates if candidate.common]
        return (common or candidates)[:3]

    @property
    def missing(self) -> list[int]:
        return [uid for uid in self.names if uid not in self.responses]


def result_text(view: RoundView, details: bool = False) -> str:
    lines = [f"<b>{escape(view.title)} · результат #{view.id}</b>"]
    if view.missing:
        lines.append("⚠️ Предварительный результат: ответили не все.")
    elif view.top and view.top[0].common:
        lines.append("Есть время, которое подходит всем.")
    else:
        lines.append("Общего времени нет. Ниже варианты с наибольшим числом участников.")
    if view.missing:
        lines.append("Подтверждённого общего времени пока нет.")
    total = len(view.names)
    for candidate in view.top:
        suffix = " — подходит всем" if candidate.common else ""
        lines.append(f"\n№{candidate.slot.id}: {candidate.slot.label} — {len(candidate.available)}/{total}{suffix}")
        if details:
            lines.append("Не могут: " + (", ".join(escape(view.names[uid]) for uid in candidate.unavailable) or "никого"))
            lines.append("Нет ответа: " + (", ".join(escape(view.names[uid]) for uid in candidate.missing) or "никого"))
    lines.append("\nВыбираем одну дату и время по Праге (Europe/Prague)." if view.mode == "once" else "\nВремя для обычной недели, по Праге (Europe/Prague).")
    return "\n".join(lines)


def progress_text(view: RoundView) -> str:
    states = {"open": "Сбор открыт", "closed": "Сбор закрыт", "voting": "Финальное голосование", "final": "Подбор завершён", "cancelled": "Подбор заменён новым"}
    lines = [f"<b>{escape(view.title)} · #{view.id}</b>", states[view.state],
             f"Длительность: {view.duration} мин. Шаг начала: 30 мин.",
             f"Ответить до: {deadline_label(view.deadline)}",
             f"Ответили: {len(view.responses)}/{len(view.names)}"]
    if view.missing:
        lines.append("Ждём: " + ", ".join(escape(view.names[uid]) for uid in view.missing))
    else:
        lines.append("Все участники ответили." + (" Ответы можно менять до закрытия сбора." if view.state == "open" else ""))
    if view.state == "open":
        lines.append("\nОтметьте все удобные интервалы для обычной недели в личном чате с ботом.")
    if view.results_visible or not view.missing:
        lines.append("\n" + result_text(view))
    return "\n".join(lines)


def app_progress_text(view: RoundView) -> str:
    states = {"open": "Выбираем удобное время", "closed": "Сбор закрыт — выбираем варианты",
              "voting": "Идёт финальное голосование", "final": "Время встречи выбрано", "cancelled": "Подбор заменён новым"}
    lines = [f"<b>{escape(view.title)} · #{view.id}</b>", states[view.state],
             f"Длительность: {view.duration} мин. Всё время — по Праге.",
             f"Ответили о доступности: {len(view.responses)} из {len(view.names)}."]
    if view.missing:
        lines.append("Ещё ждём: " + ", ".join(escape(view.names[uid]) for uid in view.missing))
    if view.state == "open":
        lines += [f"Ответить до: {deadline_label(view.deadline)}", "\nОтметьте подходящие интервалы в предложенные даты в приложении." if view.mode == "once" else "\nОтметьте все подходящие интервалы для обычной недели в приложении."]
    elif view.state == "voting":
        lines.append(f"Проголосовали: {len(view.votes)} из {len(view.names)}.")
        lines.append("Голосуют: " + ", ".join(escape(name) for name in view.names.values()))
        lines.append("\nОткройте приложение, чтобы проголосовать. Организатор подтверждает итог после голосования.")
    elif view.state == "closed":
        lines.append("\nРезультаты и выбор вариантов — в приложении.")
    return "\n".join(lines)


def availability_view(view: RoundView, selected: set[int], page: int = 0) -> tuple[str, dict]:
    size = 8
    pages = max(1, (len(view.slots) + size - 1) // size)
    page = max(0, min(page, pages - 1))
    rows = [[button(("✓ " if slot.id in selected else "□ ") + slot.label,
                    f"toggle:{view.id}:{slot.id}:{page}")]
            for slot in view.slots[page * size:(page + 1) * size]]
    if pages > 1:
        rows.append([button("←", f"page:{view.id}:{(page - 1) % pages}"),
                     button(f"{page + 1}/{pages}", f"page:{view.id}:{page}"),
                     button("→", f"page:{view.id}:{(page + 1) % pages}")])
    rows += [[button("Сохранить выбранное", f"save:{view.id}:{page}")],
             [button("Ни один вариант не подходит", f"none:{view.id}:{page}")]]
    text = (f"<b>Ваше время · подбор #{view.id}</b>\n"
            f"{'Предложенные даты' if view.mode == 'once' else 'Обычная неделя'}, время по Праге. Длительность {view.duration} мин.\n"
            f"Выбрано: {len(selected)}. Изменения применятся после «Сохранить выбранное».\n"
            "Кнопка «Ни один вариант не подходит» сразу сохраняет явный отказ.\n"
            f"Менять ответ можно до {deadline_label(view.deadline)} или закрытия организатором.")
    return text, keyboard(rows)


def organizer_keyboard(view: RoundView) -> dict:
    if view.state == "open":
        return keyboard([[button("Закрыть сбор", f"close:{view.id}")]])
    if view.state != "closed":
        return keyboard([])
    rows = [[button(("✓ " if candidate.slot.id in view.nominations else "□ ") + candidate.slot.label,
                    f"nominate:{view.id}:{candidate.slot.id}")] for candidate in view.top]
    rows.append([button("Начать финальное голосование", f"launch:{view.id}")])
    return keyboard(rows)


def vote_text(view: RoundView) -> str:
    counts = {sid: list(view.votes.values()).count(sid) for sid in view.nominations}
    lines = [f"<b>{escape(view.title)} · подтверждение #{view.id}</b>",
             "Каждый ожидаемый участник выбирает один вариант. Голос можно изменить до решения организатора."]
    if any(not candidate.common for candidate in view.candidates if candidate.slot.id in view.nominations):
        lines.append("Организатор явно разрешил голосование за варианты, не подтверждённые всеми.")
    if view.missing:
        lines.append("Доступность предварительная: ответили не все.")
    for slot in view.slots:
        if slot.id in counts:
            candidate = next(candidate for candidate in view.candidates if candidate.slot.id == slot.id)
            lines.append(f"№{slot.id}: {slot.label} — доступны {len(candidate.available)}/{len(view.names)}, голосов: {counts[slot.id]}")
    lines.append(f"Проголосовали: {len(view.votes)}/{len(view.names)}")
    if view.state == "voting":
        waiting = [uid for uid in view.names if uid not in view.votes]
        if waiting:
            lines.append("Ждём голос: " + ", ".join(escape(view.names[uid]) for uid in waiting))
    if view.state != "voting":
        lines.append("Голосование закрыто.")
    return "\n".join(lines)


def vote_keyboard(view: RoundView) -> dict:
    if view.state != "voting":
        return keyboard([])
    return keyboard([[button(slot.label, f"vote:{view.id}:{slot.id}")]
                     for slot in view.slots if slot.id in view.nominations])


def decision_view(view: RoundView) -> tuple[str, dict]:
    counts = {sid: list(view.votes.values()).count(sid) for sid in view.nominations}
    best = max(counts.values(), default=0)
    leaders = [sid for sid, count in counts.items() if count == best]
    lines = [vote_text(view)]
    if not view.votes:
        lines.append("\nГолосов ещё нет. Подтверждение будет доступно после первого голоса.")
        return "\n".join(lines), keyboard([])
    if len(leaders) > 1:
        lines.append("\nГолоса разделились поровну. Выберите итоговый вариант из лидеров.")
    else:
        lines.append("\nПодтвердите вариант с наибольшим числом голосов.")
    if len(view.votes) < len(view.names):
        lines.append("Ответили не все: подтверждение сейчас явно завершит голосование досрочно.")
    return "\n".join(lines), keyboard([
        [button("Подтвердить: " + slot.label, f"confirm:{view.id}:{slot.id}")]
        for slot in view.slots if slot.id in leaders
    ])


def schedule_text(day: int, start: int, duration: int, date: str | None = None) -> str:
    if date:
        selected_date = Date.fromisoformat(date)
        return (f"Встречаемся {selected_date:%d.%m.%Y} ({DAYS[selected_date.weekday()]}), "
                f"{clock(start)}–{clock(start + duration)} по Праге.\nДлительность: {duration} мин. Разовая встреча.")
    every = "каждый" if day in (0, 1, 3) else ("каждое" if day == 6 else "каждую")
    return (f"Встречаемся {every} {DAY_ACCUSATIVE[day]}, "
            f"{clock(start)}–{clock(start + duration)} по Праге.\n"
            f"Длительность: {duration} мин. Местное время сохраняется при переводе часов.")
