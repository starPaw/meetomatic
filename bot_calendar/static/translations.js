// Source-language keys keep all UI copy searchable. User content is never translated.
(function (root) {
  const messages = {
  "Это результат предыдущего подбора. У встречи уже есть более новый подбор.": {
    "en": "This is a previous result. A newer poll exists for this meeting.",
    "cs": "Toto je předchozí výsledek. Pro setkání již existuje novější výběr.",
    "uk": "Це результат попереднього підбору. Для зустрічі вже є новіший підбір."
  }
,
  "Выберите еженедельную или разовую встречу.": {
    "en": "Choose a weekly or one-time meeting.",
    "cs": "Vyberte týdenní nebo jednorázové setkání.",
    "uk": "Виберіть щотижневу або разову зустріч."
  },
  "Это время попадает на перевод часов. Выберите однозначное время по Праге.": {
    "en": "This time is affected by a clock change. Choose an unambiguous Prague time.",
    "cs": "Tento čas spadá do změny času. Vyberte jednoznačný pražský čas.",
    "uk": "Цей час припадає на переведення годинника. Виберіть однозначний час за Прагою."
  },
  "Укажите существующую дату встречи в формате ГГГГ-ММ-ДД.": {
    "en": "Enter a valid meeting date as YYYY-MM-DD.",
    "cs": "Zadejte platné datum setkání ve formátu RRRR-MM-DD.",
    "uk": "Вкажіть дійсну дату зустрічі у форматі РРРР-ММ-ДД."
  },
  "Выберите даты от сегодня до 365 дней вперёд.": {
    "en": "Choose dates from today up to 365 days ahead.",
    "cs": "Vyberte data od dneška do 365 dnů dopředu.",
    "uk": "Виберіть дати від сьогодні до 365 днів уперед."
  },
  "Можно предложить не больше 7 разных дат.": {
    "en": "You can propose up to 7 different dates.",
    "cs": "Můžete navrhnout nejvýše 7 různých dat.",
    "uk": "Можна запропонувати щонайбільше 7 різних дат."
  },
  "Все варианты разовой встречи должны быть в будущем.": {
    "en": "All one-time meeting options must be in the future.",
    "cs": "Všechny možnosti jednorázového setkání musí být v budoucnu.",
    "uk": "Усі варіанти разової зустрічі мають бути в майбутньому."
  },
  "Встреча пересекает перевод часов. Выберите другой диапазон.": {
    "en": "The meeting spans a clock change. Choose another time window.",
    "cs": "Setkání překračuje změnu času. Vyberte jiný interval.",
    "uk": "Зустріч перетинає переведення годинника. Виберіть інший діапазон."
  },
  "Срок ответа должен быть раньше первого предложенного времени встречи.": {
    "en": "The response deadline must be before the earliest proposed meeting time.",
    "cs": "Termín odpovědi musí být před prvním navrženým časem setkání.",
    "uk": "Строк відповіді має бути раніше першого запропонованого часу зустрічі."
  },
  "Тип существующей встречи нельзя изменить. Создайте отдельную встречу.": {
    "en": "The type of an existing meeting cannot be changed. Create a separate meeting.",
    "cs": "Typ existujícího setkání nelze změnit. Vytvořte nové setkání.",
    "uk": "Тип наявної зустрічі змінити не можна. Створіть окрему зустріч."
  },
  "Некоторые варианты уже прошли. Создайте новый подбор с будущими датами.": {
    "en": "Some options are in the past. Start a new poll with future dates.",
    "cs": "Některé možnosti již uplynuly. Začněte nový výběr s budoucími daty.",
    "uk": "Деякі варіанти вже минули. Створіть новий підбір із майбутніми датами."
  },
  "Этот вариант уже прошёл. Выберите будущую дату или попросите новый подбор.": {
    "en": "This option is in the past. Choose a future date or ask for a new poll.",
    "cs": "Tato možnost již uplynula. Vyberte budoucí datum nebo požádejte o nový výběr.",
    "uk": "Цей варіант уже минув. Виберіть майбутню дату або попросіть новий підбір."
  },
  "Этот вариант уже прошёл. Выберите будущую дату или создайте новый подбор.": {
    "en": "This option is in the past. Choose a future date or create a new poll.",
    "cs": "Tato možnost již uplynula. Vyberte budoucí datum nebo vytvořte nový výběr.",
    "uk": "Цей варіант уже минув. Виберіть майбутню дату або створіть новий підбір."
  },
  "Формат разовой встречи: 2026-11-02 18:00-21:00; 2026-11-09 18:00-21:00.": {
    "en": "One-time format: 2026-11-02 18:00-21:00; 2026-11-09 18:00-21:00.",
    "cs": "Formát jednorázového setkání: 2026-11-02 18:00-21:00; 2026-11-09 18:00-21:00.",
    "uk": "Формат разової зустрічі: 2026-11-02 18:00-21:00; 2026-11-09 18:00-21:00."
  }
,
  "Ваш голос": {
    "en": "Your vote",
    "cs": "Váš hlas",
    "uk": "Ваш голос"
  },
  "Ваш голос:": {
    "en": "Your vote:",
    "cs": "Váš hlas:",
    "uk": "Ваш голос:"
  },
  "Время лидирующих вариантов прошло. Начните новый подбор.": {
    "en": "The leading options are in the past. Start a new poll.",
    "cs": "Časy vedoucích možností již uplynuly. Začněte nový výběr.",
    "uk": "Час варіантів-лідерів минув. Почніть новий підбір."
  },
  "Вы ещё не проголосовали. Выберите один вариант ниже.": {
    "en": "You haven't voted yet. Choose one option below.",
    "cs": "Ještě jste nehlasovali. Vyberte jednu možnost níže.",
    "uk": "Ви ще не проголосували. Виберіть один варіант нижче."
  },
  "Вы наблюдаете за голосованием.": {
    "en": "You are viewing the vote.",
    "cs": "Sledujete hlasování.",
    "uk": "Ви спостерігаєте за голосуванням."
  },
  "Вы организатор. Ваш голос не ожидается: подтвердите итог после голосования участников.": {
    "en": "You are the organizer and are not voting. Confirm the result after participants vote.",
    "cs": "Jste organizátor a nehlasujete. Po hlasování účastníků potvrďte výsledek.",
    "uk": "Ви організатор і не голосуєте. Підтвердьте результат після голосування учасників."
  },
  "Выберем удобное время для встречи. Откройте приложение, чтобы организатор мог добавить вас.": {
    "en": "Let's find a time to meet. Open the app so the organizer can add you.",
    "cs": "Najdeme vhodný čas na setkání. Otevřete aplikaci, aby vás organizátor mohl přidat.",
    "uk": "Оберімо зручний час для зустрічі. Відкрийте застосунок, щоб організатор міг вас додати."
  },
  "Выберите даты в течение ближайшего года.": {
    "en": "Choose dates within the next year.",
    "cs": "Vyberte data v průběhu příštího roku.",
    "uk": "Виберіть дати протягом найближчого року."
  },
  "Выбираем конкретную дату": {
    "en": "Choose a specific date",
    "cs": "Vybereme konkrétní datum",
    "uk": "Обираємо конкретну дату"
  },
  "Выбираем постоянный день недели": {
    "en": "Choose a regular weekday",
    "cs": "Vybereme stálý den v týdnu",
    "uk": "Обираємо постійний день тижня"
  },
  "Выбрать этот вариант": {
    "en": "Choose this option",
    "cs": "Vybrat tuto možnost",
    "uk": "Вибрати цей варіант"
  },
  "Голос можно изменить до подтверждения организатором.": {
    "en": "You can change your vote until the organizer confirms the result.",
    "cs": "Hlas můžete změnit, dokud organizátor nepotvrdí výsledek.",
    "uk": "Голос можна змінити до підтвердження організатором."
  },
  "Голос сохранён": {
    "en": "Vote saved",
    "cs": "Hlas uložen",
    "uk": "Голос збережено"
  },
  "Дата встречи": {
    "en": "Meeting date",
    "cs": "Datum setkání",
    "uk": "Дата зустрічі"
  },
  "Дата и время подтверждены. Можно строить планы.": {
    "en": "Date and time confirmed. You can make plans.",
    "cs": "Datum a čas jsou potvrzeny. Můžete plánovat.",
    "uk": "Дату й час підтверджено. Можна планувати."
  },
  "Даты встречи": {
    "en": "Meeting dates",
    "cs": "Data setkání",
    "uk": "Дати зустрічі"
  },
  "Добавить дату": {
    "en": "Add date",
    "cs": "Přidat datum",
    "uk": "Додати дату"
  },
  "Добавьте до 7 конкретных дат по Праге.": {
    "en": "Add up to 7 specific dates in Prague time.",
    "cs": "Přidejte až 7 konkrétních dat v pražském čase.",
    "uk": "Додайте до 7 конкретних дат за Прагою."
  },
  "Добавьте хотя бы одну дату.": {
    "en": "Add at least one date.",
    "cs": "Přidejte alespoň jedno datum.",
    "uk": "Додайте хоча б одну дату."
  },
  "Ещё не все проголосовали. Досрочное завершение потребует подтверждения.": {
    "en": "Some people haven't voted. Ending early requires confirmation.",
    "cs": "Ještě nehlasovali všichni. Předčasné ukončení vyžaduje potvrzení.",
    "uk": "Ще не всі проголосували. Дострокове завершення потребує підтвердження."
  },
  "Ещё не проголосовал": {
    "en": "Hasn't voted yet",
    "cs": "Ještě nehlasoval/a",
    "uk": "Ще не проголосував"
  },
  "Изменить голос": {
    "en": "Change my vote",
    "cs": "Změnit hlas",
    "uk": "Змінити голос"
  },
  "Как встречаемся": {
    "en": "Meeting type",
    "cs": "Typ setkání",
    "uk": "Як зустрічаємося"
  },
  "Какие даты рассматриваем": {
    "en": "Which dates work",
    "cs": "Která data zvažujeme",
    "uk": "Які дати розглядаємо"
  },
  "Когда голосование закончится, организатор подтвердит дату и время.": {
    "en": "The organizer will confirm the date and time after voting.",
    "cs": "Po hlasování organizátor potvrdí datum a čas.",
    "uk": "Після голосування організатор підтвердить дату й час."
  },
  "Конкретные даты": {
    "en": "Specific dates",
    "cs": "Konkrétní data",
    "uk": "Конкретні дати"
  },
  "Лидирует": {
    "en": "Leading",
    "cs": "Vede",
    "uk": "Лідирує"
  },
  "Мои даты": {
    "en": "My dates",
    "cs": "Moje data",
    "uk": "Мої дати"
  },
  "Ничья": {
    "en": "Tied",
    "cs": "Remíza",
    "uk": "Нічия"
  },
  "Ничья: выберите один из лидирующих вариантов.": {
    "en": "It's a tie. Choose one of the leading options.",
    "cs": "Remíza: vyberte jednu z vedoucích možností.",
    "uk": "Нічия: виберіть один із варіантів-лідерів."
  },
  "Одна встреча в выбранную дату": {
    "en": "One meeting on the chosen date",
    "cs": "Jedno setkání ve vybraný den",
    "uk": "Одна зустріч у вибрану дату"
  },
  "Откройте приложение в Telegram, отметьте удобное время и выберите дату или день недели.": {
    "en": "Open the app in Telegram, share your availability and choose a date or weekday.",
    "cs": "Otevřete aplikaci v Telegramu, označte vhodný čas a vyberte datum nebo den v týdnu.",
    "uk": "Відкрийте застосунок у Telegram, позначте зручний час і виберіть дату або день тижня."
  },
  "Отметьте подходящее время в предложенные даты. Ответ можно менять, пока сбор открыт.": {
    "en": "Mark suitable times on the proposed dates. You can edit your answer while the poll is open.",
    "cs": "Označte vhodné časy v navržených dnech. Odpověď můžete měnit, dokud je sběr otevřený.",
    "uk": "Позначте зручний час у запропоновані дати. Відповідь можна змінювати, поки збір відкритий."
  },
  "Подтвердите выбранный вариант — бот сообщит итог участникам.": {
    "en": "Confirm an option and the bot will notify the participants.",
    "cs": "Potvrďte možnost a bot oznámí výsledek účastníkům.",
    "uk": "Підтвердьте варіант, і бот повідомить результат учасникам."
  },
  "Постоянная встреча каждую неделю": {
    "en": "A regular meeting every week",
    "cs": "Pravidelné setkání každý týden",
    "uk": "Постійна зустріч щотижня"
  },
  "Проголосовали": {
    "en": "Voted",
    "cs": "Hlasovali",
    "uk": "Проголосували"
  },
  "Разное время по датам": {
    "en": "Different times by date",
    "cs": "Různé časy podle data",
    "uk": "Різний час за датами"
  },
  "Разовая встреча": {
    "en": "One-time meeting",
    "cs": "Jednorázové setkání",
    "uk": "Разова зустріч"
  },
  "Решение организатора": {
    "en": "Organizer's decision",
    "cs": "Rozhodnutí organizátora",
    "uk": "Рішення організатора"
  },
  "Срок ответа должен быть раньше первого варианта встречи.": {
    "en": "The response deadline must be before the earliest meeting option.",
    "cs": "Termín odpovědi musí být před první možností setkání.",
    "uk": "Строк відповіді має бути раніше першого варіанта зустрічі."
  },
  "Убрать дату": {
    "en": "Remove date",
    "cs": "Odebrat datum",
    "uk": "Прибрати дату"
  },
  "Чтобы изменить режим, создайте новую встречу.": {
    "en": "Create a new meeting to change its type.",
    "cs": "Pro změnu typu vytvořte nové setkání.",
    "uk": "Щоб змінити режим, створіть нову зустріч."
  },
  "Это время уже прошло": {
    "en": "This time has passed",
    "cs": "Tento čas již uplynul",
    "uk": "Цей час уже минув"
  },
  "голос": {
    "en": "vote",
    "cs": "hlas",
    "uk": "голос"
  },
  "голоса": {
    "en": "votes",
    "cs": "hlasy",
    "uk": "голоси"
  },
  "голосов": {
    "en": "votes",
    "cs": "hlasů",
    "uk": "голосів"
  }
,
  "Всего встреч": {
    "en": "Total meetings",
    "cs": "Všechna setkání",
    "uk": "Усього зустрічей"
  },
  "Выбираем время": {
    "en": "Finding a time",
    "cs": "Hledáme termín",
    "uk": "Обираємо час"
  },
  "Уже договорились": {
    "en": "Time confirmed",
    "cs": "Termín potvrzen",
    "uk": "Уже домовилися"
  },
  "Ваши встречи": {
    "en": "Your meetings",
    "cs": "Vaše setkání",
    "uk": "Ваші зустрічі"
  },
  "Посмотреть расписание": {
    "en": "View schedule",
    "cs": "Zobrazit rozvrh",
    "uk": "Переглянути розклад"
  },
  "Открыть голосование": {
    "en": "Open voting",
    "cs": "Otevřít hlasování",
    "uk": "Відкрити голосування"
  },
  "Посмотреть варианты": {
    "en": "Explore options",
    "cs": "Zobrazit možnosti",
    "uk": "Переглянути варіанти"
  },
  "Открыть подбор": {
    "en": "Find a time",
    "cs": "Vybrat termín",
    "uk": "Відкрити підбір"
  },
  "Время выбрано. Можно строить планы.": {
    "en": "Time confirmed. Make it a plan.",
    "cs": "Termín je vybraný. Můžete plánovat.",
    "uk": "Час обрано. Можна будувати плани."
  },
  "Остался один шаг — выбрать общий вариант.": {
    "en": "One step left: choose a time together.",
    "cs": "Zbývá jeden krok: společně vybrat termín.",
    "uk": "Залишився один крок — обрати спільний варіант."
  },
  "Ответы собраны. Выбираем варианты для голосования.": {
    "en": "Responses are in. Choosing options for the vote.",
    "cs": "Odpovědi jsou sebrané. Vybíráme možnosti pro hlasování.",
    "uk": "Відповіді зібрано. Обираємо варіанти для голосування."
  },
  "Отметьте свободное время — найдём пересечение.": {
    "en": "Share your availability to find a common time.",
    "cs": "Označte volný čas a najdeme společný termín.",
    "uk": "Позначте вільний час — знайдемо перетин."
  },
  "Меньше переписки.": {
    "en": "Less back and forth.",
    "cs": "Méně domlouvání.",
    "uk": "Менше листування."
  },
  "Больше встреч.": {
    "en": "More time together.",
    "cs": "Více setkávání.",
    "uk": "Більше зустрічей."
  },
  "Соберите своих. Отметьте удобное время. Остальное — вместе.": {
    "en": "Bring your people. Share your availability. Make a plan together.",
    "cs": "Dejte dohromady své lidi. Vyberte volný čas. Zbytek domluvíte společně.",
    "uk": "Зберіть своїх. Позначте зручний час. Решта — разом."
  },
  "Ваша неделя, ваш ритм": {
    "en": "Your week, your rhythm",
    "cs": "Váš týden, váš rytmus",
    "uk": "Ваш тиждень, ваш ритм"
  },
  "Время для своих": {
    "en": "Time for your people",
    "cs": "Čas pro vaše lidi",
    "uk": "Час для своїх"
  },
  "Отметьте удобное время или выберите «Не могу».": {
    "en": "Choose your availability or select “Unavailable”.",
    "cs": "Vyberte volný čas nebo zvolte „Nemohu“.",
    "uk": "Позначте зручний час або оберіть «Не можу»."
  },
  "Ваш выбор": {
    "en": "Your selection",
    "cs": "Váš výběr",
    "uk": "Ваш вибір"
  },
  "Повторить на остальных днях": {
    "en": "Repeat on other days",
    "cs": "Zopakovat v ostatních dnech",
    "uk": "Повторити в інші дні"
  },
  "Подходит весь диапазон": {
    "en": "The whole range works",
    "cs": "Vyhovuje celý rozsah",
    "uk": "Підходить увесь діапазон"
  },
  "Очистить день": {
    "en": "Clear day",
    "cs": "Vymazat den",
    "uk": "Очистити день"
  },
  "Встреча не помещается в диапазон. Увеличьте его или сократите длительность.": {
    "en": "The meeting does not fit this time range. Widen it or shorten the meeting.",
    "cs": "Setkání se do rozsahu nevejde. Rozšiřte ho nebo zkraťte délku setkání.",
    "uk": "Зустріч не вміщується в діапазон. Збільште його або скоротіть тривалість."
  },
  "Выберите дату": {
    "en": "Choose a date",
    "cs": "Vyberte datum",
    "uk": "Оберіть дату"
  },
  "добавленные вручную": {
    "en": "manually added participants",
    "cs": "ručně přidaní účastníci",
    "uk": "додані вручну"
  },
  "Выберите дни": {
    "en": "Choose days",
    "cs": "Vyberte dny",
    "uk": "Оберіть дні"
  },
  "Перед публикацией": {
    "en": "Before you publish",
    "cs": "Před zveřejněním",
    "uk": "Перед публікацією"
  },
  "Ответить до": {
    "en": "Respond by",
    "cs": "Odpovědět do",
    "uk": "Відповісти до"
  },
  "выбрано": {
    "en": "selected",
    "cs": "vybráno",
    "uk": "обрано"
  },
  "Снять выбор": {
    "en": "Deselect all",
    "cs": "Zrušit výběr",
    "uk": "Зняти вибір"
  },
  "Выбрать первые 30": {
    "en": "Select the first 30",
    "cs": "Vybrat prvních 30",
    "uk": "Обрати перших 30"
  },
  "Выбрать всех": {
    "en": "Select everyone",
    "cs": "Vybrat všechny",
    "uk": "Обрати всіх"
  },
  "Будни": {
    "en": "Weekdays",
    "cs": "Pracovní dny",
    "uk": "Будні"
  },
  "Выходные": {
    "en": "Weekend",
    "cs": "Víkend",
    "uk": "Вихідні"
  },
  "После работы": {
    "en": "After work",
    "cs": "Po práci",
    "uk": "Після роботи"
  },
  "Днём": {
    "en": "Daytime",
    "cs": "Přes den",
    "uk": "Удень"
  },
  "Повторить время на других днях?": {
    "en": "Repeat these times on other days?",
    "cs": "Zopakovat čas v ostatních dnech?",
    "uk": "Повторити час в інші дні?"
  },
  "Выбранные интервалы заменят ваш текущий выбор в остальных днях. Ответ отправится только после сохранения.": {
    "en": "These intervals will replace your selections on the other days. Your response is only sent when you save.",
    "cs": "Tyto intervaly nahradí váš výběr v ostatních dnech. Odpověď se odešle až po uložení.",
    "uk": "Обрані інтервали замінять ваш поточний вибір в інші дні. Відповідь надішлеться лише після збереження."
  },
  "Повторить": {
    "en": "Repeat",
    "cs": "Zopakovat",
    "uk": "Повторити"
  },
  "Можно выбрать не больше 30 участников.": {
    "en": "You can select up to 30 participants.",
    "cs": "Můžete vybrat nejvýše 30 účastníků.",
    "uk": "Можна обрати не більше 30 учасників."
  },
  "Удалить встречу": {
    "en": "Delete meeting", "cs": "Smazat setkání", "uk": "Видалити зустріч"
  },
  "Удалить встречу?": {
    "en": "Delete this meeting?", "cs": "Smazat toto setkání?", "uk": "Видалити зустріч?"
  },
  "Удалить": {
    "en": "Delete", "cs": "Smazat", "uk": "Видалити"
  },
  "Встреча удалена": {
    "en": "Meeting deleted", "cs": "Setkání bylo smazáno", "uk": "Зустріч видалено"
  },
  "Встреча, её расписание и история ответов будут удалены без возможности восстановления. Сообщения в Telegram останутся.": {
    "en": "The meeting, its schedule and response history will be permanently deleted. Telegram messages will remain.",
    "cs": "Setkání, jeho rozvrh a historie odpovědí budou nevratně smazány. Zprávy v Telegramu zůstanou.",
    "uk": "Зустріч, її розклад та історію відповідей буде видалено без можливості відновлення. Повідомлення в Telegram залишаться."
  },
  "Удалить можно только встречу с завершённым подбором. Обновите список встреч.": {
    "en": "Only a meeting with a completed scheduling poll can be deleted. Refresh the meeting list.",
    "cs": "Smazat lze jen setkání s dokončeným výběrem termínu. Obnovte seznam setkání.",
    "uk": "Видалити можна лише зустріч із завершеним підбором часу. Оновіть список зустрічей."
  },
  "Эта встреча уже удалена. Создайте новую встречу.": {
    "en": "This meeting has already been deleted. Create a new meeting.",
    "cs": "Toto setkání již bylo smazáno. Vytvořte nové setkání.",
    "uk": "Цю зустріч уже видалено. Створіть нову зустріч."
  },
  "Понедельник": {
    "en": "Monday",
    "cs": "Pondělí",
    "uk": "Понеділок"
  },
  "Вторник": {
    "en": "Tuesday",
    "cs": "Úterý",
    "uk": "Вівторок"
  },
  "Среда": {
    "en": "Wednesday",
    "cs": "Středa",
    "uk": "Середа"
  },
  "Четверг": {
    "en": "Thursday",
    "cs": "Čtvrtek",
    "uk": "Четвер"
  },
  "Пятница": {
    "en": "Friday",
    "cs": "Pátek",
    "uk": "П’ятниця"
  },
  "Суббота": {
    "en": "Saturday",
    "cs": "Sobota",
    "uk": "Субота"
  },
  "Воскресенье": {
    "en": "Sunday",
    "cs": "Neděle",
    "uk": "Неділя"
  },
  "пн": {
    "en": "Mon",
    "cs": "po",
    "uk": "пн"
  },
  "вт": {
    "en": "Tue",
    "cs": "út",
    "uk": "вт"
  },
  "ср": {
    "en": "Wed",
    "cs": "st",
    "uk": "ср"
  },
  "чт": {
    "en": "Thu",
    "cs": "čt",
    "uk": "чт"
  },
  "пт": {
    "en": "Fri",
    "cs": "pá",
    "uk": "пт"
  },
  "сб": {
    "en": "Sat",
    "cs": "so",
    "uk": "сб"
  },
  "вс": {
    "en": "Sun",
    "cs": "ne",
    "uk": "нд"
  },
  "Сбор открыт": {
    "en": "Collecting availability",
    "cs": "Sběr dostupnosti",
    "uk": "Збираємо відповіді"
  },
  "Выбираем варианты": {
    "en": "Choosing options",
    "cs": "Výběr možností",
    "uk": "Обираємо варіанти"
  },
  "Идёт голосование": {
    "en": "Voting is open",
    "cs": "Probíhá hlasování",
    "uk": "Триває голосування"
  },
  "Договорились": {
    "en": "It's a date",
    "cs": "Domluveno",
    "uk": "Домовились"
  },
  "Подбор заменён": {
    "en": "Replaced by a new poll",
    "cs": "Nahrazeno novým výběrem",
    "uk": "Замінено новим опитуванням"
  },
  "Отмена": {
    "en": "Cancel",
    "cs": "Zrušit",
    "uk": "Скасувати"
  },
  "Не удалось выполнить действие.": {
    "en": "Couldn't complete this action.",
    "cs": "Akci se nepodařilo dokončit.",
    "uk": "Не вдалося виконати дію."
  },
  "Выйти без сохранения?": {
    "en": "Leave without saving?",
    "cs": "Odejít bez uložení?",
    "uk": "Вийти без збереження?"
  },
  "Несохранённый ответ или черновик формы будет сброшен.": {
    "en": "Your unsaved answer or form will be discarded.",
    "cs": "Neuložená odpověď nebo formulář se zahodí.",
    "uk": "Незбережену відповідь або чернетку буде втрачено."
  },
  "Выйти": {
    "en": "Leave",
    "cs": "Odejít",
    "uk": "Вийти"
  },
  "Сессия завершилась. Откройте приложение через бота ещё раз.": {
    "en": "Your session expired. Open the app from the bot again.",
    "cs": "Platnost relace vypršela. Otevřete aplikaci znovu přes bota.",
    "uk": "Сесію завершено. Відкрийте застосунок через бота ще раз."
  },
  "Готово": {
    "en": "Done",
    "cs": "Hotovo",
    "uk": "Готово"
  },
  "Демо: изменение показано только в примере": {
    "en": "Demo: changes only affect this example",
    "cs": "Demo: změny platí jen pro tento příklad",
    "uk": "Демо: зміни лише в цьому прикладі"
  },
  "в.": {
    "en": "m.",
    "cs": "s.",
    "uk": "з."
  },
  "встреча": {
    "en": "meet",
    "cs": "setkání",
    "uk": "зустріч"
  },
  "время быть вместе": {
    "en": "make time for each other",
    "cs": "čas být spolu",
    "uk": "час бути разом"
  },
  "Прага · Europe/Prague": {
    "en": "Prague · Europe/Prague",
    "cs": "Praha · Europe/Prague",
    "uk": "Прага · Europe/Prague"
  },
  "Telegram-группа": {
    "en": "Telegram group",
    "cs": "Telegramová skupina",
    "uk": "Telegram-група"
  },
  "Выбрать группу": {
    "en": "Choose a group",
    "cs": "Vybrat skupinu",
    "uk": "Обрати групу"
  },
  "Пока нет подключённых групп": {
    "en": "No groups connected yet",
    "cs": "Zatím žádné připojené skupiny",
    "uk": "Поки немає підключених груп"
  },
  "Добавить группу": {
    "en": "Add group",
    "cs": "Přidat skupinu",
    "uk": "Додати групу"
  },
  "встречи": {
    "en": "meetings",
    "cs": "setkání",
    "uk": "зустрічі"
  },
  "встреч": {
    "en": "meetings",
    "cs": "setkání",
    "uk": "зустрічей"
  },
  "Начнём с первой встречи": {
    "en": "Let's start with a meeting",
    "cs": "Začněme prvním setkáním",
    "uk": "Почнімо з першої зустрічі"
  },
  "Новая встреча": {
    "en": "New meeting",
    "cs": "Nové setkání",
    "uk": "Нова зустріч"
  },
  "Время собраться": {
    "en": "Time to get together",
    "cs": "Čas se sejít",
    "uk": "Час зібратися"
  },
  "Дайте встрече название, выберите участников и предложите дни. Другие встречи группы останутся без изменений.": {
    "en": "Name your meeting, choose people and suggest days. Other meetings stay as they are.",
    "cs": "Pojmenujte setkání, vyberte účastníky a navrhněte dny. Ostatní setkání se nezmění.",
    "uk": "Назвіть зустріч, оберіть учасників і запропонуйте дні. Інші зустрічі залишаться без змін."
  },
  "Организатор скоро создаст первую встречу.": {
    "en": "The organizer will create the first meeting soon.",
    "cs": "Organizátor brzy vytvoří první setkání.",
    "uk": "Організатор невдовзі створить першу зустріч."
  },
  "Создать встречу": {
    "en": "Create meeting",
    "cs": "Vytvořit setkání",
    "uk": "Створити зустріч"
  },
  "· по Праге": {
    "en": "· Prague time",
    "cs": "· pražský čas",
    "uk": "· за Прагою"
  },
  "Выбираем постоянное время для обычной недели.": {
    "en": "Finding a regular time for your week.",
    "cs": "Hledáme pravidelný čas v týdnu.",
    "uk": "Обираємо постійний час для звичайного тижня."
  },
  "Ответили": {
    "en": "Answered",
    "cs": "Odpovědělo",
    "uk": "Відповіли"
  },
  "из": {
    "en": "of",
    "cs": "z",
    "uk": "із"
  },
  "мин": {
    "en": "min",
    "cs": "min",
    "uk": "хв"
  },
  "Участники ещё не выбраны": {
    "en": "Participants haven't been selected yet",
    "cs": "Účastníci ještě nejsou vybraní",
    "uk": "Учасників ще не обрано"
  },
  "Открыть встречу": {
    "en": "Open meeting",
    "cs": "Otevřít setkání",
    "uk": "Відкрити зустріч"
  },
  "Подобрать время заново": {
    "en": "Find a new time",
    "cs": "Najít nový čas",
    "uk": "Обрати час знову"
  },
  "Ваша группа — ваши встречи": {
    "en": "Your group, your gatherings",
    "cs": "Vaše skupina, vaše setkání",
    "uk": "Ваша група — ваші зустрічі"
  },
  "Подключите Telegram-группу, где вы администратор. В каждой группе можно создать несколько встреч со своим составом и расписанием.": {
    "en": "Connect a Telegram group you administer. Each group can have several meetings with their own people and schedules.",
    "cs": "Připojte telegramovou skupinu, kterou spravujete. Každá skupina může mít více setkání s vlastními účastníky a rozvrhem.",
    "uk": "Підключіть Telegram-групу, де ви адміністратор. У кожній групі може бути кілька зустрічей зі своїми учасниками та розкладом."
  },
  "Добавьте бота в нужную группу, если его там ещё нет.": {
    "en": "Add the bot to your group if it isn't there yet.",
    "cs": "Přidejte bota do skupiny, pokud tam ještě není.",
    "uk": "Додайте бота до групи, якщо його там ще немає."
  },
  "Выберите эту группу. Проверим ваши права — и можно создавать встречи.": {
    "en": "Choose the group. We'll check your permissions and you're ready to create meetings.",
    "cs": "Vyberte skupinu. Ověříme vaše oprávnění a můžete vytvářet setkání.",
    "uk": "Оберіть групу. Перевіримо ваші права — і можна створювати зустрічі."
  },
  "Открываем выбор…": {
    "en": "Opening picker…",
    "cs": "Otevíráme výběr…",
    "uk": "Відкриваємо вибір…"
  },
  "Добавить бота в другую группу": {
    "en": "Add bot to another group",
    "cs": "Přidat bota do jiné skupiny",
    "uk": "Додати бота до іншої групи"
  },
  "Вернуться к встречам": {
    "en": "Back to meetings",
    "cs": "Zpět na setkání",
    "uk": "Назад до зустрічей"
  },
  "Демо: реальные группы не подключаются": {
    "en": "Demo: real groups aren't connected",
    "cs": "Demo: skutečné skupiny se nepřipojují",
    "uk": "Демо: справжні групи не підключаються"
  },
  "Проверяем группу. Она появится здесь через несколько секунд.": {
    "en": "Checking the group. It will appear here in a few seconds.",
    "cs": "Ověřujeme skupinu. Za pár sekund se zde objeví.",
    "uk": "Перевіряємо групу. Вона з’явиться тут за кілька секунд."
  },
  "Группа подключена": {
    "en": "Group connected",
    "cs": "Skupina připojena",
    "uk": "Групу підключено"
  },
  "Открыть выбор в чате с ботом?": {
    "en": "Open the picker in the bot chat?",
    "cs": "Otevřít výběr v chatu s botem?",
    "uk": "Відкрити вибір у чаті з ботом?"
  },
  "Можно подключить группу через команду /group в личном чате.": {
    "en": "You can connect a group using /group in the bot's private chat.",
    "cs": "Skupinu můžete připojit příkazem /group v soukromém chatu s botem.",
    "uk": "Можна підключити групу командою /group у приватному чаті з ботом."
  },
  "Открыть чат": {
    "en": "Open chat",
    "cs": "Otevřít chat",
    "uk": "Відкрити чат"
  },
  "Соберём своих.": {
    "en": "Bring your people together.",
    "cs": "Sejděte se se svými.",
    "uk": "Зберімо своїх."
  },
  "Наши встречи.": {
    "en": "Our meetings.",
    "cs": "Naše setkání.",
    "uk": "Наші зустрічі."
  },
  "Подберём время заново.": {
    "en": "Let's find a new time.",
    "cs": "Najděme nový čas.",
    "uk": "Оберімо час знову."
  },
  "Новая встреча.": {
    "en": "A new reason to meet.",
    "cs": "Nový důvod se sejít.",
    "uk": "Нова нагода зустрітися."
  },
  "Когда вам удобно?": {
    "en": "When works for you?",
    "cs": "Kdy máte čas?",
    "uk": "Коли вам зручно?"
  },
  "Время нашлось.": {
    "en": "We found our time.",
    "cs": "Našli jsme náš čas.",
    "uk": "Час знайшовся."
  },
  "Выберем наш вариант.": {
    "en": "Let's choose our time.",
    "cs": "Vyberme náš čas.",
    "uk": "Оберімо наш варіант."
  },
  "Найдём пересечение.": {
    "en": "Find our common ground.",
    "cs": "Najděme společný čas.",
    "uk": "Знайдімо спільний час."
  },
  "Несколько групп. Любое количество поводов встретиться.": {
    "en": "Different groups. So many reasons to meet.",
    "cs": "Různé skupiny. Tolik důvodů se sejít.",
    "uk": "Різні групи. Безліч приводів зустрітися."
  },
  "У каждой встречи — свои участники, ответы и постоянное время.": {
    "en": "Each meeting has its own people, answers and regular time.",
    "cs": "Každé setkání má své účastníky, odpovědi a pravidelný čas.",
    "uk": "Кожна зустріч має своїх учасників, відповіді та постійний час."
  },
  "Задайте рамки — каждый выберет удобное время.": {
    "en": "Set the boundaries. Everyone picks what works.",
    "cs": "Určete rozmezí. Každý si vybere, kdy může.",
    "uk": "Задайте межі — кожен обере зручний час."
  },
  "Отметьте все удобные интервалы. Найдём время для всех.": {
    "en": "Mark all the times you're free. We'll find a moment for everyone.",
    "cs": "Označte všechen volný čas. Najdeme chvíli pro všechny.",
    "uk": "Позначте всі зручні проміжки. Знайдемо час для всіх."
  },
  "Все ответы в одном месте. Дальше — общее решение.": {
    "en": "All answers in one place. A shared decision comes next.",
    "cs": "Všechny odpovědi na jednom místě. Pak společné rozhodnutí.",
    "uk": "Усі відповіді в одному місці. Далі — спільне рішення."
  },
  "Встречи в Telegram": {
    "en": "Meet on Telegram",
    "cs": "Setkání v Telegramu",
    "uk": "Зустрічі в Telegram"
  },
  "Встреча": {
    "en": "Meeting",
    "cs": "Setkání",
    "uk": "Зустріч"
  },
  "До": {
    "en": "Until",
    "cs": "Do",
    "uk": "До"
  },
  "Разделы": {
    "en": "Sections",
    "cs": "Sekce",
    "uk": "Розділи"
  },
  "Встречи": {
    "en": "Meetings",
    "cs": "Setkání",
    "uk": "Зустрічі"
  },
  "Моя неделя": {
    "en": "My week",
    "cs": "Můj týden",
    "uk": "Мій тиждень"
  },
  "Результаты": {
    "en": "Results",
    "cs": "Výsledky",
    "uk": "Результати"
  },
  "Управление": {
    "en": "Manage",
    "cs": "Správa",
    "uk": "Керування"
  },
  "Один раз договориться": {
    "en": "Agree once. Meet every week.",
    "cs": "Domluvte se jednou",
    "uk": "Домовитися один раз"
  },
  "Выбираем постоянный день и время для обычной недели. Всё — по Праге, в том числе после перевода часов.": {
    "en": "Choose a regular day and time. Always Prague time, including daylight saving changes.",
    "cs": "Vyberte pravidelný den a čas. Vždy podle Prahy, i po změně času.",
    "uk": "Обираємо постійний день і час. Усе за Прагою, зокрема після переведення годинників."
  },
  "Еженедельная встреча": {
    "en": "Weekly meeting",
    "cs": "Týdenní setkání",
    "uk": "Щотижнева зустріч"
  },
  "· наш ритм": {
    "en": "· our rhythm",
    "cs": "· náš rytmus",
    "uk": "· наш ритм"
  },
  "1 час": {
    "en": "1 hour",
    "cs": "1 hodina",
    "uk": "1 година"
  },
  "минут": {
    "en": "minutes",
    "cs": "minut",
    "uk": "хвилин"
  },
  "Обычная неделя": {
    "en": "A typical week",
    "cs": "Běžný týden",
    "uk": "Звичайний тиждень"
  },
  "Время по Праге": {
    "en": "Prague time",
    "cs": "Pražský čas",
    "uk": "Час за Прагою"
  },
  "участник": {
    "en": "participant",
    "cs": "účastník",
    "uk": "учасник"
  },
  "участника": {
    "en": "participants",
    "cs": "účastníci",
    "uk": "учасники"
  },
  "участников": {
    "en": "participants",
    "cs": "účastníků",
    "uk": "учасників"
  },
  "Ещё ждём:": {
    "en": "Still waiting for:",
    "cs": "Ještě čekáme na:",
    "uk": "Ще чекаємо:"
  },
  "Все участники ответили": {
    "en": "Everyone has answered",
    "cs": "Všichni odpověděli",
    "uk": "Усі учасники відповіли"
  },
  "Для вашей обычной недели": {
    "en": "For your everyday week",
    "cs": "Pro váš běžný týden",
    "uk": "Для вашого звичайного тижня"
  },
  "Выбирайте время, которое обычно свободно. Ответ можно менять, пока сбор открыт.": {
    "en": "Pick times you're usually free. You can change your answer while collection is open.",
    "cs": "Vyberte časy, kdy obvykle můžete. Odpověď lze měnit, dokud je sběr otevřený.",
    "uk": "Оберіть час, коли зазвичай вільні. Відповідь можна змінювати, доки збір відкритий."
  },
  "Пока нет подбора": {
    "en": "No availability poll yet",
    "cs": "Zatím žádný výběr času",
    "uk": "Поки немає опитування"
  },
  "Организатор скоро предложит дни и время для встречи.": {
    "en": "The organizer will suggest days and times soon.",
    "cs": "Organizátor brzy navrhne dny a časy.",
    "uk": "Організатор невдовзі запропонує дні та час."
  },
  "Вы управляете подбором": {
    "en": "You're managing this poll",
    "cs": "Spravujete tento výběr",
    "uk": "Ви керуєте опитуванням"
  },
  "Ваш ответ сейчас не ожидается. Перейдите к результатам, чтобы посмотреть доступность участников.": {
    "en": "Your answer isn't expected. Open results to see participant availability.",
    "cs": "Vaše odpověď se neočekává. Dostupnost účastníků najdete ve výsledcích.",
    "uk": "Ваша відповідь зараз не очікується. Перейдіть до результатів, щоб побачити доступність учасників."
  },
  "Доступность уже собрана": {
    "en": "Availability collected",
    "cs": "Dostupnost je sesbíraná",
    "uk": "Доступність уже зібрана"
  },
  "Ответы сохранены. Следующий шаг — выбрать и подтвердить общее время.": {
    "en": "Answers are saved. Next, choose and confirm a time together.",
    "cs": "Odpovědi jsou uložené. Teď vyberte a potvrďte společný čas.",
    "uk": "Відповіді збережено. Далі оберіть і підтвердьте спільний час."
  },
  "Открыть результаты": {
    "en": "Open results",
    "cs": "Otevřít výsledky",
    "uk": "Відкрити результати"
  },
  "Интервал": {
    "en": "Time window",
    "cs": "Interval",
    "uk": "Проміжок"
  },
  "Удалить интервал": {
    "en": "Remove time window",
    "cs": "Odstranit interval",
    "uk": "Видалити проміжок"
  },
  "Удалить": {
    "en": "Remove",
    "cs": "Odstranit",
    "uk": "Видалити"
  },
  "С": {
    "en": "From",
    "cs": "Od",
    "uk": "З"
  },
  "Начало интервала": {
    "en": "Start of time window",
    "cs": "Začátek intervalu",
    "uk": "Початок проміжку"
  },
  "Конец интервала": {
    "en": "End of time window",
    "cs": "Konec intervalu",
    "uk": "Кінець проміжку"
  },
  "Когда вы свободны?": {
    "en": "When are you free?",
    "cs": "Kdy máte volno?",
    "uk": "Коли ви вільні?"
  },
  "мин встреча": {
    "en": "min meeting",
    "cs": "min setkání",
    "uk": "хв зустріч"
  },
  "Выберите свободные промежутки. Подойдут любые начала встречи внутри них.": {
    "en": "Choose free time windows. Any meeting that fits inside them works.",
    "cs": "Vyberte volné intervaly. Setkání se do nich musí celé vejít.",
    "uk": "Оберіть вільні проміжки. Зустріч має повністю в них уміститися."
  },
  "Дни недели": {
    "en": "Weekdays",
    "cs": "Dny v týdnu",
    "uk": "Дні тижня"
  },
  "вариантов": {
    "en": "options",
    "cs": "možností",
    "uk": "варіантів"
  },
  "вариант": {
    "en": "option",
    "cs": "možnost",
    "uk": "варіант"
  },
  "варианта": {
    "en": "options",
    "cs": "možnosti",
    "uk": "варіанти"
  },
  "Скопировать на другие дни": {
    "en": "Copy to other days",
    "cs": "Kopírovat na další dny",
    "uk": "Скопіювати на інші дні"
  },
  "Пока нет интервалов. Добавьте время, когда вы свободны.": {
    "en": "No time windows yet. Add a time you're free.",
    "cs": "Zatím žádné intervaly. Přidejte čas, kdy můžete.",
    "uk": "Поки немає проміжків. Додайте час, коли ви вільні."
  },
  "Добавить интервал": {
    "en": "Add time window",
    "cs": "Přidat interval",
    "uk": "Додати проміжок"
  },
  "Не могу": {
    "en": "I can't make it",
    "cs": "Nemohu dorazit",
    "uk": "Не можу"
  },
  "Ни один предложенный вариант не подходит": {
    "en": "None of these times work for me",
    "cs": "Žádný z termínů mi nevyhovuje",
    "uk": "Жоден із варіантів не підходить"
  },
  "ВАРИАНТ": {
    "en": "OPTION",
    "cs": "MOŽNOST",
    "uk": "ВАРІАНТ"
  },
  "Подходит всем": {
    "en": "Works for everyone",
    "cs": "Vyhovuje všem",
    "uk": "Підходить усім"
  },
  "Предварительно": {
    "en": "Preliminary",
    "cs": "Předběžně",
    "uk": "Попередньо"
  },
  "Частичное совпадение": {
    "en": "Partial match",
    "cs": "Částečná shoda",
    "uk": "Частковий збіг"
  },
  "Доступны для встречи": {
    "en": "Available to meet",
    "cs": "Mohou se zúčastnit",
    "uk": "Можуть зустрітися"
  },
  "Кого не хватает": {
    "en": "Who's missing",
    "cs": "Kdo chybí",
    "uk": "Кого бракує"
  },
  "Не могут:": {
    "en": "Unavailable:",
    "cs": "Nemohou:",
    "uk": "Не можуть:"
  },
  "Нет ответа:": {
    "en": "No answer:",
    "cs": "Bez odpovědi:",
    "uk": "Немає відповіді:"
  },
  "Включён в голосование": {
    "en": "Included in vote",
    "cs": "Zařazeno do hlasování",
    "uk": "Додано до голосування"
  },
  "Включить в голосование": {
    "en": "Include in vote",
    "cs": "Zařadit do hlasování",
    "uk": "Додати до голосування"
  },
  "Голосов": {
    "en": "Votes",
    "cs": "Hlasy",
    "uk": "Голосів"
  },
  " Ваш голос": {
    "en": " Your vote",
    "cs": " Váš hlas",
    "uk": " Ваш голос"
  },
  "Голосовать за этот вариант": {
    "en": "Vote for this time",
    "cs": "Hlasovat pro tento čas",
    "uk": "Голосувати за цей час"
  },
  "Подтвердить": {
    "en": "Confirm",
    "cs": "Potvrdit",
    "uk": "Підтвердити"
  },
  "Начнём с первого подбора": {
    "en": "Let's create the first poll",
    "cs": "Začněme prvním výběrem",
    "uk": "Почнімо з першого опитування"
  },
  "Выберите участников, дни недели и время. Бот соберёт ответы в вашей группе.": {
    "en": "Choose people, days and times. The bot collects answers in your group.",
    "cs": "Vyberte účastníky, dny a časy. Bot shromáždí odpovědi ve skupině.",
    "uk": "Оберіть учасників, дні та час. Бот збере відповіді у вашій групі."
  },
  "Создать подбор": {
    "en": "Create poll",
    "cs": "Vytvořit výběr",
    "uk": "Створити опитування"
  },
  "Есть новый подбор": {
    "en": "There's a newer poll",
    "cs": "Existuje novější výběr",
    "uk": "Є нове опитування"
  },
  "Этот подбор заменён новым. Откройте приложение из последнего сообщения в группе.": {
    "en": "This poll was replaced. Open the app from the latest group message.",
    "cs": "Tento výběr byl nahrazen. Otevřete aplikaci z poslední zprávy ve skupině.",
    "uk": "Це опитування замінено. Відкрийте застосунок з останнього повідомлення в групі."
  },
  "Открыть текущий": {
    "en": "Open current poll",
    "cs": "Otevřít aktuální výběr",
    "uk": "Відкрити поточне"
  },
  "Вы организатор. Ваш голос в этом подборе не ожидается. Голосуют:": {
    "en": "You're the organizer and aren't voting in this poll. Voters:",
    "cs": "Jste organizátor a v tomto výběru nehlasujete. Hlasují:",
    "uk": "Ви організатор і не голосуєте в цьому опитуванні. Голосують:"
  },
  ". После первого голоса вы сможете подтвердить итог.": {
    "en": ". You can confirm the result after the first vote.",
    "cs": ". Výsledek můžete potvrdit po prvním hlasu.",
    "uk": ". Після першого голосу ви зможете підтвердити підсумок."
  },
  "Какой вариант выбираем?": {
    "en": "Which time shall we choose?",
    "cs": "Který čas vybereme?",
    "uk": "Який час обираємо?"
  },
  "проголосовали.": {
    "en": "voted.",
    "cs": "hlasovalo.",
    "uk": "проголосували."
  },
  " Выберите один вариант. Голос можно изменить.": {
    "en": " Choose one option. You can change your vote.",
    "cs": " Vyberte jednu možnost. Hlas lze změnit.",
    "uk": " Оберіть один варіант. Голос можна змінити."
  },
  "Есть участники без ответа о доступности. Организатор явно разрешил финальное голосование.": {
    "en": "Some people haven't shared availability. The organizer explicitly allowed the final vote.",
    "cs": "Někteří účastníci neuvedli dostupnost. Organizátor výslovně povolil finální hlasování.",
    "uk": "Деякі учасники не відповіли про доступність. Організатор явно дозволив фінальне голосування."
  },
  "Голоса разделились поровну. Решение за вами — подтвердите одного из лидеров.": {
    "en": "It's a tie. Confirm one of the leading options.",
    "cs": "Hlasy jsou vyrovnané. Potvrďte jednu z vedoucích možností.",
    "uk": "Голоси розділилися порівну. Підтвердьте один із провідних варіантів."
  },
  "Подтверждение появится после первого голоса.": {
    "en": "Confirmation is available after the first vote.",
    "cs": "Potvrzení bude dostupné po prvním hlasu.",
    "uk": "Підтвердження з’явиться після першого голосу."
  },
  "Ждём первые ответы": {
    "en": "Waiting for the first answers",
    "cs": "Čekáme na první odpovědi",
    "uk": "Чекаємо на перші відповіді"
  },
  "Как только участники отметят удобное время, здесь появятся лучшие варианты.": {
    "en": "The best options appear here as people share their availability.",
    "cs": "Nejlepší možnosti se zde objeví, jakmile účastníci označí volný čas.",
    "uk": "Коли учасники позначать зручний час, тут з’являться найкращі варіанти."
  },
  "Пригласить участников": {
    "en": "Invite people",
    "cs": "Pozvat účastníky",
    "uk": "Запросити учасників"
  },
  "Закрыть сбор": {
    "en": "Close collection",
    "cs": "Uzavřít sběr",
    "uk": "Закрити збір"
  },
  "Один общий вариант": {
    "en": "One time works for everyone",
    "cs": "Jeden společný termín",
    "uk": "Один спільний варіант"
  },
  "Вот наше общее время": {
    "en": "Here's our shared time",
    "cs": "Tady je náš společný čas",
    "uk": "Ось наш спільний час"
  },
  "Лучшие совпадения": {
    "en": "Best matches",
    "cs": "Nejlepší shody",
    "uk": "Найкращі збіги"
  },
  "Это время отметили все ожидаемые участники.": {
    "en": "All expected participants selected this time.",
    "cs": "Tento čas vybrali všichni očekávaní účastníci.",
    "uk": "Цей час позначили всі очікувані учасники."
  },
  "Считаем по сохранённым ответам. Итог пока предварительный.": {
    "en": "Based on saved answers. Results are preliminary.",
    "cs": "Podle uložených odpovědí. Výsledky jsou předběžné.",
    "uk": "Рахуємо за збереженими відповідями. Підсумок поки попередній."
  },
  "Общего времени нет. Ниже — варианты с наибольшим числом участников.": {
    "en": "No time works for everyone. These options include the most people.",
    "cs": "Žádný čas nevyhovuje všem. Tyto možnosti zahrnují nejvíce účastníků.",
    "uk": "Спільного часу немає. Тут варіанти з найбільшою кількістю учасників."
  },
  ". Ещё ждём:": {
    "en": ". Still waiting for:",
    "cs": ". Ještě čekáme na:",
    "uk": ". Ще чекаємо:"
  },
  ". Эти варианты пока нельзя считать подходящими всем.": {
    "en": ". These options aren't confirmed to work for everyone.",
    "cs": ". Tyto možnosti zatím nelze považovat za vhodné pro všechny.",
    "uk": ". Ці варіанти поки не можна вважати зручними для всіх."
  },
  "Закрыть сбор и выбрать варианты": {
    "en": "Close collection and choose options",
    "cs": "Uzavřít sběr a vybrat možnosti",
    "uk": "Закрити збір та обрати варіанти"
  },
  "После закрытия участники больше не смогут менять доступность.": {
    "en": "People can't change their availability after collection closes.",
    "cs": "Po uzavření sběru už nelze měnit dostupnost.",
    "uk": "Після закриття учасники не зможуть змінювати доступність."
  },
  "Начать голосование": {
    "en": "Start voting",
    "cs": "Spustit hlasování",
    "uk": "Почати голосування"
  },
  "Отметьте до трёх вариантов. Для частичных совпадений потребуется ваше явное решение.": {
    "en": "Select up to three options. Partial matches need your explicit approval.",
    "cs": "Vyberte až tři možnosti. Částečné shody vyžadují váš výslovný souhlas.",
    "uk": "Оберіть до трьох варіантів. Часткові збіги потребують вашого явного рішення."
  },
  "Организатор выбирает варианты финального голосования.": {
    "en": "The organizer is selecting options for the final vote.",
    "cs": "Organizátor vybírá možnosti pro finální hlasování.",
    "uk": "Організатор обирає варіанти фінального голосування."
  },
  "Договорились.": {
    "en": "It's a date.",
    "cs": "Domluveno.",
    "uk": "Домовились."
  },
  "Наш постоянный день и время. Можно строить планы.": {
    "en": "Our regular day and time. Make room for good company.",
    "cs": "Náš pravidelný den a čas. Můžete plánovat.",
    "uk": "Наш постійний день і час. Можна будувати плани."
  },
  "Каждую неделю": {
    "en": "Every week",
    "cs": "Každý týden",
    "uk": "Щотижня"
  },
  "По Праге ·": {
    "en": "Prague time ·",
    "cs": "Pražský čas ·",
    "uk": "За Прагою ·"
  },
  "Местное время сохранится при переводе часов.": {
    "en": "Local time stays the same when the clocks change.",
    "cs": "Místní čas zůstane stejný i při změně času.",
    "uk": "Місцевий час збережеться після переведення годинників."
  },
  "Итог опубликован в группе.": {
    "en": "The result was posted to the group.",
    "cs": "Výsledek je zveřejněný ve skupině.",
    "uk": "Підсумок опубліковано в групі."
  },
  "Расписание сохранено. Доставляем итог в группу.": {
    "en": "Schedule saved. Delivering the result to the group.",
    "cs": "Rozvrh uložen. Odesíláme výsledek do skupiny.",
    "uk": "Розклад збережено. Надсилаємо підсумок до групи."
  },
  "Новый подбор времени": {
    "en": "Find a new meeting time",
    "cs": "Nový výběr času",
    "uk": "Новий вибір часу"
  },
  "Название встречи": {
    "en": "Meeting name",
    "cs": "Název setkání",
    "uk": "Назва зустрічі"
  },
  "Например, завтрак команды": {
    "en": "For example, team breakfast",
    "cs": "Například týmová snídaně",
    "uk": "Наприклад, сніданок команди"
  },
  "Группа:": {
    "en": "Group:",
    "cs": "Skupina:",
    "uk": "Група:"
  },
  "Меняем время только этой встречи.": {
    "en": "Only this meeting's time will change.",
    "cs": "Měníme čas pouze tohoto setkání.",
    "uk": "Змінюємо час лише цієї зустрічі."
  },
  "У новой встречи будут свои ответы и расписание.": {
    "en": "This meeting will have its own answers and schedule.",
    "cs": "Nové setkání bude mít vlastní odpovědi a rozvrh.",
    "uk": "Нова зустріч матиме свої відповіді та розклад."
  },
  "Кто встречается": {
    "en": "Who's coming",
    "cs": "Kdo se potká",
    "uk": "Хто зустрічається"
  },
  "Выберите всех, чьи ответы нужны. Включите себя, если тоже участвуете.": {
    "en": "Choose everyone whose answer matters. Include yourself if you're joining.",
    "cs": "Vyberte všechny, jejichž odpověď potřebujete. Přidejte i sebe, pokud se účastníte.",
    "uk": "Оберіть усіх, чиї відповіді потрібні. Додайте себе, якщо також берете участь."
  },
  "Добавить по @имени или ID": {
    "en": "Add by @username or ID",
    "cs": "Přidat podle @jména nebo ID",
    "uk": "Додати за @іменем або ID"
  },
  "@anna; 123456:Борис": {
    "en": "@anna; 123456:Boris",
    "cs": "@anna; 123456:Boris",
    "uk": "@anna; 123456:Борис"
  },
  "Пригласить участника в группу приложения": {
    "en": "Invite someone to the app group",
    "cs": "Pozvat účastníka do skupiny aplikace",
    "uk": "Запросити учасника до групи застосунку"
  },
  "Сколько времени нужно": {
    "en": "How long do you need",
    "cs": "Kolik času potřebujete",
    "uk": "Скільки часу потрібно"
  },
  "30 мин": {
    "en": "30 min",
    "cs": "30 min",
    "uk": "30 хв"
  },
  "1,5 часа": {
    "en": "1.5 hours",
    "cs": "1,5 hodiny",
    "uk": "1,5 години"
  },
  "2 часа": {
    "en": "2 hours",
    "cs": "2 hodiny",
    "uk": "2 години"
  },
  "Другая длительность": {
    "en": "Custom duration",
    "cs": "Jiná délka",
    "uk": "Інша тривалість"
  },
  "Минуты, с шагом 30": {
    "en": "Minutes, in steps of 30",
    "cs": "Minuty, po 30",
    "uk": "Хвилини, з кроком 30"
  },
  "Какие дни рассматриваем": {
    "en": "Which days work",
    "cs": "Které dny připadají v úvahu",
    "uk": "Які дні розглядаємо"
  },
  "Каждую обычную неделю, по Праге.": {
    "en": "Every typical week, in Prague time.",
    "cs": "Každý běžný týden, podle Prahy.",
    "uk": "Кожного звичайного тижня, за Прагою."
  },
  "Не раньше": {
    "en": "No earlier than",
    "cs": "Nejdříve od",
    "uk": "Не раніше"
  },
  "Заканчиваем до": {
    "en": "Finish by",
    "cs": "Skončit do",
    "uk": "Завершуємо до"
  },
  "Разные диапазоны по дням": {
    "en": "Different times for each day",
    "cs": "Různé časy podle dnů",
    "uk": "Різні проміжки за днями"
  },
  "Оставьте пустым для дней и времени выше": {
    "en": "Leave blank to use the days and times above",
    "cs": "Prázdné pole použije dny a časy výše",
    "uk": "Залиште порожнім для днів і часу вище"
  },
  "вт 18:00-21:00; ср 19:00-22:00": {
    "en": "tue 18:00-21:00; wed 19:00-22:00",
    "cs": "út 18:00-21:00; st 19:00-22:00",
    "uk": "вт 18:00-21:00; ср 19:00-22:00"
  },
  "Срок ответа": {
    "en": "Response deadline",
    "cs": "Termín odpovědi",
    "uk": "Термін відповіді"
  },
  "Дата и время по Праге": {
    "en": "Date and time in Prague",
    "cs": "Datum a čas v Praze",
    "uk": "Дата й час за Прагою"
  },
  "Дата": {
    "en": "Date",
    "cs": "Datum",
    "uk": "Дата"
  },
  "Перед сроком бот один раз напомнит тем, кто не ответил. Сбор закроется автоматически.": {
    "en": "The bot reminds people who haven't answered once before the deadline. Collection closes automatically.",
    "cs": "Bot před termínem jednou připomene odpověď těm, kdo neodpověděli. Sběr se uzavře automaticky.",
    "uk": "Перед терміном бот один раз нагадає тим, хто не відповів. Збір закриється автоматично."
  },
  "Новый подбор заменит незавершённый подбор этой встречи. Старые ответы сохранятся. Другие встречи группы продолжатся без изменений.": {
    "en": "This replaces this meeting's unfinished poll. Old answers are kept. Other meetings continue unchanged.",
    "cs": "Tím nahradíte nedokončený výběr tohoto setkání. Staré odpovědi zůstanou. Ostatní setkání se nezmění.",
    "uk": "Це замінить незавершене опитування цієї зустрічі. Старі відповіді збережуться. Інші зустрічі триватимуть без змін."
  },
  "Публикуем…": {
    "en": "Publishing…",
    "cs": "Zveřejňujeme…",
    "uk": "Публікуємо…"
  },
  "Опубликовать в группе": {
    "en": "Publish to group",
    "cs": "Zveřejnit ve skupině",
    "uk": "Опублікувати в групі"
  },
  "Ответы участников": {
    "en": "Participant answers",
    "cs": "Odpovědi účastníků",
    "uk": "Відповіді учасників"
  },
  "Подобрать заново": {
    "en": "Start again",
    "cs": "Vybrat znovu",
    "uk": "Обрати знову"
  },
  "Ответ ещё не сохранён": {
    "en": "Answer not saved yet",
    "cs": "Odpověď ještě není uložená",
    "uk": "Відповідь ще не збережено"
  },
  "Ни один вариант не подходит": {
    "en": "None of the times work",
    "cs": "Žádný termín nevyhovuje",
    "uk": "Жоден варіант не підходить"
  },
  "интервал": {
    "en": "time window",
    "cs": "interval",
    "uk": "проміжок"
  },
  "интервала": {
    "en": "time windows",
    "cs": "intervaly",
    "uk": "проміжки"
  },
  "интервалов": {
    "en": "time windows",
    "cs": "intervalů",
    "uk": "проміжків"
  },
  "Показать время": {
    "en": "Show times",
    "cs": "Zobrazit časy",
    "uk": "Показати час"
  },
  "Ждём": {
    "en": "Waiting",
    "cs": "Čekáme",
    "uk": "Чекаємо"
  },
  "Сохранено": {
    "en": "Saved",
    "cs": "Uloženo",
    "uk": "Збережено"
  },
  "Посмотреть результаты": {
    "en": "View results",
    "cs": "Zobrazit výsledky",
    "uk": "Переглянути результати"
  },
  "Ни один вариант": {
    "en": "No times work",
    "cs": "Žádný vhodný čas",
    "uk": "Жоден варіант"
  },
  "вариант выбран": {
    "en": "option selected",
    "cs": "možnost vybrána",
    "uk": "варіант обрано"
  },
  "варианта выбрано": {
    "en": "options selected",
    "cs": "možnosti vybrány",
    "uk": "варіанти обрано"
  },
  "вариантов выбрано": {
    "en": "options selected",
    "cs": "možností vybráno",
    "uk": "варіантів обрано"
  },
  "Ответ сохранён · можно изменить": {
    "en": "Answer saved · you can edit it",
    "cs": "Odpověď uložena · lze ji změnit",
    "uk": "Відповідь збережено · можна змінити"
  },
  "Изменения ещё не сохранены": {
    "en": "Unsaved changes",
    "cs": "Neuložené změny",
    "uk": "Зміни ще не збережено"
  },
  "Отметьте всё подходящее время": {
    "en": "Select all times that work",
    "cs": "Označte všechen vhodný čas",
    "uk": "Позначте весь зручний час"
  },
  "Сохраняем…": {
    "en": "Saving…",
    "cs": "Ukládáme…",
    "uk": "Зберігаємо…"
  },
  "Сохранить": {
    "en": "Save",
    "cs": "Uložit",
    "uk": "Зберегти"
  },
  "Предпросмотр · вымышленные группы и участники · ответы не отправляются": {
    "en": "Preview · fictional groups and people · no answers are sent",
    "cs": "Ukázka · smyšlené skupiny a lidé · odpovědi se neodesílají",
    "uk": "Демо · вигадані групи й учасники · відповіді не надсилаються"
  },
  "Доступность": {
    "en": "Availability",
    "cs": "Dostupnost",
    "uk": "Доступність"
  },
  "Пересечения": {
    "en": "Matches",
    "cs": "Shody",
    "uk": "Збіги"
  },
  "Голосование": {
    "en": "Voting",
    "cs": "Hlasování",
    "uk": "Голосування"
  },
  "Итог": {
    "en": "Final plan",
    "cs": "Výsledek",
    "uk": "Підсумок"
  },
  "Ваш ответ пока не ожидается": {
    "en": "Your answer isn't expected yet",
    "cs": "Vaše odpověď se zatím neočekává",
    "uk": "Ваша відповідь поки не очікується"
  },
  "Попросите организатора включить вас в участников встречи. Если вы только открыли ссылку группы, сначала присоединитесь к ней в приложении.": {
    "en": "Ask the organizer to add you to the meeting. If you opened a group link, join the group in the app first.",
    "cs": "Požádejte organizátora o přidání do setkání. Pokud jste otevřeli odkaz skupiny, nejprve se k ní připojte v aplikaci.",
    "uk": "Попросіть організатора додати вас до зустрічі. Якщо відкрили посилання групи, спершу приєднайтеся до неї в застосунку."
  },
  "Я участник этой группы": {
    "en": "I'm a member of this group",
    "cs": "Jsem členem této skupiny",
    "uk": "Я учасник цієї групи"
  },
  "К встречам группы": {
    "en": "Back to group meetings",
    "cs": "Na setkání skupiny",
    "uk": "До зустрічей групи"
  },
  "Голосовать за частичные варианты?": {
    "en": "Vote on partial matches?",
    "cs": "Hlasovat o částečných shodách?",
    "uk": "Голосувати за часткові збіги?"
  },
  "Есть участники, которым эти интервалы не подходят, или люди без ответа. Вы явно разрешаете финальное голосование с этим ограничением. Можно расширить диапазоны и собрать доступность заново.": {
    "en": "Some people can't make these times or haven't answered. You're explicitly allowing a final vote with that limitation. You can also widen the time range and collect answers again.",
    "cs": "Některým účastníkům časy nevyhovují nebo neodpověděli. Výslovně povolujete finální hlasování s tímto omezením. Můžete také rozšířit rozmezí a sbírat odpovědi znovu.",
    "uk": "Деяким учасникам ці проміжки не підходять або вони не відповіли. Ви явно дозволяєте фінальне голосування з цим обмеженням. Можна розширити проміжки та зібрати відповіді знову."
  },
  "Да, начать": {
    "en": "Yes, start voting",
    "cs": "Ano, spustit",
    "uk": "Так, почати"
  },
  "Финальное голосование запущено": {
    "en": "Final voting started",
    "cs": "Finální hlasování spuštěno",
    "uk": "Фінальне голосування розпочато"
  },
  "Демо: приглашения не отправляются": {
    "en": "Demo: invitations aren't sent",
    "cs": "Demo: pozvánky se neodesílají",
    "uk": "Демо: запрошення не надсилаються"
  },
  "Выберем удобное время для нашей еженедельной встречи. Откройте приложение, чтобы организатор мог добавить вас.": {
    "en": "Let's find a time for our weekly meeting. Open the app so the organizer can add you.",
    "cs": "Najděme čas pro naše týdenní setkání. Otevřete aplikaci, aby vás organizátor mohl přidat.",
    "uk": "Оберімо зручний час для нашої щотижневої зустрічі. Відкрийте застосунок, щоб організатор міг вас додати."
  },
  "Выберите хотя бы один день.": {
    "en": "Choose at least one day.",
    "cs": "Vyberte alespoň jeden den.",
    "uk": "Оберіть хоча б один день."
  },
  "Добавьте хотя бы одного участника.": {
    "en": "Add at least one participant.",
    "cs": "Přidejte alespoň jednoho účastníka.",
    "uk": "Додайте хоча б одного учасника."
  },
  "Подбор опубликован": {
    "en": "Poll published",
    "cs": "Výběr zveřejněn",
    "uk": "Опитування опубліковано"
  },
  "Демо: бот в реальные группы не добавляется": {
    "en": "Demo: the bot isn't added to real groups",
    "cs": "Demo: bot se nepřidává do skutečných skupin",
    "uk": "Демо: бот не додається до справжніх груп"
  },
  "Вы появились в списке участников группы": {
    "en": "You're now on the group's participant list",
    "cs": "Jste v seznamu účastníků skupiny",
    "uk": "Ви з’явилися у списку учасників групи"
  },
  "Интервалы скопированы на остальные дни": {
    "en": "Time windows copied to the other days",
    "cs": "Intervaly zkopírovány na ostatní dny",
    "uk": "Проміжки скопійовано на інші дні"
  },
  "Ответ сохранён. Спасибо!": {
    "en": "Answer saved. Thank you!",
    "cs": "Odpověď uložena. Děkujeme!",
    "uk": "Відповідь збережено. Дякуємо!"
  },
  "Закрыть сбор доступности?": {
    "en": "Close availability collection?",
    "cs": "Uzavřít sběr dostupnosti?",
    "uk": "Закрити збір доступності?"
  },
  "Сохраним текущие ответы. После закрытия их нельзя будет изменить. Затем вы выберете варианты для финального голосования.": {
    "en": "Current answers will be saved and can no longer be changed. You'll then choose options for the final vote.",
    "cs": "Současné odpovědi se uloží a nepůjde je změnit. Poté vyberete možnosti pro finální hlasování.",
    "uk": "Поточні відповіді збережуться, їх уже не можна буде змінити. Потім ви оберете варіанти для фінального голосування."
  },
  "Сбор закрыт. Выберите варианты голосования": {
    "en": "Collection closed. Choose voting options",
    "cs": "Sběr uzavřen. Vyberte možnosti hlasování",
    "uk": "Збір закрито. Оберіть варіанти голосування"
  },
  "Ваш голос сохранён": {
    "en": "Your vote is saved",
    "cs": "Váš hlas je uložen",
    "uk": "Ваш голос збережено"
  },
  "Зафиксировать наше время?": {
    "en": "Make this our regular time?",
    "cs": "Potvrdit náš pravidelný čas?",
    "uk": "Зафіксувати наш час?"
  },
  "по Праге.": {
    "en": "Prague time.",
    "cs": "pražského času.",
    "uk": "за Прагою."
  },
  " Проголосовали не все — вы явно завершаете голосование досрочно.": {
    "en": " Not everyone has voted. You're explicitly ending the vote early.",
    "cs": " Ne všichni hlasovali. Výslovně ukončujete hlasování předčasně.",
    "uk": " Проголосували не всі — ви явно завершуєте голосування достроково."
  },
  "Итог будет опубликован в группе.": {
    "en": "The result will be posted to the group.",
    "cs": "Výsledek bude zveřejněn ve skupině.",
    "uk": "Підсумок буде опубліковано в групі."
  },
  "Расписание подтверждено": {
    "en": "Schedule confirmed",
    "cs": "Rozvrh potvrzen",
    "uk": "Розклад підтверджено"
  },
  "Время быть вместе.": {
    "en": "Time for each other.",
    "cs": "Čas být spolu.",
    "uk": "Час бути разом."
  },
  "Откройте приложение в Telegram, отметьте удобное время и найдите ваш общий день недели.": {
    "en": "Open the app in Telegram, share when you're free and find your shared day of the week.",
    "cs": "Otevřete aplikaci v Telegramu, označte volný čas a najděte společný den v týdnu.",
    "uk": "Відкрийте застосунок у Telegram, позначте зручний час і знайдіть спільний день тижня."
  },
  "Открыть в Telegram": {
    "en": "Open in Telegram",
    "cs": "Otevřít v Telegramu",
    "uk": "Відкрити в Telegram"
  },
  "Посмотреть пример интерфейса": {
    "en": "Explore the demo",
    "cs": "Prohlédnout ukázku",
    "uk": "Переглянути приклад"
  },
  "Не удалось загрузить приложение. Откройте его заново.": {
    "en": "Couldn't load the app. Please reopen it.",
    "cs": "Aplikaci se nepodařilo načíst. Otevřete ji znovu.",
    "uk": "Не вдалося завантажити застосунок. Відкрийте його знову."
  },
  "Собираем удобное время…": {
    "en": "Finding time together…",
    "cs": "Hledáme společný čas…",
    "uk": "Знаходимо зручний час…"
  },
  "Язык": {
    "en": "Language",
    "cs": "Jazyk",
    "uk": "Мова"
  },
  "Язык Telegram": {
    "en": "Telegram language",
    "cs": "Jazyk Telegramu",
    "uk": "Мова Telegram"
  },
  "Telegram не отвечает. Попробуйте ещё раз.": {
    "en": "Telegram isn't responding. Please try again.",
    "cs": "Telegram neodpovídá. Zkuste to znovu.",
    "uk": "Telegram не відповідає. Спробуйте ще раз."
  },
  "Проверьте данные и обновите состояние встречи.": {
    "en": "Check your entries and refresh the meeting.",
    "cs": "Zkontrolujte údaje a obnovte setkání.",
    "uk": "Перевірте дані та оновіть стан зустрічі."
  },
  "Нет соединения. Ваш выбор сохранён на экране. Попробуйте ещё раз.": {
    "en": "No connection. Your selection is still on screen. Try again.",
    "cs": "Bez připojení. Váš výběr zůstává na obrazovce. Zkuste to znovu.",
    "uk": "Немає з’єднання. Ваш вибір залишається на екрані. Спробуйте ще раз."
  },
  "Длительность: от 30 до 480 минут с шагом 30 минут.": {
    "en": "Duration must be 30–480 minutes, in steps of 30.",
    "cs": "Délka musí být 30–480 minut, po 30 minutách.",
    "uk": "Тривалість: 30–480 хвилин із кроком 30."
  },
  "Нужен хотя бы один вариант встречи.": {
    "en": "Add at least one meeting time.",
    "cs": "Přidejte alespoň jeden termín.",
    "uk": "Додайте хоча б один час зустрічі."
  },
  "Этот срок попадает на перевод часов. Выберите однозначное время, например 12:00.": {
    "en": "The deadline falls during a clock change. Choose an unambiguous time, such as 12:00.",
    "cs": "Termín spadá do změny času. Vyberte jednoznačný čas, například 12:00.",
    "uk": "Термін припадає на переведення годинників. Оберіть однозначний час, наприклад 12:00."
  },
  "Срок ответа должен быть в будущем.": {
    "en": "The response deadline must be in the future.",
    "cs": "Termín odpovědi musí být v budoucnosti.",
    "uk": "Термін відповіді має бути в майбутньому."
  },
  "Формат диапазонов: вт 18:00-21:00; ср 18:00-21:00.": {
    "en": "Use time windows like: tue 18:00-21:00; wed 18:00-21:00.",
    "cs": "Zadejte intervaly takto: út 18:00-21:00; st 18:00-21:00.",
    "uk": "Формат проміжків: вт 18:00-21:00; ср 18:00-21:00."
  },
  "Время задаётся с шагом 30 минут, от 00:00 до 24:00.": {
    "en": "Use 30-minute steps, from 00:00 to 24:00.",
    "cs": "Použijte kroky po 30 minutách, od 00:00 do 24:00.",
    "uk": "Час задається з кроком 30 хвилин, від 00:00 до 24:00."
  },
  "Встреча должна помещаться в диапазон одного дня; конец может быть 24:00.": {
    "en": "The whole meeting must fit within one day. The end can be 24:00.",
    "cs": "Celé setkání se musí vejít do jednoho dne. Konec může být 24:00.",
    "uk": "Зустріч має вміститися в один день. Кінець може бути о 24:00."
  },
  "Дни недели: пн, вт, ср, чт, пт, сб, вс.": {
    "en": "Weekdays: mon, tue, wed, thu, fri, sat, sun.",
    "cs": "Dny: po, út, st, čt, pá, so, ne.",
    "uk": "Дні: пн, вт, ср, чт, пт, сб, нд."
  },
  "Сбор уже закрыт. Изменить доступность нельзя.": {
    "en": "Collection is closed. Availability can no longer be changed.",
    "cs": "Sběr je uzavřen. Dostupnost už nelze měnit.",
    "uk": "Збір закрито. Змінити доступність уже не можна."
  },
  "Выберите интервалы или явно нажмите «Ни один вариант не подходит».": {
    "en": "Choose time windows or explicitly select that none work.",
    "cs": "Vyberte intervaly nebo výslovně označte, že žádný nevyhovuje.",
    "uk": "Оберіть проміжки або явно зазначте, що жоден не підходить."
  },
  "Сбор уже закрыт.": {
    "en": "Collection is already closed.",
    "cs": "Sběr je už uzavřen.",
    "uk": "Збір уже закрито."
  },
  "Это голосование закрыто или вариант не включён в него.": {
    "en": "Voting is closed or this option is no longer available.",
    "cs": "Hlasování je uzavřené nebo tato možnost není dostupná.",
    "uk": "Голосування закрито або цього варіанта в ньому немає."
  },
  "Нужно открытое голосование хотя бы с одним голосом.": {
    "en": "Voting must be open with at least one vote.",
    "cs": "Hlasování musí být otevřené a mít alespoň jeden hlas.",
    "uk": "Потрібне відкрите голосування хоча б з одним голосом."
  },
  "Голоса изменились. Откройте /confirm и выберите одного из текущих лидеров.": {
    "en": "Votes changed. Refresh results and choose one of the current leaders.",
    "cs": "Hlasy se změnily. Obnovte výsledky a vyberte jednu z vedoucích možností.",
    "uk": "Голоси змінилися. Оновіть результати та оберіть одного з поточних лідерів."
  },
  "Эта команда доступна только организатору.": {
    "en": "Only the organizer can do this.",
    "cs": "Tuto akci může provést jen organizátor.",
    "uk": "Ця дія доступна лише організатору."
  },
  "Вы не включены в список ожидаемых участников этого подбора.": {
    "en": "You aren't on this meeting's participant list.",
    "cs": "Nejste v seznamu účastníků tohoto setkání.",
    "uk": "Вас немає у списку учасників цієї зустрічі."
  },
  "Укажите от 1 до 30 участников.": {
    "en": "Choose 1–30 participants.",
    "cs": "Vyberte 1–30 účastníků.",
    "uk": "Оберіть 1–30 учасників."
  },
  "Выберите от 1 до 30 участников.": {
    "en": "Choose 1–30 participants.",
    "cs": "Vyberte 1–30 účastníků.",
    "uk": "Оберіть 1–30 учасників."
  },
  "Укажите название встречи от 1 до 80 символов.": {
    "en": "Use a meeting name of 1–80 characters.",
    "cs": "Název setkání musí mít 1–80 znaků.",
    "uk": "Назва зустрічі має містити 1–80 символів."
  },
  "Проверьте диапазоны времени.": {
    "en": "Check the time windows.",
    "cs": "Zkontrolujte časové intervaly.",
    "uk": "Перевірте часові проміжки."
  },
  "Укажите дату и время окончания сбора.": {
    "en": "Enter the date and time collection should close.",
    "cs": "Zadejte datum a čas ukončení sběru.",
    "uk": "Укажіть дату й час завершення збору."
  },
  "Выберите от одного до трёх предложенных вариантов.": {
    "en": "Choose one to three of the suggested options.",
    "cs": "Vyberte jednu až tři navržené možnosti.",
    "uk": "Оберіть від одного до трьох запропонованих варіантів."
  },
  "Сначала закройте сбор доступности.": {
    "en": "Close availability collection first.",
    "cs": "Nejprve uzavřete sběr dostupnosti.",
    "uk": "Спершу закрийте збір доступності."
  },
  "Присоединиться могут только участники этой Telegram-группы.": {
    "en": "Only members of this Telegram group can join.",
    "cs": "Připojit se mohou jen členové této telegramové skupiny.",
    "uk": "Приєднатися можуть лише учасники цієї Telegram-групи."
  },
  "Не удалось проверить создание. Обновите форму.": {
    "en": "Couldn't verify this creation request. Reopen the form.",
    "cs": "Požadavek na vytvoření nelze ověřit. Otevřete formulář znovu.",
    "uk": "Не вдалося перевірити запит створення. Відкрийте форму знову."
  }
};
  if (typeof module !== 'undefined') module.exports = messages;
  else root.MeetingMessages = messages;
})(typeof window === 'undefined' ? globalThis : window);
