const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const i18n = require('../bot_calendar/static/i18n.js');
test('Telegram takes priority and unsupported Telegram languages fall back to English', () => {
  for (const [tg, browser, expected] of [['cs-CZ', 'ru', 'cs'], ['UK', 'en', 'uk'], ['ru_RU', 'en', 'ru'], ['de', 'ru', 'en'], [undefined, 'cs-CZ', 'cs'], ['', '', 'en']]) {
    assert.equal(i18n.detect(tg, browser), expected);
  }
});
test('all literal UI keys have all three translations', () => {
  const source = fs.readFileSync('bot_calendar/static/app.js', 'utf8');
  for (const match of source.matchAll(/\bt\((['"])(.*?)\1\)/g)) {
    assert.ok(i18n.messages[match[2]], `Missing key: ${match[2]}`);
  }
  for (const [key, value] of Object.entries(i18n.messages)) {
    for (const language of ['en', 'cs', 'uk']) assert.ok(value[language]?.trim(), `${key}: ${language}`);
  }
});
test('locale plural rules handle 1, 2, 5, 11, 21 correctly', () => {
  const expected = {en: [0, 2, 2, 2, 2], cs: [0, 1, 2, 2, 2], ru: [0, 1, 2, 2, 0], uk: [0, 1, 2, 2, 0]};
  for (const language of Object.keys(expected)) {
    i18n.setLanguage(language);
    assert.deepEqual([1, 2, 5, 11, 21].map(n => i18n.plural(n, [0, 1, 2])), expected[language]);
  }
});
test('deadline display stays in Prague across DST, regardless of user locale', () => {
  for (const language of Object.keys(i18n.languages)) {
    i18n.setLanguage(language);
    assert.match(i18n.deadline(Date.parse('2026-07-01T16:00:00Z') / 1000), /18:00/);
    assert.match(i18n.deadline(Date.parse('2026-12-01T17:00:00Z') / 1000), /18:00/);
  }
});
