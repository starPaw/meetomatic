/* Locale affects presentation only; Telegram identity is verified by the server. */
(function (root) {
  'use strict';
  const messages = typeof module !== 'undefined' ? require('./translations.js') : root.MeetingMessages;
  const languages = {ru: 'Русский', en: 'English', cs: 'Čeština', uk: 'Українська'};
  const normalize = value => typeof value === 'string' ? value.toLowerCase().split(/[-_]/)[0] : '';
  function detect(telegram, browser) {
    const code = normalize(telegram || browser);
    return Object.hasOwn(languages, code) ? code : 'en';
  }
  let language = 'en';
  const api = {
    languages, messages, detect,
    get language() { return language; },
    setLanguage(value) { language = Object.hasOwn(languages, value) ? value : 'en'; },
    t(key) { return language === 'ru' ? key : messages[key]?.[language] ?? messages[key]?.en ?? key; },
    plural(number, forms) {
      const category = new Intl.PluralRules(language).select(number);
      return forms[category === 'one' ? 0 : category === 'few' ? 1 : 2];
    },
    deadline(timestamp) {
      return new Intl.DateTimeFormat(language, {timeZone: 'Europe/Prague', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hourCycle: 'h23'}).format(new Date(timestamp * 1000));
    },
  };
  if (typeof module !== 'undefined') module.exports = api;
  else root.MeetingI18n = api;
})(typeof window === 'undefined' ? globalThis : window);
