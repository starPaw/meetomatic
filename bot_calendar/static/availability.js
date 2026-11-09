(function (root, factory) {
  const availability = factory();
  if (typeof module === "object" && module.exports) module.exports = availability;
  if (root) root.Availability = availability;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const STEP = 30;

  function checkDuration(duration) {
    if (!Number.isInteger(duration) || duration <= 0) throw new TypeError("Duration must be a positive integer number of minutes");
  }

  function validateSlot(slot) {
    if (!slot || !Number.isInteger(slot.id) || !Number.isInteger(slot.day) || !Number.isInteger(slot.start) ||
        slot.day < 0 || slot.start < 0 || slot.start >= 1440 || slot.start % STEP !== 0) {
      throw new TypeError("Each slot must have an integer id, weekday, and half-hour start minute");
    }
  }

  function validateInterval(interval) {
    if (!interval || !Number.isInteger(interval.day) || !Number.isInteger(interval.start) || !Number.isInteger(interval.end) ||
        interval.day < 0 || interval.start < 0 || interval.start >= 1440 || interval.start % STEP !== 0 ||
        interval.end <= interval.start || interval.end > 1440) {
      throw new TypeError("Each interval must have a weekday and valid minute-of-day start/end (end may be 1440 for 24:00)");
    }
  }

  // Keep each run of adjacent half-hour starts as its own interval. Overlapping
  // intervals are meaningful when selected starts are sparse, so never merge them.
  function toIntervals(selectedSlots, durationMinutes) {
    checkDuration(durationMinutes);
    if (!Array.isArray(selectedSlots)) throw new TypeError("Selected slots must be an array");
    const sorted = selectedSlots.map((slot) => {
      validateSlot(slot);
      if (slot.start + durationMinutes > 1440) throw new TypeError("Selected slot duration must fit within its day");
      return { id: slot.id, day: slot.day, start: slot.start };
    }).sort((a, b) => a.day - b.day || a.start - b.start || a.id - b.id);
    const unique = sorted.filter((slot, index) => index === 0 || slot.day !== sorted[index - 1].day || slot.start !== sorted[index - 1].start);
    const intervals = [];
    for (let index = 0; index < unique.length;) {
      const first = unique[index];
      let last = first.start;
      index += 1;
      while (index < unique.length && unique[index].day === first.day && unique[index].start === last + STEP) {
        last = unique[index].start;
        index += 1;
      }
      intervals.push({ day: first.day, start: first.start, end: last + durationMinutes });
    }
    return intervals;
  }

  // Expand intervals only onto known candidate slots, preserving the server's
  // available slot set and requiring the full meeting duration to fit.
  function toSlots(intervals, slots, durationMinutes) {
    checkDuration(durationMinutes);
    if (!Array.isArray(intervals) || !Array.isArray(slots)) throw new TypeError("Intervals and slots must be arrays");
    intervals.forEach(validateInterval);
    slots.forEach(validateSlot);
    const selected = new Set();
    for (const slot of slots) {
      if (intervals.some((interval) => interval.day === slot.day && slot.start >= interval.start && slot.start + durationMinutes <= interval.end)) {
        selected.add(slot.id);
      }
    }
    return [...selected].sort((a, b) => a - b);
  }

  return { toIntervals, toSlots };
});
