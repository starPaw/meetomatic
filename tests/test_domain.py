from datetime import datetime, timezone
import unittest

from bot_calendar.domain import PRAGUE, RuleError, Slot, parse_deadline, parse_duration, parse_windows, rank_candidates
from bot_calendar.views import RoundView, result_text, schedule_text


class DomainTests(unittest.TestCase):
    def test_half_hour_starts_fit_duration_and_windows_are_deduplicated(self):
        slots = parse_windows("вт,чт 18:00-20:00; вт 18:30-20:00", 60)
        self.assertEqual([(s.day, s.start) for s in slots], [(1, 1080), (1, 1110), (1, 1140), (3, 1080), (3, 1110), (3, 1140)])
        self.assertEqual([s.id for s in slots], list(range(1, 7)))

    def test_invalid_ranges_and_duration(self):
        for text in ("вт 18:15-20:00", "вт 23:30-01:00", "вт 18:00-18:30", "вт 23:00-24:30", "xy 18:00-20:00", ""):
            with self.subTest(text=text), self.assertRaises(RuleError):
                parse_windows(text, 60)
        for value in ("0", "45", "500", "abc"):
            with self.subTest(value=value), self.assertRaises(RuleError):
                parse_duration(value)
        self.assertEqual(parse_duration("-"), 60)
        self.assertEqual(parse_windows("вс 23:00-24:00", 60)[0].label, "воскресенье, 23:00–24:00")

    def test_refusal_and_missing_are_different_and_neither_is_common(self):
        slots = [Slot(1, 1, 1080, 60)]
        refused = rank_candidates(slots, [1, 2], {1: {1}, 2: set()})[0]
        absent = rank_candidates(slots, [1, 2], {1: {1}})[0]
        self.assertEqual(refused.unavailable, (2,))
        self.assertEqual(refused.missing, ())
        self.assertEqual(absent.unavailable, ())
        self.assertEqual(absent.missing, (2,))
        self.assertFalse(refused.common)
        self.assertFalse(absent.common)

    def test_single_common_option_is_only_recommendation(self):
        slots = parse_windows("ср 18:00-20:00", 60)
        view = RoundView(1, "closed", 60, 2e9, {1: "Аня", 2: "Борис"}, slots, {1: {1, 2}, 2: {2, 3}})
        self.assertEqual([c.slot.id for c in view.top], [2])
        self.assertIn("подходит всем", result_text(view))

    def test_ranking_is_support_then_weekday_and_time(self):
        slots = parse_windows("чт 18:00-20:00; вт 18:00-20:00", 60)
        ranked = rank_candidates(slots, [1, 2, 3], {1: {2, 4}, 2: {4}, 3: set()})
        self.assertEqual([c.slot.id for c in ranked[:3]], [4, 2, 1])

    def test_deadline_offsets_follow_prague_dst(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp()
        winter = datetime.fromtimestamp(parse_deadline("15.01.2026 19:00", now), timezone.utc)
        summer = datetime.fromtimestamp(parse_deadline("15.07.2026 19:00", now), timezone.utc)
        self.assertEqual(winter.hour, 18)
        self.assertEqual(summer.hour, 17)
        self.assertEqual(winter.astimezone(PRAGUE).hour, 19)
        self.assertEqual(summer.astimezone(PRAGUE).hour, 19)

    def test_ambiguous_nonexistent_and_past_deadlines_are_rejected(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp()
        for text in ("29.03.2026 02:30", "25.10.2026 02:30", "31.02.2026 12:00", "01.01.2025 20:00"):
            with self.subTest(text=text), self.assertRaises(RuleError):
                parse_deadline(text, now)

    def test_final_schedule_is_weekday_wall_time(self):
        self.assertIn("каждую среду, 19:00–20:00 по Праге", schedule_text(2, 1140, 60))
        self.assertIn("каждый вторник", schedule_text(1, 1140, 60))
        self.assertIn("каждое воскресенье", schedule_text(6, 1140, 60))


if __name__ == "__main__":
    unittest.main()
