'use strict';

const tg = window.Telegram?.WebApp;
const params = new URLSearchParams(location.search);
// The launch parameter only selects a screen; the API verifies identity and access.
const launch = params.has('group') || params.has('meeting') || params.has('round') ? null : /^(?:(round|meeting|group)_(\d+)|app)(?:_(create|results|repeat|meetings))?$/.exec(params.get('tgWebAppStartParam') || tg?.initDataUnsafe?.start_param || '');
const initialScreen = params.get('open') || launch?.[3];
const preview = params.get('preview') === '1';
const root = document.querySelector('#app');
const modal = document.querySelector('#modal');
const i18n = window.MeetingI18n;
const t = key => i18n.t(key);
const protocolDays = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'];
let languagePreference = 'auto';
try { languagePreference = localStorage.getItem('meeting.language') || 'auto'; } catch (_) { /* Storage may be unavailable in a WebView. */ }
if (languagePreference !== 'auto' && !Object.hasOwn(i18n.languages, languagePreference)) languagePreference = 'auto';
let days, dayShort, stateNames;
function updateLanguage() {
  i18n.setLanguage(languagePreference === 'auto' ? i18n.detect(tg?.initDataUnsafe?.user?.language_code, navigator.language) : languagePreference);
  document.documentElement.lang = i18n.language;
  document.title = t('Время быть вместе.');
  document.querySelector('.boot p')?.replaceChildren(t('Собираем удобное время…'));
  days = [t("Понедельник"), t("Вторник"), t("Среда"), t("Четверг"), t("Пятница"), t("Суббота"), t("Воскресенье")];
  dayShort = [t("пн"), t("вт"), t("ср"), t("чт"), t("пт"), t("сб"), t("вс")];
  stateNames = {open: t("Сбор открыт"), closed: t("Выбираем варианты"), voting: t("Идёт голосование"), final: t("Договорились"), cancelled: t("Подбор заменён")};
}
updateLanguage();
const formatDeadline = timestamp => i18n.deadline(timestamp);
const isOnce = value => value?.mode === 'once';
function dateLabel(date, short = false) {
  const parsed = new Date(`${date}T12:00:00Z`);
  if (!Number.isFinite(parsed.getTime())) return date;
  return new Intl.DateTimeFormat(i18n.language, {timeZone: 'UTC', day: 'numeric', month: short ? 'short' : 'long', ...(short ? {} : {weekday: 'long', year: 'numeric'})}).format(parsed);
}
function dayLabel(value, short = false) {
  const slot = typeof value === 'number' ? data?.round?.slots.find(slot => slot.day === value) || {day: value} : value;
  return slot?.date ? dateLabel(slot.date, short) : (short ? dayShort : days)[slot?.day] || '';
}
function addDateDays(date, amount) {
  const value = new Date(`${date}T12:00:00Z`);
  value.setUTCDate(value.getUTCDate() + amount);
  return value.toISOString().slice(0, 10);
}
function pragueToday() {
  const parts = new Intl.DateTimeFormat('en-CA', {timeZone: 'Europe/Prague', year: 'numeric', month: '2-digit', day: '2-digit'}).formatToParts(new Date((data?.server_time || Date.now() / 1000) * 1000));
  const part = type => parts.find(item => item.type === type).value;
  return `${part('year')}-${part('month')}-${part('day')}`;
}
function languagePicker() {
  return `<label class="language-picker">${icon('globe', 16)}<select id="language-selector" aria-label="${h(t('Язык'))}"><option value="auto" ${languagePreference === 'auto' ? 'selected' : ''}>${h(t('Язык Telegram'))}</option>${Object.entries(i18n.languages).map(([code, name]) => `<option value="${code}" ${languagePreference === code ? 'selected' : ''}>${name}</option>`).join('')}</select></label>`;
}
function syncTheme() {
  const dark = tg?.initData ? tg.colorScheme === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.dataset.theme = dark ? 'dark' : 'light';
  const color = dark ? '#111b19' : '#f6f5f0';
  document.querySelector('meta[name="theme-color"]').content = color;
  if (tg?.initData) { tg.setHeaderColor?.(color); tg.setBackgroundColor?.(color); }
}
syncTheme();
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', syncTheme);
// The available Telegram/browser window controls layout, including after rotation.
// Updating attributes instead of re-rendering preserves focus and unsaved inputs.
const layoutQueries = {
  mobile: window.matchMedia('(max-width: 600px)'),
  desktop: window.matchMedia('(min-width: 1024px)'),
  touch: window.matchMedia('(any-pointer: coarse)'),
};
function syncLayout() {
  document.documentElement.dataset.layout = layoutQueries.mobile.matches ? 'mobile' : layoutQueries.desktop.matches ? 'desktop' : 'tablet';
  document.documentElement.dataset.input = layoutQueries.touch.matches || navigator.maxTouchPoints > 0 ? 'touch' : 'pointer';
}
syncLayout();
Object.values(layoutQueries).forEach(query => query.addEventListener('change', syncLayout));
const paths = {
  check: '<path d="m5 12 4 4L19 6"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M16 3v4M8 3v4M3 11h18m-12 5h.01m5.99 0h.01"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2m20 0v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/><circle cx="9" cy="7" r="4"/>',
  arrow: '<path d="M5 12h14m-6-6 6 6-6 6"/>',
  globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a17 17 0 0 1 0 18 17 17 0 0 1 0-18"/>',
  leaf: '<path d="M20 3c-9 0-17 1-17 9a8 8 0 0 0 8 8c8 0 9-8 9-17ZM4 20 15 9"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10h.01"/>',
  sliders: '<path d="M4 21v-7m0-4V3m8 18v-9m0-4V3m8 18v-5m0-4V3M1 14h6m2-6h6m2 8h6"/>',
  chart: '<path d="M4 20h17M7 16V9m5 7V4m5 12v-5"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  back: '<path d="m14 6-6 6 6 6"/>',
  refresh: '<path d="M20 11a8 8 0 0 0-14-5L3 9m0-6v6h6m-5 4a8 8 0 0 0 14 5l3-3m0 6v-6h-6"/>',
  trash: '<path d="M3 6h18M9 6V4h6v2m-10 0 1 14h12l1-14M10 10v6m4-6v6"/>',
  lock: '<rect x="4" y="10" width="16" height="11" rx="3"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
  heart: '<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z"/>',
};
const icon = (name, size = 18) => `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.calendar}</svg>`;
const h = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[char]));
const time = minute => `${String(Math.floor(minute / 60)).padStart(2, '0')}:${String(minute % 60).padStart(2, '0')}`;
const initials = name => name.trim().split(/\s+/).slice(0, 2).map(part => part[0]).join('').toUpperCase();
const plural = (number, forms) => i18n.plural(number, forms);
let data, tab = 'week', activeDay, selected = new Set(), explicitNone = false, dirty = false;
let rangeDraft = null, rangeDraftDay = null;
let nominations = new Set(), form, busy = false, toastTimer, modalAction, botUsername = 'meeting_bot';
let directLinks = false;
let roundId = Number(params.get('round') || (launch?.[1] === 'round' ? launch[2] : null)) || null;
let groupId = Number(params.get('group') || (launch?.[1] === 'group' ? -Number(launch[2]) : null)) || null;
let meetingId = Number(params.get('meeting') || (launch?.[1] === 'meeting' ? launch[2] : null)) || null;
let createForMeeting = null, connectionTimer;
const requestedSpecificMeeting = Boolean(roundId || meetingId);
const stageParam = params.get('stage');


function normalizeWindows(value) {
  const aliases = [
    ['mon', 'monday', 'po', 'pondělí', 'понеділок'],
    ['tue', 'tuesday', 'út', 'úterý', 'вівторок'],
    ['wed', 'wednesday', 'st', 'středa', 'середа'],
    ['thu', 'thursday', 'čt', 'čtvrtek', 'четвер'],
    ['fri', 'friday', 'pá', 'pátek', 'п’ятниця', "п'ятниця"],
    ['sat', 'saturday', 'so', 'sobota', 'субота'],
    ['sun', 'sunday', 'ne', 'neděle', 'нд', 'неділя'],
  ];
  return value.split(/([;\n])/).map(part => part.replace(/^([^0-9]+)(?=\d)/, prefix => prefix.split(',').map(day => {
    const name = day.trim().toLowerCase();
    const index = aliases.findIndex(names => names.includes(name));
    return index < 0 ? name : protocolDays[index];
  }).join(',') + ' ')).join('');
}
function localizedError(result) {
  if (result.error && (i18n.language === 'ru' || i18n.messages[result.error])) return t(result.error);
  if (result.code === 'telegram_auth_required') return t('Сессия завершилась. Откройте приложение через бота ещё раз.');
  if (result.code === 'telegram_unavailable') return t('Telegram не отвечает. Попробуйте ещё раз.');
  if (result.code === 'rule_error' || result.code === 'invalid_request') return t('Проверьте данные и обновите состояние встречи.');
  return t('Не удалось выполнить действие.');
}

function notify(message, error = false) {
  const node = document.querySelector('#toast');
  node.textContent = message;
  node.className = `toast show${error ? ' error' : ''}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => node.classList.remove('show'), 4000);
}

function setDirty(value) {
  dirty = value;
  try {
    if (value) tg?.enableClosingConfirmation?.();
    else tg?.disableClosingConfirmation?.();
  } catch (_) { /* Older Telegram versions use the in-app saved indicator. */ }
}

function showModal(title, copy, label, action, warning = false, destructive = false) {
  modal.innerHTML = `<div class="modal-icon">${icon(warning ? 'info' : 'calendar', 29)}</div><h2 id="modal-title">${h(title)}</h2><p>${h(copy)}</p><div class="panel-actions"><button class="btn secondary" data-modal="cancel">${t("Отмена")}</button><button class="btn${destructive ? ' danger' : ''}" data-modal="confirm">${h(label)}</button></div>`;
  modalAction = action;
  modal.showModal();
}
modal.addEventListener('click', event => {
  const button = event.target.closest('[data-modal]');
  if (!button) return;
  const action = modalAction;
  modal.close();
  if (button.dataset.modal === 'confirm') action?.();
});

async function api(path, body) {
  let response;
  try { response = await fetch(path, {
    method: body ? 'POST' : 'GET',
    headers: {'X-Telegram-Init-Data': tg?.initData || '', ...(body ? {'Content-Type': 'application/json'} : {})},
    ...(body ? {body: JSON.stringify(body)} : {}),
  }); } catch (_) { throw new Error(t('Нет соединения. Ваш выбор сохранён на экране. Попробуйте ещё раз.')); }
  const result = await response.json();
  if (!response.ok) {
    const error = new Error(localizedError(result));
    error.code = result.code;
    throw error;
  }
  return result;
}

function receive(next, reset = false) {
  const changedRound = next.round?.id !== data?.round?.id;
  data = next;
  botUsername = next.bot_username;
  groupId = next.group_id ?? null;
  meetingId = next.meeting_id ?? null;
  roundId = next.round?.id ?? null;
  if (reset || changedRound || !dirty) {
    selected = new Set(next.round?.my_answer?.slots || []);
    explicitNone = next.round?.my_answer?.none || false;
    setDirty(false);
    rangeDraft = null; rangeDraftDay = null;
  }
  const options = next.round?.slots || [];
  if (!options.some(slot => slot.day === activeDay)) activeDay = options[0]?.day;
  if (reset || changedRound) nominations = new Set(next.round?.nominations || []);
  if (next.round && next.round.state !== 'open' && tab === 'week') tab = 'results';
  render();
}

function stateURL() {
  const query = new URLSearchParams();
  if (roundId) query.set('round', roundId);
  else if (meetingId) query.set('meeting', meetingId);
  if (groupId) query.set('group', groupId);
  return `/api/state${query.size ? `?${query}` : ''}`;
}

function leaveDraft(action) {
  if (dirty || (tab === 'create' && form?.modified)) showModal(t("Выйти без сохранения?"), t("Несохранённый ответ или черновик формы будет сброшен."), t("Выйти"), () => { setDirty(false); action(); });
  else action();
}

async function navigate(gid, mid = null, repeat = false) {
  if (busy) return;
  if (preview) {
    groupId = gid; meetingId = mid; form = null; createForMeeting = repeat ? mid : null;
    data.group_id = gid; data.group_name = data.groups.find(group => group.id === gid)?.title || data.group_name;
    if (mid) {
      const item = data.meetings.find(item => item.id === mid);
      if (item) { data.round = {...data.round, title: item.title, meeting_id: mid, id: item.round_id}; data.meeting_id = mid; }
    }
    tab = repeat ? 'create' : mid ? 'week' : 'meetings'; render(); return;
  }
  const previous = {gid: groupId, mid: meetingId, sid: roundId};
  busy = true;
  groupId = gid; meetingId = mid; roundId = null;
  try {
    const next = await api(stateURL());
    busy = false; form = null; createForMeeting = repeat ? mid : null;
    tab = repeat ? 'create' : mid ? 'week' : 'meetings';
    receive(next, true); window.scrollTo(0, 0);
  } catch (error) {
    busy = false; groupId = previous.gid; meetingId = previous.mid; roundId = previous.sid;
    notify(error.message, true); render();
  }
}

async function refresh(silent = false) {
  if (preview || busy) return;
  try {
    const next = await api(stateURL());
    if (silent && (dirty || tab === 'create')) {
      if (next.round?.state === data?.round?.state) {
        data = next;
        return;
      }
    }
    receive(next);
  } catch (error) {
    if (!silent) notify(error.message, true);
    if (error.code === 'telegram_auth_required') renderLanding(t("Сессия завершилась. Откройте приложение через бота ещё раз."));
  }
}

async function perform(action, payload = {}, message = t("Готово")) {
  if (busy) return;
  busy = true;
  render();
  try {
    const next = preview ? demoAction(action, payload) : await api('/api/action', {action, group: groupId, round: roundId, ...payload});
    busy = false;
    if (action === 'create') { form = null; createForMeeting = null; tab = 'week'; roundId = next.round.id; }
    if (action === 'close' || action === 'start_vote' || action === 'confirm') tab = 'results';
    if (action === 'join_group' || action === 'delete_meeting') tab = 'meetings';
    if (action === 'delete_meeting') { form = null; createForMeeting = null; }
    receive(next, true);
    notify(preview ? t("Демо: изменение показано только в примере") : message);
    try { tg?.HapticFeedback?.notificationOccurred('success'); } catch (_) { /* Optional. */ }
  } catch (error) {
    busy = false;
    render();
    if (error.code === 'partial_confirmation_required') confirmPartial(payload.slots);
    else notify(error.message, true);
  }
}

function brand() {
  return `<div class="brand"><span class="brand-mark" aria-hidden="true"><i></i><i></i></span><div><div class="brand-name">${t("встреча")}</div><div class="brand-sub">${t("время быть вместе")}</div></div></div>`;
}

function topbar() {
  return `<header class="topbar">${brand()}<div class="top-right">${languagePicker()}<div class="timezone">${icon('globe', 14)}${t("Прага · Europe/Prague")}</div><div class="profile"><span class="profile-name">${h(data.user.name)}</span><span class="avatar">${h(initials(data.user.name))}</span></div></div></header>`;
}

function workspaceBar() {
  const groups = data.groups || [];
  return `<div class="workspace-bar"><div class="group-field"><label for="group-selector">${t("Telegram-группа")}</label><select id="group-selector" aria-label="${t("Выбрать группу")}" ${!groups.length ? 'disabled' : ''}>${groups.length ? groups.map(group => `<option value="${group.id}" ${group.id === groupId ? 'selected' : ''}>${h(group.title)}</option>`).join('') : `<option>${t("Пока нет подключённых групп")}</option>`}</select></div><button class="btn secondary small connect-button" data-action="connect" aria-label="${t("Добавить группу")}" title="${t("Добавить группу")}">${icon('plus', 15)}<span>${t("Добавить группу")}</span></button></div>`;
}

function deleteMeetingButton(meeting) {
  if (!data.is_organizer || meeting?.state !== 'final') return '';
  return `<button class="text-button danger" data-action="delete-meeting" data-meeting="${meeting.id}" ${busy ? 'disabled' : ''}>${icon('trash', 15)}${t("Удалить встречу")}</button>`;
}

function meetingsView() {
  const meetings = data.meetings || [];
  const active = meetings.filter(meeting => ['open', 'closed', 'voting'].includes(meeting.state)).length;
  const confirmed = meetings.filter(meeting => meeting.schedule).length;
  const overview = meetings.length ? `<div class="meeting-overview">${[
    ['calendar', meetings.length, t("Всего встреч")], ['clock', active, t("Выбираем время")], ['check', confirmed, t("Уже договорились")],
  ].map(([symbol, count, label]) => `<div class="overview-stat">${icon(symbol, 20)}<div><strong>${count}</strong><span>${label}</span></div></div>`).join('')}</div>` : '';
  return `<div><div class="admin-toolbar meetings-toolbar"><h1 class="section-title">${meetings.length ? t("Ваши встречи") : t("Начнём с первой встречи")}</h1>${data.is_organizer ? `<button class="btn small" data-action="create">${icon('plus', 17)}${t("Новая встреча")}</button>` : ''}</div>${overview}${!meetings.length ? empty('calendar', t("Время собраться"), data.is_organizer ? t("Дайте встрече название, выберите участников и предложите дни. Другие встречи группы останутся без изменений.") : t("Организатор скоро создаст первую встречу."), data.is_organizer ? t("Создать встречу") : '', 'create') : `<div class="meeting-grid">${meetings.map(meeting => {
    const label = meeting.state === 'final' ? t("Посмотреть расписание") : meeting.state === 'voting' ? t("Открыть голосование") : meeting.state === 'closed' ? t("Посмотреть варианты") : t("Открыть подбор");
    const next = meeting.state === 'final' ? t("Время выбрано. Можно строить планы.") : meeting.state === 'voting' ? t("Остался один шаг — выбрать общий вариант.") : meeting.state === 'closed' ? t("Ответы собраны. Выбираем варианты для голосования.") : t("Отметьте свободное время — найдём пересечение.");
    return `<article class="card meeting-card" data-state="${h(meeting.state)}"><div class="meeting-card-top"><div class="meeting-symbol">${icon(meeting.state === 'final' ? 'check' : 'calendar', 23)}</div><span class="badge">${h(stateNames[meeting.state] || t("Новая встреча"))}</span></div><h2>${h(meeting.title)}</h2>${meeting.schedule ? `<p class="meeting-time">${h(dayLabel(meeting.schedule))}<br><strong>${time(meeting.schedule.start)}–${time(meeting.schedule.start + meeting.schedule.duration)}</strong> ${t("· по Праге")}</p>` : `<p>${meeting.duration} ${t("мин")} · ${isOnce(meeting) ? t("Разовая встреча") : t("Каждую неделю")}</p>`}<p class="meeting-next">${next}</p><div class="meeting-progress"><div class="meeting-progress-head"><span>${t("Ответили")}</span><strong>${meeting.answered_count || 0} / ${meeting.expected_count || 0}</strong></div><progress value="${meeting.answered_count || 0}" max="${meeting.expected_count || 1}" aria-label="${t("Ответили")} ${meeting.answered_count || 0} ${t("из")} ${meeting.expected_count || 0}"></progress></div><div class="meeting-actions"><button class="btn full" data-action="open-meeting" data-meeting="${meeting.id}">${label}${icon('arrow', 16)}</button>${data.is_organizer ? `<button class="text-button" data-action="repeat" data-meeting="${meeting.id}">${icon('refresh', 14)}${t("Подобрать время заново")}</button>` : ''}${deleteMeetingButton(meeting)}</div></article>`;
  }).join('')}</div>`}</div>`;
}

function connectView() {
  return `<section class="card connect-card"><div class="empty-icon">${icon('users', 29)}</div><h2>${t("Ваша группа — ваши встречи")}</h2><p>${t("Подключите Telegram-группу, где вы администратор. В каждой группе можно создать несколько встреч со своим составом и расписанием.")}</p><div class="connect-steps"><div><span class="step-no">1</span><p>${t("Добавьте бота в нужную группу, если его там ещё нет.")}</p></div><div><span class="step-no">2</span><p>${t("Выберите эту группу. Проверим ваши права — и можно создавать встречи.")}</p></div></div><button class="btn full" data-action="choose-group" ${busy ? 'disabled' : ''}>${busy ? t("Открываем выбор…") : t("Выбрать группу")}${icon('arrow', 15)}</button><button class="btn outline full" data-action="add-bot">${icon('plus', 15)}${t("Добавить бота в другую группу")}</button>${data.groups?.length ? `<button class="text-button" data-action="home">${t("Вернуться к встречам")}</button>` : ''}</section>`;
}

function openTelegram(url) {
  if (tg?.initData) { tg.openTelegramLink(url); tg.close(); }
  else window.location.href = url;
}

async function chooseGroup() {
  if (preview) return notify(t("Демо: реальные группы не подключаются"));
  if (!tg?.isVersionAtLeast?.('9.6')) return openTelegram(data.connect_url);
  busy = true; render();
  try {
    const prepared = await api('/api/action', {action: 'prepare_group'});
    busy = false; render();
    const known = new Set((data.groups || []).map(group => `${group.id}:${group.is_organizer}`));
    tg.requestChat(prepared.prepared_request_id, sent => {
      if (!sent) return;
      notify(t("Проверяем группу. Она появится здесь через несколько секунд."));
      clearInterval(connectionTimer);
      let tries = 0;
      connectionTimer = setInterval(async () => {
        if (++tries > 12) { clearInterval(connectionTimer); return; }
        try {
          const next = await api(stateURL());
          const added = next.groups.find(group => !known.has(`${group.id}:${group.is_organizer}`));
          receive(next);
          if (added) { clearInterval(connectionTimer); navigate(added.id); notify(t("Группа подключена")); }
        } catch (_) { /* The normal refresh will keep the saved state visible. */ }
      }, 2500);
    });
  } catch (error) {
    busy = false; render();
    showModal(t("Открыть выбор в чате с ботом?"), t("Можно подключить группу через команду /group в личном чате."), t("Открыть чат"), () => openTelegram(data.connect_url));
  }
}

function intro() {
  const round = data.round;
  const isCreate = tab === 'create';
  const home = tab === 'meetings', connect = tab === 'connect' || !data.groups?.length;
  if (home && !connect) return '';
  let title = connect ? t("Соберём своих.") : home ? t("Наши встречи.") : isCreate ? createForMeeting ? t("Подберём время заново.") : t("Новая встреча.") : tab === 'week' ? t("Когда вам удобно?") : round?.state === 'final' ? t("Время нашлось.") : round?.state === 'voting' ? t("Выберем наш вариант.") : t("Найдём пересечение.");
  let copy = connect ? t("Несколько групп. Любое количество поводов встретиться.") : home ? t("У каждой встречи — свои участники, ответы и постоянное время.") : isCreate ? t("Задайте рамки — каждый выберет удобное время.") : tab === 'week' ? t("Отметьте все удобные интервалы. Найдём время для всех.") : t("Все ответы в одном месте. Дальше — общее решение.");
  return `<section class="intro"><div><div class="eyebrow">${connect ? t("Встречи в Telegram") : h(data.group_name)}${round && !isCreate && !home && !connect ? ` / ${h(round.title || t("Встреча"))}` : ''}</div><h1>${title}</h1><p>${copy}</p></div>${round && !isCreate && !home && !connect ? `<div class="intro-side"><span class="status-pill${round.preliminary && round.state !== 'open' ? ' warning' : ''}"><span class="dot"></span>${h(stateNames[round.state])}</span>${round.state === 'open' ? `<div class="intro-note">${icon('clock', 14)}${t("До")} ${h(formatDeadline(round.deadline_ts))}</div>` : ''}</div>` : ''}</section>`;
}

function tabs() {
  if (!data.group_id || ['connect', 'meetings'].includes(tab)) return '';
  return `<nav class="tabs" aria-label="${t("Разделы")}"><button class="tab" data-action="home">${icon('users', 16)}${t("Встречи")}</button>${data.round && !data.not_invited && tab !== 'create' ? `<button class="tab ${tab === 'week' ? 'active' : ''}" data-action="tab" data-tab="week">${icon('calendar', 16)}${isOnce(data.round) ? t("Мои даты") : t("Моя неделя")}</button><button class="tab ${tab === 'results' ? 'active' : ''}" data-action="tab" data-tab="results">${icon('chart', 16)}${t("Результаты")}</button>${data.is_organizer && tab !== 'week' ? `<button class="tab ${tab === 'admin' ? 'active' : ''}" data-action="tab" data-tab="admin">${icon('sliders', 16)}${t("Управление")}</button>` : ''}` : ''}</nav>`;
}

const minuteValue = value => { const [hour, minute] = value.split(':').map(Number); return hour * 60 + minute; };
const minuteLabel = value => value === 1440 ? '24:00' : time(value);
function rangesForSelection(day = null) {
  if (day !== null && rangeDraftDay === day && rangeDraft) return rangeDraft;
  const slots = data.round.slots.filter(slot => selected.has(slot.id) && (day === null || slot.day === day));
  return window.Availability.toIntervals(slots, data.round.duration);
}
function selectionForRanges(ranges, keepOtherDays = true) {
  const next = window.Availability.toSlots(ranges, data.round.slots, data.round.duration);
  const otherDays = keepOtherDays ? [...selected].filter(id => {
    const slot = data.round.slots.find(item => item.id === id);
    return slot && slot.day !== activeDay;
  }) : [];
  selected = new Set([...otherDays, ...next]);
}

function selectionSummary() {
  const chosenDays = [...new Set(data.round.slots.filter(slot => selected.has(slot.id)).map(slot => slot.day))].sort();
  const detail = explicitNone ? t("Ни один предложенный вариант не подходит") : chosenDays.length ? `${chosenDays.map(day => dayLabel(day, true)).join(' · ')} — ${selected.size} ${plural(selected.size, [t("вариант"), t("варианта"), t("вариантов")])}` : t("Отметьте удобное время или выберите «Не могу».");
  return `${icon(explicitNone ? 'info' : 'check', 16)}<div><strong>${t("Ваш выбор")}</strong><span>${detail}</span></div>`;
}

function sidebar() {
  const round = data.round;
  if (!round) return `<aside class="sidebar"><div class="note-card"><div class="little-star">${icon('leaf', 24)}</div><h3>${t("Один раз договориться")}</h3><p>${t("Выбираем постоянный день и время для обычной недели. Всё — по Праге, в том числе после перевода часов.")}</p></div></aside>`;
  const count = round.answered_count;
  return `<aside class="sidebar"><section class="card summary-card"><div class="summary-icon">${icon('calendar', 24)}</div><div class="eyebrow">${isOnce(round) ? t("Разовая встреча") : t("Еженедельная встреча")}</div><h2 class="summary-title">${h(data.group_name)} ${t("· наш ритм")}</h2><div class="summary-meta"><div class="meta-row">${icon('clock', 16)}${round.duration / 60 === 1 ? t("1 час") : `${round.duration} ${t("минут")}`}</div><div class="meta-row">${icon('refresh', 16)}${isOnce(round) ? t("Конкретные даты") : t("Обычная неделя")}</div><div class="meta-row">${icon('globe', 16)}${t("Время по Праге")}</div><div class="meta-row">${icon('users', 16)}${round.expected_count} ${plural(round.expected_count, [t("участник"), t("участника"), t("участников")])}</div></div><div class="avatar-stack">${round.participants.slice(0, 7).map((person, i) => `<span class="avatar hue${i % 4}" title="${h(person.name)}">${h(initials(person.name))}</span>`).join('')}</div><div class="progress-heading"><strong>${t("Ответили")}</strong><span>${count} ${t("из")} ${round.expected_count}</span></div><progress value="${count}" max="${round.expected_count}" aria-label="${t("Ответили")} ${count} ${t("из")} ${round.expected_count}"></progress><div class="waiting">${round.missing.length ? `${t("Ещё ждём:")} <strong>${h(round.missing.join(', '))}</strong>` : `${icon('check', 12)} ${t("Все участники ответили")}`}</div></section><div class="note-card"><div class="little-star">${icon('leaf', 22)}</div><h3>${isOnce(round) ? t("Одна встреча в выбранную дату") : t("Для вашей обычной недели")}</h3><p>${isOnce(round) ? t("Отметьте подходящее время в предложенные даты. Ответ можно менять, пока сбор открыт.") : t("Выбирайте время, которое обычно свободно. Ответ можно менять, пока сбор открыт.")}</p></div></aside>`;
}

function availability() {
  const round = data.round;
  if (!round) return empty('calendar', t("Пока нет подбора"), t("Организатор скоро предложит дни и время для встречи."));
  if (!round.is_expected) return empty('users', t("Вы управляете подбором"), t("Ваш ответ сейчас не ожидается. Перейдите к результатам, чтобы посмотреть доступность участников."), t("Результаты"), 'show-results');
  if (!round.can_answer) return empty('lock', t("Доступность уже собрана"), t("Ответы сохранены. Следующий шаг — выбрать и подтвердить общее время."), t("Открыть результаты"), 'show-results');
  const availableDays = [...new Set(round.slots.map(slot => slot.day))];
  const daySlots = round.slots.filter(slot => slot.day === activeDay);
  const dayRanges = rangesForSelection(activeDay);
  const firstStart = Math.min(...daySlots.map(slot => slot.start));
  const lastEnd = Math.max(...daySlots.map(slot => slot.start + round.duration));
  const intervalRows = dayRanges.map((range, index) => {
    const start = range.start, end = range.end;
    return `<div class="interval-row" data-range-index="${index}"><div class="interval-head"><strong>${t("Интервал")} ${index + 1}</strong><button class="text-button remove-interval" data-action="remove-range" data-index="${index}" aria-label="${t("Удалить интервал")}">${t("Удалить")}</button></div><div class="range-values"><label>${t("С")} <select data-range="start" data-index="${index}">${Array.from({length: Math.floor((lastEnd - firstStart) / 30) + 1}, (_, i) => firstStart + i * 30).filter(value => value + round.duration <= end).map(value => `<option value="${value}" ${value === start ? 'selected' : ''}>${time(value)}</option>`).join('')}</select></label><label>${t("До")} <select data-range="end" data-index="${index}">${Array.from({length: Math.floor((lastEnd - firstStart) / 30) + 1}, (_, i) => firstStart + i * 30).filter(value => value >= start + round.duration).map(value => `<option value="${value}" ${value === end ? 'selected' : ''}>${minuteLabel(value)}</option>`).join('')}</select></label></div><div class="range-slider"><div class="range-track"></div><input aria-label="${t("Начало интервала")} ${index + 1}" type="range" min="${firstStart}" max="${lastEnd}" step="30" value="${start}" data-range="start" data-index="${index}"><input aria-label="${t("Конец интервала")} ${index + 1}" type="range" min="${firstStart}" max="${lastEnd}" step="30" value="${end}" data-range="end" data-index="${index}"></div></div>`;
  }).join('');
  const selectedCount = daySlots.filter(slot => selected.has(slot.id)).length;
  return `<div><section class="card availability-card"><div class="availability-top"><div class="section-head"><h2>${t("Когда вы свободны?")}</h2><span class="small-label">${icon('clock', 13)}${round.duration} ${t("мин встреча")}</span></div><p class="section-sub">${t("Выберите свободные промежутки. Подойдут любые начала встречи внутри них.")}</p></div><div class="day-tabs compact-days ${isOnce(round) ? 'date-days' : ''}" role="group" aria-label="${isOnce(round) ? t("Даты встречи") : t("Дни недели")}">${availableDays.map(day => {const count = round.slots.filter(slot => slot.day === day && selected.has(slot.id)).length; return `<button class="day-tab ${day === activeDay ? 'active' : ''}" data-action="day" data-day="${day}" aria-pressed="${day === activeDay}" aria-label="${h(dayLabel(day))}${count ? `, ${count} ${t("вариантов")}` : ''}"><strong>${h(dayLabel(day, true))}</strong><span>${count ? icon('check', 12) : '·'}</span></button>`;}).join('')}</div><div class="slots-area"><div class="day-toolbar"><h3>${h(dayLabel(activeDay))}${selectedCount ? ` · ${selectedCount} ${plural(selectedCount, [t("вариант"), t("варианта"), t("вариантов")])}` : ''}</h3><button class="text-button" data-action="copy-day" ${!selectedCount || availableDays.length < 2 ? 'disabled' : ''}>${t("Повторить на остальных днях")}</button></div><div class="day-quick-actions"><button class="preset-chip" data-action="whole-day" ${selectedCount === daySlots.length ? 'disabled' : ''}>${icon('check', 14)}${t("Подходит весь диапазон")}</button><button class="text-button" data-action="clear-day" ${!selectedCount ? 'disabled' : ''}>${t("Очистить день")}</button></div>${intervalRows || `<p class="no-intervals">${t("Пока нет интервалов. Добавьте время, когда вы свободны.")}</p>`}<button class="btn outline add-interval" data-action="add-range">${icon('plus', 15)}${t("Добавить интервал")}</button></div><div class="selection-summary">${selectionSummary()}</div><div class="availability-bottom"><button class="none-option ${explicitNone ? 'selected' : ''}" data-action="none" aria-pressed="${explicitNone}"><span class="radio"></span><strong>${t("Не могу")}</strong><span>${t("Ни один предложенный вариант не подходит")}</span></button></div></section></div>`;
}

function empty(symbol, title, copy, label = '', action = '') {
  return `<section class="card empty"><div class="empty-icon">${icon(symbol, 28)}</div><h2>${h(title)}</h2><p>${h(copy)}</p>${label ? `<button class="btn" data-action="${action}">${h(label)}${icon('arrow', 15)}</button>` : ''}</section>`;
}

function resultCard(option, index, mode) {
  const round = data.round;
  const chosen = mode === 'nominate' ? nominations.has(option.slot_id) : round.my_vote === option.slot_id;
  const voting = mode === 'vote', leader = voting && round.leaders.includes(option.slot_id);
  const percent = round.voted_count ? Math.round((option.votes || 0) / round.voted_count * 100) : 0;
  return `<article class="card result-card ${voting ? 'voting-option' : ''} ${chosen ? 'chosen' : ''}" data-leader="${leader}">
    <div class="result-top"><span class="result-rank">${t("ВАРИАНТ")} ${String(index + 1).padStart(2, '0')}</span><span class="badge${option.common ? '' : ' partial'}">${option.common ? t("Подходит всем") : round.preliminary ? t("Предварительно") : t("Частичное совпадение")}</span></div>
    <div class="result-title">${h(dayLabel(option))}</div><div class="result-time">${time(option.start)}–${time(option.end)} ${t("· по Праге")}</div>
    ${voting ? `<div class="vote-badges">${chosen ? `<span class="badge your-vote">${icon('check', 13)}${t("Ваш голос")}</span>` : ''}${leader ? `<span class="badge leader">${round.leaders.length > 1 ? t("Ничья") : t("Лидирует")}</span>` : ''}${option.expired ? `<span class="badge partial">${t("Это время уже прошло")}</span>` : ''}</div>` : ''}
    <div class="result-support"><span>${t("Доступны для встречи")}</span><strong>${option.available_count} ${t("из")} ${option.expected_count}</strong></div>
    ${!voting ? `<div class="support-dots" aria-hidden="true">${Array.from({length: Math.min(option.expected_count, 30)}, (_, i) => `<span class="${i < option.available_count ? 'on' : ''}"></span>`).join('')}</div>` : ''}
    ${data.is_organizer && (option.unavailable?.length || option.missing?.length) ? `<details class="result-details"><summary>${t("Кого не хватает")}</summary>${option.unavailable?.length ? `<p>${t("Не могут:")} ${h(option.unavailable.join(', '))}</p>` : ''}${option.missing?.length ? `<p>${t("Нет ответа:")} ${h(option.missing.join(', '))}</p>` : ''}</details>` : ''}
    ${mode === 'nominate' ? `<button class="result-choice" data-action="nominate" data-slot="${option.slot_id}" aria-pressed="${chosen}" ${option.expired ? 'disabled' : ''}><span class="slot-check">${icon('check', 12)}</span>${chosen ? t("Включён в голосование") : t("Включить в голосование")}</button>` : ''}
    ${voting ? `<div class="result-vote"><div class="vote-score"><strong>${option.votes || 0} ${plural(option.votes || 0, [t("голос"), t("голоса"), t("голосов")])}</strong><span>${percent}%</span></div><progress value="${option.votes || 0}" max="${round.voted_count || 1}" aria-label="${h(t('Голосов') + ': ' + (option.votes || 0))}"></progress>${round.is_expected ? `<button class="btn ${chosen ? 'secondary' : 'outline'} full" data-action="vote" data-slot="${option.slot_id}" aria-pressed="${chosen}" ${busy || chosen || option.expired ? 'disabled' : ''}>${chosen ? icon('check', 14) + t("Ваш голос сохранён") : round.my_vote != null ? t("Изменить голос") : t("Выбрать этот вариант")}</button>` : ''}</div>` : ''}
  </article>`;
}

function votingOverview(round) {
  const mine = round.vote_options.find(option => option.slot_id === round.my_vote);
  return `<section class="voting-overview"><div class="voting-progress-heading"><strong>${t("Проголосовали")}</strong><span>${round.voted_count} / ${round.expected_count}</span></div><progress value="${round.voted_count}" max="${round.expected_count || 1}" aria-label="${t("Проголосовали")} ${round.voted_count} ${t("из")} ${round.expected_count}"></progress><p class="voting-my-choice">${mine ? `${icon('check', 16)}${t("Ваш голос:")} <strong>${h(dayLabel(mine, true))}, ${time(mine.start)}–${time(mine.end)}</strong>` : round.is_expected ? t("Вы ещё не проголосовали. Выберите один вариант ниже.") : t("Вы наблюдаете за голосованием.")}</p><div class="voting-people">${round.participants.map((person, index) => `<span class="voter-chip ${person.voted ? 'voted' : ''}"><span class="avatar hue${index % 4}">${h(initials(person.name))}</span>${h(person.name)}${person.voted ? icon('check', 13) : icon('clock', 13)}<span class="sr-only">${person.voted ? t("Голос сохранён") : t("Ещё не проголосовал")}</span></span>`).join('')}</div><p class="hint">${t("Голос можно изменить до подтверждения организатором.")}</p></section>`;
}

function voteConfirmation(round) {
  if (!data.is_organizer) return notice(t("Когда голосование закончится, организатор подтвердит дату и время."));
  const leaders = round.vote_options.filter(option => round.leaders.includes(option.slot_id) && !option.expired);
  const copy = !round.leaders.length ? t("Подтверждение появится после первого голоса.") : !leaders.length ? t("Время лидирующих вариантов прошло. Начните новый подбор.") : round.leaders.length > 1 ? t("Ничья: выберите один из лидирующих вариантов.") : t("Подтвердите выбранный вариант — бот сообщит итог участникам.");
  return `<section class="vote-confirm-panel"><h3>${t("Решение организатора")}</h3><p>${copy}</p>${leaders.length && round.voted_count < round.expected_count ? `<p class="hint">${t("Ещё не все проголосовали. Досрочное завершение потребует подтверждения.")}</p>` : ''}<div class="confirm-options">${leaders.map(option => `<button class="btn ${leaders.length > 1 ? 'outline' : ''}" data-action="confirm" data-slot="${option.slot_id}" ${busy ? 'disabled' : ''}>${t("Подтвердить")} ${h(dayLabel(option, true))}, ${time(option.start)}–${time(option.end)}${icon('check', 16)}</button>`).join('')}</div>${round.leaders.length && !leaders.length ? `<button class="btn secondary" data-action="repeat" data-meeting="${meetingId}">${t("Подобрать время заново")}</button>` : ''}</section>`;
}

function results() {
  const round = data.round;
  if (!round) return empty('calendar', t("Начнём с первого подбора"), t("Выберите участников, дни недели и время. Бот соберёт ответы в вашей группе."), data.is_organizer ? t("Создать подбор") : '', 'create');
  if (round.state === 'final' && data.schedule) {
    const historical = data.meetings.some(meeting => meeting.id === meetingId && meeting.round_id !== round.id);
    return `${historical ? notice(t("Это результат предыдущего подбора. У встречи уже есть более новый подбор."), true) + `<div class="panel-actions"><button class="btn secondary" data-action="latest">${t("Открыть текущий")}${icon('arrow', 14)}</button></div>` : ''}${finalView()}`;
  }
  if (round.state === 'cancelled') return empty('refresh', t("Есть новый подбор"), t("Этот подбор заменён новым. Откройте приложение из последнего сообщения в группе."), t("Открыть текущий"), 'latest');
  if (round.state === 'voting') {
    const roleNotice = !round.is_expected && data.is_organizer ? notice(t("Вы организатор. Ваш голос не ожидается: подтвердите итог после голосования участников.")) : '';
    return `<div><div class="results-header"><h2>${t("Какой вариант выбираем?")}</h2><p>${isOnce(round) ? t("Одна встреча в выбранную дату") : t("Постоянная встреча каждую неделю")}</p></div>${votingOverview(round)}${roleNotice}${round.preliminary ? notice(t("Есть участники без ответа о доступности. Организатор явно разрешил финальное голосование."), true) : ''}<div class="result-list">${round.vote_options.map((option, index) => resultCard(option, index, 'vote')).join('')}</div>${voteConfirmation(round)}</div>`;
  }
  if (!round.answered_count) return `<div>${empty('users', t("Ждём первые ответы"), t("Как только участники отметят удобное время, здесь появятся лучшие варианты."))}${data.is_organizer ? `<div class="panel-actions"><button class="btn secondary" data-action="share">${icon('users', 16)}${t("Пригласить участников")}</button>${round.state === 'open' ? `<button class="btn outline" data-action="close">${t("Закрыть сбор")}</button>` : ''}</div>` : ''}</div>`;
  const common = round.candidates.some(option => option.common);
  const mode = round.state === 'closed' && data.is_organizer ? 'nominate' : 'view';
  return `<div><div class="results-header"><h2>${common ? round.candidates.length === 1 ? t("Один общий вариант") : t("Вот наше общее время") : t("Лучшие совпадения")}</h2><p>${common ? t("Это время отметили все ожидаемые участники.") : round.preliminary ? t("Считаем по сохранённым ответам. Итог пока предварительный.") : t("Общего времени нет. Ниже — варианты с наибольшим числом участников.")}</p></div>${round.preliminary ? notice(`${t("Ответили")} ${round.answered_count} ${t("из")} ${round.expected_count}${t(". Ещё ждём:")} ${round.missing.join(', ')}${t(". Эти варианты пока нельзя считать подходящими всем.")}`, true) : ''}<div class="result-list">${round.candidates.map((option, index) => resultCard(option, index, mode)).join('')}</div>${data.is_organizer && round.state === 'open' ? `<div class="panel-actions"><button class="btn" data-action="close">${t("Закрыть сбор и выбрать варианты")}${icon('arrow', 15)}</button></div><div class="hint">${t("После закрытия участники больше не смогут менять доступность.")}</div>` : ''}${mode === 'nominate' ? `<div class="panel-actions"><button class="btn" data-action="start-vote" ${!nominations.size || busy ? 'disabled' : ''}>${t("Начать голосование")}${nominations.size ? ` · ${nominations.size}` : ''}${icon('arrow', 15)}</button></div><div class="hint">${t("Отметьте до трёх вариантов. Для частичных совпадений потребуется ваше явное решение.")}</div>` : ''}${!data.is_organizer && round.state === 'closed' ? notice(t("Организатор выбирает варианты финального голосования.")) : ''}</div>`;
}

function notice(text, warning = false) {
  return `<div class="notice${warning ? ' warning' : ''}">${icon('info', 16)}<span>${h(text)}</span></div>`;
}

function finalView() {
  const schedule = data.schedule;
  return `<section class="card final-card"><div class="final-mark">${icon('check', 31)}</div><h2>${t("Договорились.")}</h2><p>${schedule.date ? t("Дата и время подтверждены. Можно строить планы.") : t("Наш постоянный день и время. Можно строить планы.")}</p><div class="schedule-ticket"><div class="eyebrow">${schedule.date ? t("Разовая встреча") : t("Каждую неделю")}</div><h3>${h(dayLabel(schedule))}</h3><strong>${time(schedule.start)}–${time(schedule.start + schedule.duration)}</strong><p>${t("По Праге ·")} ${schedule.duration} ${t("минут")}</p></div><p>${schedule.date ? '' : t("Местное время сохранится при переводе часов.") + '<br>'}${data.round.publication_state === 'sent' ? t("Итог опубликован в группе.") : t("Расписание сохранено. Доставляем итог в группу.")}</p>${data.is_organizer ? `<div class="panel-actions"><button class="btn secondary full" data-action="repeat" data-meeting="${meetingId}">${icon('refresh', 16)}${t("Подобрать время заново")}</button></div>${deleteMeetingButton(data.meetings.find(item => item.id === meetingId && item.round_id === data.round.id))}` : ''}</section>`;
}

function ensureForm() {
  if (form) return;
  const round = createForMeeting ? data.round : null;
  const byDay = new Map();
  for (const slot of round?.slots || []) {
    const range = byDay.get(slot.day) || [slot.start, slot.end];
    byDay.set(slot.day, [Math.min(range[0], slot.start), Math.max(range[1], slot.end)]);
  }
  const first = [...byDay.values()][0] || [1080, 1260];
  const defaultDate = addDateDays(data.defaults.deadline.slice(0, 10), 1);
  form = {
    mode: round?.mode || 'weekly', dates: new Set(round?.slots.filter(slot => slot.date).map(slot => slot.date) || [defaultDate]), dateDraft: defaultDate,
    title: round?.title || '', meetingId: createForMeeting, modified: false,
    participants: new Set(round ? round.participants.map(person => person.id).filter(Boolean) : [data.user.id]),
    duration: round?.duration || 60, days: new Set(byDay.size ? byDay.keys() : [1, 3]),
    from: time(first[0]), to: time(first[1]), extra: '',
    deadline: data.defaults.deadline, windows: round?.windows || '', advanced: Boolean(round?.windows),
    requestId: crypto.randomUUID(),
  };
}

function formFeedback() {
  if (form.advanced && form.windows.trim()) return '';
  if (form.mode === 'once') {
    if (!form.dates.size) return t("Добавьте хотя бы одну дату.");
    if ([...form.dates].some(date => date < pragueToday() || date > addDateDays(pragueToday(), 365))) return t("Выберите даты в течение ближайшего года.");
    if (`${[...form.dates].sort()[0]}T${form.from}` <= form.deadline) return t("Срок ответа должен быть раньше первого варианта встречи.");
  }
  return minuteValue(form.to) - minuteValue(form.from) < form.duration
    ? t("Встреча не помещается в диапазон. Увеличьте его или сократите длительность.") : '';
}

function formPreview() {
  const [date, clock] = form.deadline.split('T');
  const parsed = new Date(`${date}T12:00:00Z`);
  const deadline = Number.isFinite(parsed.getTime()) ? `${new Intl.DateTimeFormat(i18n.language, {day: 'numeric', month: 'short', timeZone: 'UTC'}).format(parsed)}, ${clock}` : t("Выберите дату");
  const people = `${form.participants.size} ${plural(form.participants.size, [t("участник"), t("участника"), t("участников")])}${form.extra.trim() ? ` + ${t("добавленные вручную")}` : ''}`;
  const when = form.advanced && form.windows.trim() ? form.windows.trim() : `${(form.mode === 'once' ? [...form.dates].sort().map(date => dateLabel(date, true)).join(', ') : [...form.days].sort().map(day => dayShort[day]).join(', ')) || t("Выберите дни")} · ${form.from}–${form.to}`;
  return `<div class="preview-kicker">${icon('check', 15)}${t("Перед публикацией")}</div><strong class="preview-title">${h(form.title.trim() || t("Новая встреча"))}</strong><div class="preview-detail">${form.mode === 'once' ? t("Разовая встреча") : t("Каждую неделю")}</div><div class="preview-detail">${icon('users', 16)}<span>${h(people)}</span></div><div class="preview-detail">${icon('calendar', 16)}<span>${h(when)} · ${form.duration} ${t("мин")}</span></div><div class="preview-detail">${icon('clock', 16)}<span>${t("Ответить до")} ${h(deadline)} · ${t("Время по Праге")}</span></div>`;
}

function updateFormPreview() {
  const preview = root.querySelector('.form-preview');
  if (!preview || !form) return;
  preview.innerHTML = formPreview();
  const message = formFeedback();
  const feedback = root.querySelector('.form-feedback');
  feedback.textContent = message;
  feedback.hidden = !message;
  root.querySelector('#to').setCustomValidity(message);
  root.querySelector('#to').setAttribute('aria-invalid', String(Boolean(message)));
  root.querySelectorAll('[data-action="form-days-preset"], [data-action="form-time-preset"]').forEach(button => {
    const active = !form.advanced && (button.dataset.days
      ? button.dataset.days.split(',').length === form.days.size && button.dataset.days.split(',').every(day => form.days.has(Number(day)))
      : form.from === button.dataset.from && form.to === button.dataset.to);
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
}

function createView() {
  ensureForm();
  const [deadlineDate, deadlineTime] = form.deadline.split('T');
  return `<div class="card admin-card">
    <div class="admin-toolbar"><h2 class="section-title">${form.meetingId ? t("Новый подбор времени") : t("Новая встреча")}</h2><button class="text-button" data-action="home">${t("Отмена")}</button></div>
    <form id="create-form">
      <section class="form-section form-title"><div class="field"><label for="meeting-title">${t("Название встречи")}</label><input id="meeting-title" data-field="title" value="${h(form.title)}" placeholder="${t("Например, завтрак команды")}" maxlength="80" required ${form.meetingId ? 'readonly' : ''}></div><p class="form-help form-note">${t("Группа:")} <strong>${h(data.group_name)}</strong>. ${form.meetingId ? t("Меняем время только этой встречи.") : t("У новой встречи будут свои ответы и расписание.")}</p></section>
      <section class="form-section form-mode"><h3>${t("Как встречаемся")}</h3><div class="meeting-mode-choices">${[['once', t("Разовая встреча"), t("Выбираем конкретную дату")], ['weekly', t("Каждую неделю"), t("Выбираем постоянный день недели")]].map(([mode, title, description]) => `<button type="button" class="choice ${form.mode === mode ? 'active' : ''}" data-action="form-mode" data-mode="${mode}" aria-pressed="${form.mode === mode}" ${form.meetingId ? 'disabled' : ''}><strong class="mode-label">${title}</strong><small>${description}</small></button>`).join('')}</div>${form.meetingId ? `<p class="form-help">${t("Чтобы изменить режим, создайте новую встречу.")}</p>` : ''}</section>
      <section class="form-section form-people"><h3><span class="step-no">1</span>${t("Кто встречается")}</h3><p class="form-help">${t("Выберите всех, чьи ответы нужны. Включите себя, если тоже участвуете.")}</p>
        <div class="people-toolbar"><span>${form.participants.size} ${t("выбрано")}</span><button type="button" class="text-button" data-action="select-all-people">${data.people.slice(0, 30).every(person => form.participants.has(person.id)) ? t("Снять выбор") : data.people.length > 30 ? t("Выбрать первые 30") : t("Выбрать всех")}</button></div><div class="people">${data.people.map((person, i) => `<button type="button" class="person-chip ${form.participants.has(person.id) ? 'selected' : ''}" data-action="person" data-person="${person.id}" aria-pressed="${form.participants.has(person.id)}"><span class="avatar hue${i % 4}">${h(initials(person.name))}</span>${h(person.name)}<span class="chip-check">${icon('check', 13)}</span></button>`).join('')}</div>
        <div class="field"><label for="extra-people">${t("Добавить по @имени или ID")}</label><input id="extra-people" data-field="extra" value="${h(form.extra)}" placeholder="${t("@anna; 123456:Борис")}" autocomplete="off"></div><button type="button" class="text-button" data-action="share">${icon('users', 13)}${t("Пригласить участника в группу приложения")}</button>
      </section>
      <section class="form-section form-duration"><h3><span class="step-no">2</span>${t("Сколько времени нужно")}</h3><div class="duration-choices">${[30, 60, 90, 120].map(value => `<button type="button" class="choice ${form.duration === value ? 'active' : ''}" data-action="duration" data-duration="${value}">${value === 30 ? t("30 мин") : value === 60 ? t("1 час") : value === 90 ? t("1,5 часа") : t("2 часа")}</button>`).join('')}</div><details class="advanced"><summary>${t("Другая длительность")}</summary><div class="field"><label for="duration">${t("Минуты, с шагом 30")}</label><input id="duration" data-field="duration" type="number" min="30" max="480" step="30" value="${form.duration}"></div></details></section>
      <section class="form-section form-days"><h3><span class="step-no">3</span>${form.mode === 'once' ? t("Какие даты рассматриваем") : t("Какие дни рассматриваем")}</h3>${form.mode === 'once' ? `<p class="form-help">${t("Добавьте до 7 конкретных дат по Праге.")}</p><div class="date-picker-row"><div class="field"><label for="meeting-date">${t("Дата встречи")}</label><input id="meeting-date" data-field="dateDraft" type="date" min="${pragueToday()}" max="${addDateDays(pragueToday(), 365)}" value="${h(form.dateDraft)}"></div><button type="button" class="btn secondary" data-action="add-date" ${form.dates.size >= 7 ? 'disabled' : ''}>${icon('plus', 15)}${t("Добавить дату")}</button></div><div class="date-choices">${[...form.dates].sort().map(date => `<button type="button" class="date-chip" data-action="remove-date" data-date="${h(date)}" aria-label="${h(t('Убрать дату') + ' ' + dateLabel(date))}">${h(dateLabel(date, true))}<span aria-hidden="true">×</span></button>`).join('')}</div>` : `<p class="form-help">${t("Каждую обычную неделю, по Праге.")}</p><div class="form-shortcuts"><button type="button" class="preset-chip ${form.days.size === 5 && [0,1,2,3,4].every(day => form.days.has(day)) ? 'active' : ''}" data-action="form-days-preset" data-days="0,1,2,3,4">${t("Будни")}</button><button type="button" class="preset-chip ${form.days.size === 2 && [5,6].every(day => form.days.has(day)) ? 'active' : ''}" data-action="form-days-preset" data-days="5,6">${t("Выходные")}</button></div><div class="weekday-choices">${dayShort.map((day, i) => `<button type="button" class="choice ${form.days.has(i) ? 'active' : ''}" data-action="form-day" data-day="${i}" aria-pressed="${form.days.has(i)}">${day}</button>`).join('')}</div>`}

        <div class="form-shortcuts"><button type="button" class="preset-chip" data-action="form-time-preset" data-from="18:00" data-to="21:00">${t("После работы")} <span>18–21</span></button><button type="button" class="preset-chip" data-action="form-time-preset" data-from="10:00" data-to="16:00">${t("Днём")} <span>10–16</span></button></div><div class="time-fields"><div class="field"><label for="from">${t("Не раньше")}</label><select id="from" data-field="from">${timeOptions(form.from, 0, 1410)}</select></div><div class="field"><label for="to">${t("Заканчиваем до")}</label><select id="to" data-field="to" aria-describedby="form-feedback">${timeOptions(form.to, 30, 1440)}</select></div></div>
        <details class="advanced" ${form.advanced ? 'open' : ''}><summary>${form.mode === 'once' ? t("Разное время по датам") : t("Разные диапазоны по дням")}</summary><div class="field"><label for="windows">${t("Оставьте пустым для дней и времени выше")}</label><textarea id="windows" data-field="windows" rows="2" placeholder="${form.mode === 'once' ? `${form.dateDraft} 18:00-21:00` : t("вт 18:00-21:00; ср 19:00-22:00")}">${form.advanced ? h(form.windows) : ''}</textarea></div></details>
      </section>
      <section class="form-section form-deadline"><h3><span class="step-no">4</span>${t("Срок ответа")}</h3><div class="time-fields deadline-fields"><div class="field"><label for="deadline-date">${t("Дата")}</label><input id="deadline-date" data-field="deadlineDate" type="date" lang="${i18n.language}" value="${h(deadlineDate)}" required></div><div class="field"><label for="deadline-time">${t("Время по Праге")}</label><select id="deadline-time" data-field="deadlineTime">${timeOptions(deadlineTime, 0, 1439, 15)}</select></div></div><p class="form-help form-note">${t("Перед сроком бот один раз напомнит тем, кто не ответил. Сбор закроется автоматически.")}</p></section>
      ${form.meetingId && data.round && data.round.state !== 'final' ? notice(t("Новый подбор заменит незавершённый подбор этой встречи. Старые ответы сохранятся. Другие встречи группы продолжатся без изменений.")) : ''}
      <aside class="form-preview" aria-label="${t("Перед публикацией")}">${formPreview()}</aside><p id="form-feedback" class="form-feedback" aria-live="polite" hidden></p>
      <button type="submit" class="btn full" ${busy ? 'disabled' : ''}>${busy ? t("Публикуем…") : t("Опубликовать в группе")}${icon('arrow', 16)}</button>
    </form></div>`;
}

function timeOptions(value, first, last, step = 30) {
  const values = Array.from({length: Math.floor((last - first) / step) + 1}, (_, i) => time(first + i * step));
  // Keep an existing deadline's exact minute when it falls between picker steps.
  if (step === 15 && /^([01]\d|2[0-3]):[0-5]\d$/.test(value) && !values.includes(value)) values.push(value);
  return values.sort().map(option => `<option value="${option}" ${value === option ? 'selected' : ''}>${option}</option>`).join('');
}

function admin() {
  const round = data.round;
  if (!round) return createView();
  return `<div><div class="admin-toolbar"><h2 class="section-title">${t("Ответы участников")}</h2><button class="btn secondary small" data-action="repeat" data-meeting="${meetingId}">${icon('refresh', 14)}${t("Подобрать заново")}</button></div><section class="card admin-card"><div class="answer-list">${round.answers.map((answer, i) => {
    const labels = answer.slots?.map(id => round.slots.find(slot => slot.id === id)).filter(Boolean) || [];
    return `<article class="answer-row"><span class="avatar hue${i % 4}">${h(initials(answer.name))}</span><div><strong>${h(answer.name)}</strong><p>${answer.slots === null ? t("Ответ ещё не сохранён") : !answer.slots.length ? t("Ни один вариант не подходит") : `${answer.slots.length} ${plural(answer.slots.length, [t("интервал"), t("интервала"), t("интервалов")])}`}</p>${labels.length ? `<details class="advanced"><summary>${t("Показать время")}</summary><p>${labels.map(slot => `${h(dayLabel(slot))}, ${slot.start_label}–${slot.end_label}`).join('<br>')}</p></details>` : ''}</div><span class="badge${answer.slots === null ? ' partial' : ''}">${answer.slots === null ? t("Ждём") : t("Сохранено")}</span></article>`;
  }).join('')}</div></section><div class="panel-actions"><button class="btn secondary" data-action="show-results">${icon('chart', 16)}${t("Посмотреть результаты")}</button>${round.state === 'open' ? `<button class="btn outline" data-action="close">${t("Закрыть сбор")}</button>` : ''}</div></div>`;
}

function dock() {
  const round = data.round;
  if (tab !== 'week' || !round?.can_answer) return '';
  const saved = !dirty && round.my_answer !== null;
  const label = explicitNone ? t("Ни один вариант") : `${selected.size} ${plural(selected.size, [t("вариант выбран"), t("варианта выбрано"), t("вариантов выбрано")])}`;
  return `<footer class="action-dock"><div class="dock-inner"><div class="dock-copy"><div class="dock-check">${icon(saved ? 'check' : 'calendar', 18)}</div><div><strong>${h(label)}</strong><span>${saved ? t("Ответ сохранён · можно изменить") : dirty ? t("Изменения ещё не сохранены") : t("Отметьте всё подходящее время")}</span></div></div><button class="btn" data-action="save" ${busy || !dirty || (!selected.size && !explicitNone) ? 'disabled' : ''}>${busy ? t("Сохраняем…") : t("Сохранить")}${icon(saved ? 'check' : 'arrow', 15)}</button></div></footer>`;
}

function syncURL() {
  if (preview || !data?.group_id) return;
  const url = new URL(location.href);
  for (const key of ['open', 'round', 'meeting', 'group', 'tgWebAppStartParam']) url.searchParams.delete(key);
  url.searchParams.set('group', data.group_id);
  if (tab === 'create') {
    url.searchParams.set('open', createForMeeting ? 'repeat' : 'create');
    if (createForMeeting) url.searchParams.set('meeting', createForMeeting);
  } else if (['meetings', 'connect'].includes(tab)) url.searchParams.set('open', tab);
  else if (data.round) {
    url.searchParams.set('round', data.round.id);
    url.searchParams.set('open', tab === 'week' ? 'week' : 'results');
  }
  if (url.href !== location.href) history.replaceState(null, '', url);
}

function render() {
  if (!data) return;
  syncURL();
  const focused = document.activeElement;
  const focusAction = focused?.dataset?.action;
  const retainActionFocus = ['day', 'person', 'duration', 'form-day', 'select-all-people', 'form-days-preset', 'form-time-preset', 'form-mode', 'add-date', 'remove-date', 'whole-day', 'clear-day'].includes(focusAction);
  const focusSelector = focused?.matches('[data-range]') ? `[data-range="${focused.dataset.range}"][data-index="${focused.dataset.index}"]${focused.tagName === 'INPUT' ? '[type="range"]' : ''}` : retainActionFocus ? [...focused.attributes].filter(attribute => attribute.name.startsWith('data-')).map(attribute => `[${attribute.name}="${CSS.escape(attribute.value)}"]`).join('') : null;
  const demoBar = preview ? `<div class="demo-bar">${t("Предпросмотр · вымышленные группы и участники · ответы не отправляются")}</div><div class="demo-controls"><button data-action="demo" data-stage="meetings">${t("Встречи")}</button><button data-action="demo" data-stage="connect">${t("Добавить группу")}</button><button data-action="demo" data-stage="open">${t("Доступность")}</button><button data-action="demo" data-stage="closed">${t("Пересечения")}</button><button data-action="demo" data-stage="voting">${t("Голосование")}</button><button data-action="demo" data-stage="final">${t("Итог")}</button><button data-action="demo" data-stage="create">${t("Новая встреча")}</button></div>` : '';
  let content;
  if (tab === 'connect' || !data.groups?.length && !data.join_group_id) content = connectView();
  else if (tab === 'meetings' && data.group_id) content = meetingsView();
  else if (data.not_invited) content = empty('users', t("Ваш ответ пока не ожидается"), t("Попросите организатора включить вас в участников встречи. Если вы только открыли ссылку группы, сначала присоединитесь к ней в приложении."), data.join_group_id ? t("Я участник этой группы") : t("К встречам группы"), data.join_group_id ? 'join-group' : 'home');
  else if (tab === 'create' && data.is_organizer) content = createView();
  else if (tab === 'admin' && data.is_organizer) content = admin();
  else if (tab === 'results') content = results();
  else content = availability();
  const wide = ['meetings', 'connect', 'create'].includes(tab) || !data.groups?.length || tab === 'results' && data.round?.state === 'voting';
  root.innerHTML = `${demoBar}<div class="shell${tab === 'week' ? ' availability-mode' : tab === 'create' ? ' create-mode' : ''}">${topbar()}${workspaceBar()}${intro()}${tabs()}<div class="layout${wide ? ' wide' : ''}"><section class="main-panel">${content}</section>${wide || data.not_invited ? '' : sidebar()}</div></div>${dock()}`;
  updateFormPreview();
  if (focusSelector) {
    let target = root.querySelector(focusSelector);
    if (target?.disabled && ['whole-day', 'clear-day'].includes(focusAction)) target = root.querySelector(`[data-action="${focusAction === 'whole-day' ? 'clear-day' : 'whole-day'}"]`);
    if (!target && focusAction === 'remove-date') target = root.querySelector('#meeting-date');
    target?.focus({preventScroll: true});
  }
  root.querySelectorAll('.range-slider').forEach(slider => {
    const row = slider.closest('.interval-row'); const range = rangesForSelection(activeDay)[Number(row.dataset.rangeIndex)];
    if (range) {
      const slots = data.round.slots.filter(slot => slot.day === activeDay);
      const low = Math.min(...slots.map(slot => slot.start)), high = Math.max(...slots.map(slot => slot.start + data.round.duration));
      slider.style.setProperty('--from', `${(range.start - low) / (high - low) * 100}%`);
      slider.style.setProperty('--to', `${(range.end - low) / (high - low) * 100}%`);
    }
  });
}

function confirmPartial(slots) {
  showModal(t("Голосовать за частичные варианты?"), t("Есть участники, которым эти интервалы не подходят, или люди без ответа. Вы явно разрешаете финальное голосование с этим ограничением. Можно расширить диапазоны и собрать доступность заново."), t("Да, начать"), () => perform('start_vote', {slots, allow_partial: true}, t("Финальное голосование запущено")), true);
}

function share() {
  if (preview) return notify(t("Демо: приглашения не отправляются"));
  const url = directLinks ? `https://t.me/${botUsername}?startapp=group_${Math.abs(groupId)}` : `https://t.me/${botUsername}?start=group_${Math.abs(groupId)}`;
  const target = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(t("Выберем удобное время для встречи. Откройте приложение, чтобы организатор мог добавить вас."))}`;
  if (tg?.initData) tg.openTelegramLink(target);
  else window.open(target, '_blank', 'noopener');
}

root.addEventListener('input', event => {
  if (!event.target.dataset.field || !form) return;
  const key = event.target.dataset.field;
  if (key === 'deadlineDate' || key === 'deadlineTime') {
    const [date, time] = form.deadline.split('T');
    form.deadline = key === 'deadlineDate' ? `${event.target.value}T${time}` : `${date}T${event.target.value}`;
  } else form[key] = key === 'duration' ? Number(event.target.value) : event.target.value;
  form.modified = true;
  if (key === 'windows') form.advanced = true;
  updateFormPreview();
});

root.addEventListener('change', event => {
  if (event.target.id === 'language-selector') {
    languagePreference = event.target.value;
    try { localStorage.setItem('meeting.language', languagePreference); } catch (_) { /* Keep this session's choice. */ }
    updateLanguage();
    clearTimeout(toastTimer);
    document.querySelector('#toast').classList.remove('show');
    if (data) render(); else renderLanding();
    document.querySelector('#language-selector')?.focus();
    return;
  }
  if (event.target.matches('[data-range]')) {
    const index = Number(event.target.dataset.index), kind = event.target.dataset.range;
    const ranges = (rangeDraftDay === activeDay && rangeDraft ? rangeDraft : rangesForSelection(activeDay)).map(range => ({...range}));
    const row = event.target.closest('.interval-row');
    const startControl = row.querySelector('input[type="range"][data-range="start"]'), endControl = row.querySelector('input[type="range"][data-range="end"]');
    let start = kind === 'start' ? Number(event.target.value) : Number(startControl.value);
    let end = kind === 'end' ? Number(event.target.value) : Number(endControl.value);
    if (kind === 'start') start = Math.min(start, end - data.round.duration);
    else end = Math.max(end, start + data.round.duration);
    ranges[index] = {day: activeDay, start, end};
    rangeDraft = ranges; rangeDraftDay = activeDay;
    selectionForRanges(ranges); explicitNone = false; setDirty(true); render();
    return;
  }
  if (event.target.id !== 'group-selector') return;
  const next = Number(event.target.value);
  event.target.value = String(groupId);
  leaveDraft(() => navigate(next));
});

root.addEventListener('submit', event => {
  if (event.target.id !== 'create-form') return;
  event.preventDefault();
  if (formFeedback()) { updateFormPreview(); return notify(formFeedback(), true); }
  if (form.mode !== 'once' && !form.days.size && !(form.advanced && form.windows.trim())) return notify(t("Выберите хотя бы один день."), true);
  const people = data.people.filter(person => form.participants.has(person.id));
  if (!people.length && !form.extra.trim()) return notify(t("Добавьте хотя бы одного участника."), true);
  const windows = form.advanced && form.windows.trim() ? (form.mode === 'once' ? form.windows.trim() : normalizeWindows(form.windows.trim())) : (form.mode === 'once' ? [...form.dates].sort() : [...form.days].sort().map(day => protocolDays[day])).map(day => `${day} ${form.from}-${form.to}`).join('; ');
  perform('create', {request_id: form.requestId, participants: people, extra_participants: form.extra,
    title: form.title, meeting: form.meetingId, mode: form.mode, duration: form.duration, windows, deadline: form.deadline}, t("Подбор опубликован"));
});

root.addEventListener('input', event => {
  if (!event.target.matches('input[type="range"][data-range]')) return;
  const index = Number(event.target.dataset.index), kind = event.target.dataset.range;
  const row = event.target.closest('.interval-row');
  const ranges = (rangeDraftDay === activeDay && rangeDraft ? rangeDraft : rangesForSelection(activeDay)).map(range => ({...range}));
  const startControl = row.querySelector('input[type="range"][data-range="start"]'), endControl = row.querySelector('input[type="range"][data-range="end"]');
  let start = kind === 'start' ? Number(event.target.value) : Number(startControl.value);
  let end = kind === 'end' ? Number(event.target.value) : Number(endControl.value);
  if (kind === 'start') start = Math.min(start, end - data.round.duration);
  else end = Math.max(end, start + data.round.duration);
  startControl.value = String(start); endControl.value = String(end);
  ranges[index] = {day: activeDay, start, end};
  rangeDraft = ranges; rangeDraftDay = activeDay;
  selectionForRanges(ranges); explicitNone = false; setDirty(true);
  const slots = data.round.slots.filter(slot => slot.day === activeDay);
  const low = Math.min(...slots.map(slot => slot.start)), high = Math.max(...slots.map(slot => slot.start + data.round.duration));
  const slider = row.querySelector('.range-slider');
  slider.style.setProperty('--from', `${(start - low) / (high - low) * 100}%`);
  slider.style.setProperty('--to', `${(end - low) / (high - low) * 100}%`);
  root.querySelector('.selection-summary').innerHTML = selectionSummary();
  const labels = row.querySelectorAll('.range-values select');
  if (labels[0].querySelector(`option[value="${start}"]`)) labels[0].value = String(start);
  if (labels[1].querySelector(`option[value="${end}"]`)) labels[1].value = String(end);
});

root.addEventListener('click', event => {
  const button = event.target.closest('[data-action]');
  if (!button || button.disabled) return;
  const action = button.dataset.action;
  const round = data?.round;
  if (busy) return;
  if (action === 'home') leaveDraft(() => {
    if (!data.group_id && data.groups?.length) return navigate(data.groups[0].id);
    form = null; createForMeeting = null; tab = 'meetings'; render(); window.scrollTo(0, 0);
  });
  else if (action === 'connect') leaveDraft(() => { form = null; tab = 'connect'; render(); window.scrollTo(0, 0); });
  else if (action === 'choose-group') chooseGroup();
  else if (action === 'add-bot') {
    if (preview) return notify(t("Демо: бот в реальные группы не добавляется"));
    openTelegram(data.add_bot_url);
  }
  else if (action === 'delete-meeting') {
    const meeting = data.meetings.find(item => item.id === Number(button.dataset.meeting));
    if (!data.is_organizer || meeting?.state !== 'final') return;
    const targetGroup = groupId;
    showModal(t("Удалить встречу?"), `«${meeting.title}». ${t("Встреча, её расписание и история ответов будут удалены без возможности восстановления. Сообщения в Telegram останутся.")}`, t("Удалить"), () => perform('delete_meeting', {group: targetGroup, meeting: meeting.id, round: meeting.round_id}, t("Встреча удалена")), true, true);
  }
  else if (action === 'join-group') perform('join_group', {group: data.join_group_id}, t("Вы появились в списке участников группы"));
  else if (action === 'open-meeting' || action === 'repeat') leaveDraft(() => navigate(groupId, Number(button.dataset.meeting) || meetingId, action === 'repeat'));
  else if (action === 'tab') { tab = button.dataset.tab; render(); }
  else if (action === 'day') { activeDay = Number(button.dataset.day); rangeDraft = null; rangeDraftDay = null; render(); }
  else if (action === 'slot') {
    const id = Number(button.dataset.slot);
    selected.has(id) ? selected.delete(id) : selected.add(id);
    explicitNone = false; setDirty(true); render();
    try { tg?.HapticFeedback?.selectionChanged(); } catch (_) { /* Optional. */ }
  } else if (action === 'add-range') {
    const slots = round.slots.filter(slot => slot.day === activeDay);
    const first = Math.min(...slots.map(slot => slot.start)), last = Math.max(...slots.map(slot => slot.start + round.duration));
    const ranges = rangesForSelection(activeDay).map(range => ({...range}));
    let start = first;
    for (const range of [...ranges].sort((a, b) => a.start - b.start)) {
      if (start + round.duration <= range.start) break;
      if (start < range.end) start = range.end;
    }
    if (start + round.duration > last) start = first;
    ranges.push({day: activeDay, start, end: start + round.duration});
    selectionForRanges(ranges); explicitNone = false; setDirty(true); rangeDraft = ranges; rangeDraftDay = activeDay; render();
  } else if (action === 'remove-range') {
    const ranges = rangesForSelection(activeDay).filter((_, index) => index !== Number(button.dataset.index));
    selectionForRanges(ranges); explicitNone = false; setDirty(true); rangeDraft = ranges; rangeDraftDay = activeDay; render();
  } else if (action === 'whole-day' || action === 'clear-day') {
    const dayIds = new Set(round.slots.filter(slot => slot.day === activeDay).map(slot => slot.id));
    selected = new Set([...selected].filter(id => !dayIds.has(id)));
    if (action === 'whole-day') dayIds.forEach(id => selected.add(id));
    explicitNone = false; setDirty(true); rangeDraft = null; rangeDraftDay = null; render();
  } else if (action === 'copy-day') {
    const ranges = rangesForSelection(activeDay);
    if (!ranges.length || !round.slots.some(slot => slot.day === activeDay && selected.has(slot.id))) return;
    const daysToCopy = [...new Set(round.slots.map(slot => slot.day))];
    const copy = () => {
      selected = new Set(window.Availability.toSlots(daysToCopy.flatMap(day => ranges.map(range => ({day, start: range.start, end: range.end}))), round.slots, round.duration));
      explicitNone = false; setDirty(true); rangeDraft = null; rangeDraftDay = null;
      notify(t("Интервалы скопированы на остальные дни")); render();
    };
    if (round.slots.some(slot => slot.day !== activeDay && selected.has(slot.id))) {
      showModal(t("Повторить время на других днях?"), t("Выбранные интервалы заменят ваш текущий выбор в остальных днях. Ответ отправится только после сохранения."), t("Повторить"), copy);
    } else copy();
  } else if (action === 'none') { explicitNone = !explicitNone; selected.clear(); rangeDraft = null; setDirty(true); render(); }
  else if (action === 'save') perform('availability', {slots: [...selected], none: explicitNone}, t("Ответ сохранён. Спасибо!"));
  else if (action === 'show-results') { tab = 'results'; render(); }
  else if (action === 'create') leaveDraft(() => { form = null; createForMeeting = null; tab = 'create'; render(); window.scrollTo(0, 0); });
  else if (action === 'latest') { roundId = null; refresh(); }
  else if (action === 'share') share();
  else if (action === 'close') showModal(t("Закрыть сбор доступности?"), t("Сохраним текущие ответы. После закрытия их нельзя будет изменить. Затем вы выберете варианты для финального голосования."), t("Закрыть сбор"), () => perform('close', {}, t("Сбор закрыт. Выберите варианты голосования")));
  else if (action === 'nominate') {
    const id = Number(button.dataset.slot);
    if (nominations.has(id)) nominations.delete(id);
    else if (nominations.size < 3) nominations.add(id);
    render();
  } else if (action === 'start-vote') perform('start_vote', {slots: [...nominations]}, t("Финальное голосование запущено"));
  else if (action === 'vote') perform('vote', {slot: Number(button.dataset.slot)}, t("Ваш голос сохранён"));
  else if (action === 'confirm') {
    const option = round.vote_options.find(item => item.slot_id === Number(button.dataset.slot));
    const missing = round.voted_count < round.expected_count;
    showModal(t("Зафиксировать наше время?"), `${dayLabel(option)}, ${time(option.start)}–${time(option.end)} ${t("по Праге.")}${missing ? t(" Проголосовали не все — вы явно завершаете голосование досрочно.") : ''} ${t("Итог будет опубликован в группе.")}`, t("Подтвердить"), () => perform('confirm', {slot: option.slot_id}, t("Расписание подтверждено")));
  } else if (action === 'person') {
    const id = Number(button.dataset.person);
    if (!form.participants.has(id) && form.participants.size >= 30) return notify(t("Можно выбрать не больше 30 участников."), true);
    form.participants.has(id) ? form.participants.delete(id) : form.participants.add(id);
    form.modified = true; render();
  } else if (action === 'form-mode') {
    if (form.meetingId || !['once', 'weekly'].includes(button.dataset.mode)) return;
    form.mode = button.dataset.mode; form.advanced = false; form.windows = ''; form.modified = true; render();
  } else if (action === 'add-date') {
    const input = root.querySelector('#meeting-date');
    if (!form.dateDraft || !input.checkValidity() || form.dateDraft < pragueToday() || form.dateDraft > addDateDays(pragueToday(), 365)) return notify(t("Выберите даты в течение ближайшего года."), true);
    if (form.dates.size >= 7 && !form.dates.has(form.dateDraft)) return;
    form.dates.add(form.dateDraft); form.advanced = false; form.modified = true; render();
  } else if (action === 'remove-date') {
    form.dates.delete(button.dataset.date); form.advanced = false; form.modified = true; render();
  } else if (action === 'select-all-people') {
    const people = data.people.slice(0, 30);
    form.participants = people.every(person => form.participants.has(person.id)) ? new Set() : new Set(people.map(person => person.id));
    form.modified = true; render();
  } else if (action === 'form-days-preset') {
    form.days = new Set(button.dataset.days.split(',').map(Number));
    form.advanced = false; form.modified = true; render();
  } else if (action === 'form-time-preset') {
    form.from = button.dataset.from; form.to = button.dataset.to;
    form.advanced = false; form.modified = true; render();
  } else if (action === 'duration') { form.duration = Number(button.dataset.duration); form.modified = true; render(); }
  else if (action === 'form-day') {
    const day = Number(button.dataset.day);
    form.days.has(day) ? form.days.delete(day) : form.days.add(day);
    form.advanced = false; form.modified = true; render();
  } else if (action === 'demo') {
    const stage = button.dataset.stage;
    form = null; createForMeeting = null; tab = ['meetings', 'connect', 'create'].includes(stage) ? stage : stage === 'open' ? 'week' : 'results';
    receive(demoData(['create', 'meetings', 'connect'].includes(stage) ? 'open' : stage), true);
  }
});

function demoData(stage = 'open') {
  const people = [{id: 101, name: 'Александр'}, {id: 102, name: 'Маша'}, {id: 103, name: 'Антон'}, {id: 104, name: 'Даша'}, {id: 105, name: 'Роман'}];
  const slots = [5, 6].flatMap((day, di) => Array.from({length: 9}, (_, i) => ({id: di * 9 + i + 1, day, start: 600 + i * 30, end: 720 + i * 30, start_label: time(600 + i * 30), end_label: time(720 + i * 30)})));
  const tomorrow = new Date(Date.now() + 86400000).toISOString().slice(0, 10) + 'T20:00';
  const allAnswered = stage !== 'open';
  const candidates = [slots[2], slots[3], slots[11]].map((slot, i) => ({slot_id: slot.id, day: slot.day, start: slot.start, end: slot.end, label: `${h(dayLabel(slot))}, ${slot.start_label}–${slot.end_label}`, available_count: i < 2 ? 5 : 4, expected_count: 5, common: i < 2, unavailable: i < 2 ? [] : ['Роман'], missing: []}));
  return {
    user: people[0], is_organizer: true, group_name: 'Воскресный клуб', timezone: 'Europe/Prague', bot_username: botUsername,
    group_id: -9001, meeting_id: 1,
    groups: [{id: -9001, title: 'Воскресный клуб', is_organizer: true}, {id: -9002, title: 'Друзья в Праге', is_organizer: true}],
    meetings: [{id: 1, title: 'Воскресный завтрак', round_id: 1, state: stage, duration: 120, expected_count: 5, answered_count: allAnswered ? 5 : 3, schedule: null}, {id: 2, title: 'Книжный клуб', round_id: 2, state: 'final', duration: 60, expected_count: 4, answered_count: 4, schedule: {day: 2, start: 1140, duration: 60}}, {id: 3, title: 'Прогулка после работы', round_id: 3, state: 'voting', duration: 90, expected_count: 6, answered_count: 6, schedule: null}],
    connect_url: `https://t.me/${botUsername}?start=connect`, add_bot_url: `https://t.me/${botUsername}?startgroup=connect`,
    defaults: {deadline: tomorrow}, server_time: Date.now() / 1000, people,
    round: {id: 1, meeting_id: 1, group_id: -9001, title: 'Воскресный завтрак', state: stage, duration: 120, windows: 'сб,вс 10:00-16:00', deadline: new Date(Date.now() + 86400000).toISOString(), deadline_ts: Date.now() / 1000 + 86400, deadline_label: 'завтра, 20:00', can_answer: stage === 'open', is_expected: true, expected_count: 5, answered_count: allAnswered ? 5 : 3, missing: allAnswered ? [] : ['Даша', 'Роман'], participants: people.map((person, i) => ({...person, answered: allAnswered || i < 3, voted: i < 4})), voting_missing: ['Роман'], slots, my_answer: {slots: [2, 3, 4, 11], none: false}, candidates: allAnswered ? candidates.slice(0, 2) : candidates.map(option => ({...option, available_count: 3, common: false, missing: ['Даша', 'Роман']})), preliminary: !allAnswered, nominations: [3, 4], vote_options: candidates.slice(0, 2).map((option, i) => ({...option, votes: i === 0 ? 2 : 2})), voted_count: 4, my_vote: 3, leaders: [3, 4], publication_state: stage === 'final' ? 'sent' : null, answers: people.map((person, i) => ({...person, slots: allAnswered || i < 3 ? [2, 3, 4, 11] : null}))},
    schedule: stage === 'final' ? {day: 5, start: 660, duration: 120, session_id: 1} : null,
  };
}

function demoAction(action, payload) {
  const next = structuredClone(data);
  const round = next.round;
  if (action === 'delete_meeting') {
    const meeting = next.meetings.find(item => item.id === payload.meeting);
    if (!next.is_organizer || meeting?.state !== 'final' || meeting.round_id !== payload.round) throw new Error(t("Удалить можно только встречу с завершённым подбором. Обновите список встреч."));
    next.meetings = next.meetings.filter(item => item.id !== payload.meeting);
    if (next.meeting_id === payload.meeting) { next.meeting_id = null; next.round = null; next.schedule = null; }
  }
  else if (action === 'availability') round.my_answer = {slots: payload.slots, none: payload.none};
  else if (action === 'close') round.state = 'closed';
  else if (action === 'start_vote') {
    if (round.preliminary && !payload.allow_partial) { const error = new Error('partial'); error.code = 'partial_confirmation_required'; throw error; }
    round.state = 'voting'; round.nominations = payload.slots;
    round.vote_options = round.candidates.filter(option => payload.slots.includes(option.slot_id)).map(option => ({...option, votes: 0}));
    round.voted_count = 0; round.leaders = []; round.my_vote = null; round.participants.forEach(person => person.voted = false);
  } else if (action === 'vote') {
    round.vote_options.forEach(option => { if (option.slot_id === round.my_vote) option.votes--; if (option.slot_id === payload.slot) option.votes++; });
    if (round.my_vote === null) round.voted_count++;
    round.my_vote = payload.slot;
    round.participants.forEach(person => { if (person.id === next.user.id) person.voted = true; });
    const best = Math.max(...round.vote_options.map(option => option.votes));
    round.leaders = round.vote_options.filter(option => option.votes === best).map(option => option.slot_id);
  } else if (action === 'confirm') {
    round.state = 'final';
    const option = round.vote_options.find(item => item.slot_id === payload.slot);
    next.schedule = {mode: round.mode || 'weekly', date: option.date || null, day: option.day, start: option.start, duration: round.duration, session_id: round.id};
  } else if (action === 'create') {
    const created = demoData('open');
    const mid = payload.meeting || Math.max(...data.meetings.map(item => item.id)) + 1;
    created.group_id = groupId; created.group_name = data.group_name; created.meeting_id = mid;
    const parsedSlots = new Map();
    for (const window of payload.windows.split(';')) {
      const match = /^\s*([а-яё, \d-]+)\s+(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})\s*$/i.exec(window);
      if (!match) throw new Error('Проверьте диапазоны времени.');
      const start = Number(match[2]) * 60 + Number(match[3]), end = Number(match[4]) * 60 + Number(match[5]);
      for (const name of match[1].split(',')) {
        const date = payload.mode === 'once' ? name.trim() : null;
        let day = date ? Math.floor(Date.parse(date + 'T00:00:00Z') / 86400000) + 719163 : protocolDays.indexOf(name.trim().toLowerCase());
        if (day < 0) day = days.map(value => value.toLowerCase()).indexOf(name.trim().toLowerCase());
        for (let minute = start; minute + payload.duration <= end && day >= 0; minute += 30) parsedSlots.set(`${day}:${minute}`, {day, date, start: minute, end: minute + payload.duration, start_label: time(minute), end_label: time(minute + payload.duration)});
      }
    }
    const slots = [...parsedSlots.values()].sort((a, b) => a.day - b.day || a.start - b.start).map((slot, i) => ({...slot, id: i + 1}));
    if (!slots.length) throw new Error('Встреча должна помещаться в диапазон времени.');
    created.round = {...created.round, is_expected: payload.participants.some(person => person.id === data.user.id), id: mid, meeting_id: mid, group_id: groupId, title: payload.title, mode: payload.mode || 'weekly', duration: payload.duration, windows: payload.windows,
      slots, participants: payload.participants.map(person => ({...person, answered: false, voted: false})), voting_missing: payload.participants.map(person => person.name), expected_count: payload.participants.length, answered_count: 0,
      my_answer: null, missing: payload.participants.map(person => person.name), candidates: [], nominations: [], vote_options: [], voted_count: 0, my_vote: null, leaders: []};
    created.schedule = payload.meeting ? data.schedule : null;
    created.meetings = [{id: mid, title: payload.title, mode: payload.mode || 'weekly', round_id: mid, state: 'open', duration: payload.duration, expected_count: payload.participants.length, answered_count: 0, schedule: created.schedule}, ...data.meetings.filter(item => item.id !== mid)];
    return created;
  }
  return next;
}

function renderLanding(message = '') {
  const target = roundId ? `round_${roundId}` : meetingId ? `meeting_${meetingId}` : groupId ? `group_${Math.abs(groupId)}` : 'app';
  const link = `https://t.me/${botUsername}?${directLinks ? `startapp=${target}` : `start=${target === 'app' ? 'app' : target.replace(/^round_/, 'availability_')}`}`;
  root.innerHTML = `<div class="shell"><section class="landing"><header class="landing-header">${brand()}${languagePicker()}</header><div class="card empty"><div class="landing-art"><span>${t("сб")}</span><span>${icon('check', 25)}</span><span>${t("вс")}</span></div><h2>${t("Время быть вместе.")}</h2><p>${h(message || t("Откройте приложение в Telegram, отметьте удобное время и выберите дату или день недели."))}</p><a class="btn full" href="${h(link)}">${t("Открыть в Telegram")}${icon('arrow', 16)}</a><p><a href="/?preview=1">${t("Посмотреть пример интерфейса")}</a></p></div></section></div>`;
}

async function init() {
  try {
    if (tg?.initData) {
      tg.ready(); tg.expand(); tg.MainButton?.hide();
      syncTheme();
      tg.onEvent('themeChanged', syncTheme);
    }
    const config = await fetch('/api/config').then(response => response.json());
    botUsername = config.bot_username;
    directLinks = config.direct_links === true;
    if (preview) {
      tab = ['create', 'meetings', 'connect'].includes(stageParam) ? stageParam : stageParam === 'open' ? 'week' : stageParam ? 'results' : 'meetings';
      receive(demoData(['create', 'meetings', 'connect'].includes(stageParam) ? 'open' : stageParam || 'open'), true);
    } else if (!tg?.initData) renderLanding();
    else {
      tab = requestedSpecificMeeting ? 'week' : 'meetings';
      receive(await api(stateURL()), true);
      if (initialScreen === 'create' && data.is_organizer) { tab = 'create'; render(); }
      else if (initialScreen === 'results') { tab = 'results'; render(); }
      else if (initialScreen === 'meetings' || initialScreen === 'connect') { tab = initialScreen; render(); }
      else if (initialScreen === 'meetings') { tab = 'meetings'; render(); }
      else if (initialScreen === 'repeat' && data.is_organizer && data.round) { createForMeeting = meetingId; tab = 'create'; render(); }
      setInterval(() => { if (!document.hidden && !modal.open) refresh(true); }, 12000);
    }
  } catch (error) { renderLanding(error.message || t("Не удалось загрузить приложение. Откройте его заново.")); }
}
init();
