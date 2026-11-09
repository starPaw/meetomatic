const test = require('node:test');
const assert = require('node:assert/strict');
const Availability = require('../bot_calendar/static/availability.js');

const slot = (id, start, day = 1) => ({ id, day, start });

test('a 60 minute range from 18:00 to 20:00 contains starts at 18:00, 18:30, and 19:00', () => {
  const candidates = [slot(1, 1080), slot(2, 1110), slot(3, 1140), slot(4, 1170)];
  assert.deepEqual(Availability.toSlots([{ day: 1, start: 1080, end: 1200 }], candidates, 60), [1, 2, 3]);
});

test('consecutive starts form runs and starts separated by a gap stay separate', () => {
  const selected = [slot(4, 1260), slot(2, 1110), slot(1, 1080), slot(3, 1170)];
  assert.deepEqual(Availability.toIntervals(selected, 60), [
    { day: 1, start: 1080, end: 1170 },
    { day: 1, start: 1170, end: 1230 },
    { day: 1, start: 1260, end: 1320 },
  ]);
});

test('sparse starts with overlapping duration remain separate and round trip losslessly', () => {
  const selected = [slot(1, 1080), slot(3, 1140)];
  const intervals = Availability.toIntervals(selected, 60);
  assert.deepEqual(intervals, [
    { day: 1, start: 1080, end: 1140 },
    { day: 1, start: 1140, end: 1200 },
  ]);
  assert.deepEqual(Availability.toSlots(intervals, [slot(1, 1080), slot(2, 1110), slot(3, 1140)], 60), [1, 3]);
});

test('days are independent and results use stable day and ID ordering', () => {
  const selected = [slot(4, 1380, 3), slot(2, 1380, 1)];
  const intervals = Availability.toIntervals(selected, 60);
  assert.deepEqual(intervals, [
    { day: 1, start: 1380, end: 1440 },
    { day: 3, start: 1380, end: 1440 },
  ]);
  const candidates = [slot(4, 1380, 3), slot(2, 1380, 1)];
  assert.deepEqual(Availability.toSlots(intervals, candidates, 60), [2, 4]);
});

test('24:00 is supported as the exclusive end boundary', () => {
  const candidates = [slot(1, 1380), slot(2, 1410)];
  assert.deepEqual(Availability.toSlots([{ day: 1, start: 1380, end: 1440 }], candidates, 30), [1, 2]);
});

test('every subset of nine starts round trips without adding or losing IDs', () => {
  const candidates = Array.from({ length: 9 }, (_, index) => slot(index + 1, 600 + index * 30));
  for (let mask = 0; mask < 2 ** candidates.length; mask += 1) {
    const selected = candidates.filter((_, index) => mask & (1 << index));
    const intervals = Availability.toIntervals(selected, 120);
    assert.deepEqual(Availability.toSlots(intervals, candidates, 120), selected.map((item) => item.id), `subset mask ${mask}`);
  }
});
