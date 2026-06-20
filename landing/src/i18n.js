// Полные переводы лендинга RU / EN
const translations = {
  ru: {
    nav: {
      manifest: "манифест",
      how: "инструмент",
      map: "карта",
      reading: "о методе",
      pricing: "тарифы",
      faq: "faq",
      cta: "открыть →",
    },
    hero: {
      kicker: "opus minor · 2026",
      title1: "Твоё внимание уходит куда угодно,",
      title2: "кроме тебя.",
      subtitle:
        "innerCore — место, где оно возвращается. Дневник сновидений с юнгианским анализом.",
      cta: "Открыть приложение",
      scroll: "↓ читать манифест",
      badges: ["архетипы", "символы", "векторная карта", "e2e-шифрование"],
      caption: "quod superius sicut quod inferius — что вверху, то и внизу",
    },
    manifest: {
      kicker: "— i. manifesto",
      title: "Кому ты на самом деле принадлежишь?",
      blocks: [
        {
          kicker: "— внимание",
          paragraphs: [
            "Интернет забирает внимание. Работа забирает внимание. Учёба забирает внимание. Новости, реклама, чаты, чужие мнения, чужие ожидания — каждый требует свою долю. И каждый получает.",
            "А ты? Сколько внимания доходит до тебя самого? Час в день? Десять минут? Совсем ничего?",
            { italic: "Это не философский вопрос. Это вопрос о том, кто ты есть." },
            "Когда внимание уходит вовне — внутри становится пусто. И тогда любая внешняя проблема — на работе, в семье, со здоровьем — встречает не тебя, а пустое место.",
          ],
        },
        {
          kicker: "— конфликт",
          title: "Откуда берутся конфликты",
          paragraphs: [
            "Большинство конфликтов между людьми — не про деньги, не про власть, не про обиды. Они про то, что внутри у одного человека пусто, и он требует, чтобы другой это заполнил. А другой тоже пустой. И они сталкиваются.",
            "Невозможно любить кого-то, не любя себя. То, что выглядит как любовь к другому без любви к себе — это переадресация: попытка получить от другого то, что должно быть у тебя внутри. Поэтому первое — внимание к себе. Второе — внимание к близким. Всё остальное идёт из этого порядка.",
          ],
        },
        {
          kicker: "— тело",
          title: "Психика — это и есть здоровье",
          paragraphs: [
            "Психика — это нервная система. Нервная система регулирует органы, гормоны, эмоции, отношения. Когда психика не услышана — болеют органы. Когда психика не понята — рушатся отношения. Когда внутренний конфликт не разобран — он выходит наружу симптомом: бессонницей, гипертонией, скандалом, увольнением, разводом.",
            "Психология — не «мягкая» наука рядом с серьёзной медициной. Психология — корень медицины. Лечение симптома без работы с причиной — это бесконечная борьба со следствиями.",
          ],
        },
        {
          kicker: "— практика",
          title: "Куда смотреть",
          paragraphs: [
            "Внимание возвращается через простые практики. Одна из самых прямых — работа со снами. Днём психика защищена ролями, словами и привычками. Ночью защит нет. Снится то, что есть.",
            { italic: "innerCore — инструмент для этой работы." },
          ],
        },
      ],
    },
    tool: {
      kicker: "— ii. instrumentum",
      titleA: "Что делает",
      titleB: "innerCore",
      subkicker: "mercurius · sulphur · sal",
      cards: [
        {
          glyph: "☿",
          label: "Mercurius",
          title: "Записывает",
          intro: "Сразу после пробуждения — текстом или голосом.",
          body: "Сон забывается в первые минуты, поэтому запись делается короткой и быстрой. Пара минут — и материал сохранён.",
        },
        {
          glyph: "🜍",
          label: "Sulphur",
          title: "Разбирает",
          intro: "Каждый сон проходит через юнгианский разбор.",
          body: "Какие архетипы появились, какие мотивы повторяются из прошлых снов, какой эмоциональный тон, какие фигуры активны. Не магия — рабочая модель психики.",
        },
        {
          glyph: "🜔",
          label: "Sal",
          title: "Складывает карту",
          intro: "Один сон ничего не значит. Сто снов — складываются в карту.",
          body: "Какие архетипы возвращаются, какие сюжеты повторяются, какие темы ты годами обходишь, а они всё равно приходят. Эта карта — твоя.",
        },
      ],
    },
    map: {
      kicker: "— iii. mappa somniorum",
      title: "Карта",
      p1: "Каждый сон превращается в точку. Похожие сны притягиваются — образуют кластеры. Кластеры собираются в созвездия архетипов. Чем дольше пишешь — тем точнее карта.",
      p2: "Это работает математически: каждый сон превращается в вектор смыслов. Близкие смыслы — близкие точки в пространстве. Юнгианская модель ложится на векторную базу данных как ключ в замок.",
    },
    sigillum: {
      kicker: "— iv. sigillum",
      titleA: "Сны — самое личное,",
      titleB: "что может быть.",
      p1: "innerCore шифрует содержимое снов на твоём устройстве до того, как они уйдут на сервер. На сервере хранится только шифротекст. Ни Google, ни сотрудники innerCore, ни хостинг, ни кто-либо ещё не может прочитать, что тебе снилось.",
      p2: "Ключ от твоего архива есть только у тебя. Это не маркетинг — это архитектура.",
    },
    reading: {
      kicker: "— v. lectio",
      title: "О методе",
      lead: "Несколько коротких текстов о том, что стоит за приложением. Юнг, архетипы, практика дневника снов.",
      articles: [
        {
          kicker: "— чтение I",
          title: "Зачем вести дневник снов",
          paragraphs: [
            "Юнгианский подход к снам отличается от популярных сонников и таблиц «что значит, если приснилась вода». В аналитической психологии Карла Густава Юнга сны рассматриваются как прямые сообщения от бессознательного — той части психики, которую дневное сознание не контролирует и редко слышит.",
            "Каждый сон — индивидуальное послание конкретному человеку. У одного человека вода может быть символом перемен, у другого — забытым страхом из детства, у третьего — образом матери. Универсальных толкований нет. Есть устойчивые структуры — архетипы — которые проявляются у каждого человека по-своему.",
            "Дневник снов — это первый и обязательный инструмент любой серьёзной работы со сновидениями.",
          ],
        },
        {
          kicker: "— чтение II",
          title: "Что такое архетипы Юнга",
          paragraphs: [
            "Архетипы — это базовые структуры психики, общие для всех людей. Юнг выделил их в результате анализа тысяч снов своих пациентов и сопоставления с мифами разных культур, религиозными традициями, герметическими текстами, фольклором.",
            { kind: "archetypes-ru" },
            "Эти фигуры появляются в снах не случайно — они отражают активную работу психики, обращённую к самому сновидцу. Юнг описал архетипы в работах «Архетипы и коллективное бессознательное», «Психология и алхимия», «Человек и его символы».",
          ],
        },
        {
          kicker: "— чтение III",
          title: "Как работа со снами влияет на жизнь",
          paragraphs: [
            "Юнгианский анализ — это не предсказание будущего и не объяснение прошлого. Это процесс индивидуации — становления собой, постепенного интегрирования отщеплённых частей психики.",
            "Через регулярную работу со снами человек начинает видеть свои повторяющиеся паттерны: какие фигуры возвращаются в сюжетах, какие конфликты живут внутри, какие части психики проецируются на других людей и создают конфликты в отношениях, какие темы игнорируются и поэтому проявляются через симптомы тела или болезни.",
            "Это медленная, но фундаментальная работа. Юнгианские терапевты работают с пациентами годами. Современные цифровые инструменты — приложения для дневников снов, разборы, карты сновидений — не заменяют терапию, но делают её первый шаг доступным каждому, кто готов слушать себя.",
          ],
        },
        {
          kicker: "— чтение IV",
          title: "Дневник снов как ежедневная практика",
          paragraphs: [
            "Самое сложное в работе со снами — их запомнить. Сон забывается в первые минуты после пробуждения, и без записи материал теряется. Регулярный дневник сновидений — единственный способ сохранить материал для анализа.",
            "innerCore делает запись простой: голосом сразу после пробуждения, текстом — когда удобнее. Из накопленных снов складывается индивидуальная карта повторяющихся образов и архетипов.",
            "Со временем становится видно: ты обходишь стороной одну и ту же тему годами, а она всё равно приходит к тебе во сне. Это и есть точка, в которой начинается настоящая работа над собой.",
          ],
        },
      ],
    },
    faq: {
      kicker: "— vi. quaestiones",
      title: "Частые вопросы",
      items: [
        {
          q: "Это работает с моделью. Это не подмена психотерапевта?",
          a: [
            "Нет. Разбор от модели — не психотерапия. Терапевт работает с человеком в комнате, видит реакции, держит контейнер для эмоций.",
            "innerCore — инструмент для записи и первичного разбора. Если возникают трудные темы — иди к специалисту. innerCore хорошо работает рядом с терапией: между сессиями есть, что приносить.",
          ],
        },
        {
          q: "Я не разбираюсь в Юнге. Это для меня?",
          a: [
            "Да. Знать теорию заранее не нужно. Каждый встреченный архетип объясняется простыми словами в контексте конкретного сна.",
            "Юнгианский язык приходит сам через практику. Через месяц записей ты уже начнёшь узнавать свою Тень в лицо.",
          ],
        },
        {
          q: "А если я не вижу снов или не помню их?",
          a: [
            "Сны видят все люди — каждую ночь по 4–6 эпизодов. Не запоминается — другое. Это тренируется.",
            { kind: "memory-tips-ru" },
          ],
        },
        {
          q: "Сколько нужно снов, чтобы появилась карта?",
          a: [
            "Десять снов — уже видна структура. Пятьдесят — отчётливые кластеры. Сто и больше — устойчивые архетипы и темы.",
            "Это не быстрый продукт. Это медленная практика. И именно медленность здесь — преимущество.",
          ],
        },
        {
          q: "Как именно с приватностью?",
          a: [
            "Содержимое снов шифруется на твоём устройстве до отправки. На сервере — только шифротекст. Ключ хранится у тебя. Ни сотрудники innerCore, ни хостинг-провайдер, ни внешние сервисы не имеют доступа к плейнтексту твоих снов.",
          ],
        },
        {
          q: "Можно работать без интернета?",
          a: [
            "Запись — да, в офлайн-режиме. Анализ требует подключения, потому что разбор идёт через языковую модель. Карта обновляется при следующем выходе в сеть.",
          ],
        },
      ],
    },
    final: {
      titleA: "Сегодня ночью",
      titleB: "что-то приснится.",
      cta: "Открыть приложение",
      tgLead: "Канал автора",
      tgTail: "— про снотолкование, AI и киберпанк.",
    },
    footer: {
      contact: "контакт",
      privacy: "политика приватности",
      telegram: "telegram",
    },
  },

  en: {
    nav: {
      manifest: "manifesto",
      how: "tool",
      map: "map",
      reading: "method",
      pricing: "pricing",
      faq: "faq",
      cta: "open →",
    },
    hero: {
      kicker: "opus minor · 2026",
      title1: "Your attention goes anywhere,",
      title2: "except to you.",
      subtitle:
        "innerCore — the place where it returns. A dream journal with Jungian analysis.",
      cta: "Open the app",
      scroll: "↓ read manifesto",
      badges: ["archetypes", "symbols", "vector map", "e2e-encryption"],
      caption: "quod superius sicut quod inferius — as above, so below",
    },
    manifest: {
      kicker: "— i. manifesto",
      title: "To whom do you really belong?",
      blocks: [
        {
          kicker: "— attention",
          paragraphs: [
            "The internet takes attention. Work takes attention. Study takes attention. News, ads, chats, other people's opinions, other people's expectations — each demands its share. And each one gets it.",
            "And you? How much attention reaches you? An hour a day? Ten minutes? None at all?",
            { italic: "This is not a philosophical question. This is a question of who you are." },
            "When attention goes outward — inside becomes empty. And then any external problem — at work, in the family, with health — meets not you, but an empty place.",
          ],
        },
        {
          kicker: "— conflict",
          title: "Where conflicts come from",
          paragraphs: [
            "Most conflicts between people are not about money, not about power, not about grievances. They are about one person being empty inside and demanding that another fill that emptiness. And the other is just as empty. And so they collide.",
            "It is impossible to love someone without loving yourself. What looks like love for another without love for oneself is redirection: an attempt to receive from another what should be inside you. So first — attention to yourself. Second — attention to those close to you. Everything else follows from that order.",
          ],
        },
        {
          kicker: "— body",
          title: "The psyche is health itself",
          paragraphs: [
            "The psyche is the nervous system. The nervous system regulates organs, hormones, emotions, relationships. When the psyche is unheard — organs become ill. When the psyche is misunderstood — relationships fall apart. When inner conflict is not worked through — it comes out as a symptom: insomnia, hypertension, a quarrel, a dismissal, a divorce.",
            "Psychology is not a “soft” science alongside serious medicine. Psychology is the root of medicine. Treating a symptom without working with its cause is an endless fight with consequences.",
          ],
        },
        {
          kicker: "— practice",
          title: "Where to look",
          paragraphs: [
            "Attention returns through simple practices. One of the most direct is working with dreams. By day, the psyche is protected by roles, words, and habits. At night there are no defences. You dream what is.",
            { italic: "innerCore is the instrument for this work." },
          ],
        },
      ],
    },
    tool: {
      kicker: "— ii. instrumentum",
      titleA: "What innerCore",
      titleB: "does",
      subkicker: "mercurius · sulphur · sal",
      cards: [
        {
          glyph: "☿",
          label: "Mercurius",
          title: "Records",
          intro: "Right after waking — by text or by voice.",
          body: "A dream is forgotten within the first few minutes, so capture is short and fast. A couple of minutes — and the material is saved.",
        },
        {
          glyph: "🜍",
          label: "Sulphur",
          title: "Analyses",
          intro: "Every dream passes through a Jungian reading.",
          body: "Which archetypes appeared, which motifs recur from previous dreams, what the emotional tone is, which figures are active. Not magic — a working model of the psyche.",
        },
        {
          glyph: "🜔",
          label: "Sal",
          title: "Builds the map",
          intro: "One dream means nothing. A hundred dreams — form a map.",
          body: "Which archetypes return, which storylines repeat, which themes you avoid for years while they still keep coming. This map is yours.",
        },
      ],
    },
    map: {
      kicker: "— iii. mappa somniorum",
      title: "The map",
      p1: "Each dream becomes a point. Similar dreams attract each other — they form clusters. Clusters gather into constellations of archetypes. The longer you write — the more precise the map.",
      p2: "It works mathematically: each dream becomes a vector of meanings. Close meanings — close points in space. The Jungian model fits a vector database like a key in a lock.",
    },
    sigillum: {
      kicker: "— iv. sigillum",
      titleA: "Dreams are the most personal",
      titleB: "thing that can be.",
      p1: "innerCore encrypts the contents of dreams on your device before they leave it. Only the ciphertext is stored on the server. Neither Google, nor innerCore staff, nor the hosting provider, nor anyone else can read what you dreamed.",
      p2: "Only you have the key to your archive. This is not marketing — this is architecture.",
    },
    reading: {
      kicker: "— v. lectio",
      title: "About the method",
      lead: "A few short texts on what stands behind the app. Jung, archetypes, the practice of a dream journal.",
      articles: [
        {
          kicker: "— reading I",
          title: "Why keep a dream journal",
          paragraphs: [
            "The Jungian approach to dreams differs from popular dream dictionaries and “what it means if you dreamed of water” tables. In Carl Gustav Jung's analytical psychology, dreams are treated as direct messages from the unconscious — that part of the psyche that the daytime mind does not control and rarely hears.",
            "Each dream is an individual message to a specific person. For one person, water may be a symbol of change; for another — a forgotten childhood fear; for a third — an image of the mother. There are no universal interpretations. There are stable structures — archetypes — that manifest in each person in their own way.",
            "A dream journal is the first and necessary instrument of any serious work with dreams.",
          ],
        },
        {
          kicker: "— reading II",
          title: "What Jung's archetypes are",
          paragraphs: [
            "Archetypes are basic structures of the psyche, common to all people. Jung identified them through the analysis of thousands of his patients' dreams and through comparison with myths of various cultures, religious traditions, hermetic texts, and folklore.",
            { kind: "archetypes-en" },
            "These figures do not appear in dreams by accident — they reflect the active work of the psyche addressed to the dreamer themselves. Jung described archetypes in “Archetypes and the Collective Unconscious”, “Psychology and Alchemy”, “Man and His Symbols”.",
          ],
        },
        {
          kicker: "— reading III",
          title: "How dream work affects life",
          paragraphs: [
            "Jungian analysis is not prediction of the future and not explanation of the past. It is the process of individuation — becoming yourself, gradually integrating split-off parts of the psyche.",
            "Through regular work with dreams a person begins to see their recurring patterns: which figures keep returning in the storylines, which conflicts live inside, which parts of the psyche are projected onto others and create conflicts in relationships, which themes are ignored and therefore appear as bodily symptoms or illness.",
            "This is slow but fundamental work. Jungian therapists work with patients for years. Modern digital tools — dream journaling apps, readings, dream maps — do not replace therapy, but make its first step accessible to anyone ready to listen to themselves.",
          ],
        },
        {
          kicker: "— reading IV",
          title: "Dream journal as a daily practice",
          paragraphs: [
            "The hardest part of dream work is remembering them. A dream is forgotten within the first few minutes after waking, and without a record the material is lost. A regular dream journal is the only way to preserve material for analysis.",
            "innerCore makes recording simple: by voice right after waking, by text — whenever it suits you better. From the accumulated dreams an individual map of recurring images and archetypes takes shape.",
            "Over time it becomes visible: you keep avoiding the same theme for years, and it still comes to you in dreams. This is the point where real work on yourself begins.",
          ],
        },
      ],
    },
    faq: {
      kicker: "— vi. quaestiones",
      title: "Frequent questions",
      items: [
        {
          q: "It works with a model. Isn't that replacing a therapist?",
          a: [
            "No. A reading from a model is not psychotherapy. A therapist works with a person in the room, sees reactions, holds a container for emotions.",
            "innerCore is a tool for recording and a first reading. If difficult themes come up — go to a specialist. innerCore works well alongside therapy: between sessions there is something to bring.",
          ],
        },
        {
          q: "I'm not familiar with Jung. Is this for me?",
          a: [
            "Yes. You don't need to know the theory beforehand. Each encountered archetype is explained in simple words in the context of the particular dream.",
            "The Jungian language comes on its own through practice. After a month of entries you'll already start recognising your Shadow by sight.",
          ],
        },
        {
          q: "What if I don't see dreams, or don't remember them?",
          a: [
            "All people see dreams — 4–6 episodes every night. What doesn't happen is remembering. That is trainable.",
            { kind: "memory-tips-en" },
          ],
        },
        {
          q: "How many dreams are needed for a map to appear?",
          a: [
            "Ten dreams — and structure is already visible. Fifty — distinct clusters. A hundred and more — stable archetypes and themes.",
            "This is not a fast product. This is a slow practice. And the slowness here is precisely the advantage.",
          ],
        },
        {
          q: "What about privacy, exactly?",
          a: [
            "Dream content is encrypted on your device before being sent. Only the ciphertext is on the server. The key is kept by you. Neither innerCore staff, nor the hosting provider, nor any external service has access to the plaintext of your dreams.",
          ],
        },
        {
          q: "Can it work offline?",
          a: [
            "Recording — yes, in offline mode. Analysis requires a connection because the reading goes through a language model. The map updates the next time you go online.",
          ],
        },
      ],
    },
    final: {
      titleA: "Tonight you will",
      titleB: "dream something.",
      cta: "Open the app",
      tgLead: "Author's channel",
      tgTail: "— on dream interpretation, AI and cyberpunk.",
    },
    footer: {
      contact: "contact",
      privacy: "privacy policy",
      telegram: "telegram",
    },
  },
};

// Special inline blocks rendered in the component (for clarity)
export const ARCHETYPES = {
  ru: ["Тень", "Анима", "Анимус", "Самость", "Персона", "Старый Мудрец", "Великая Мать", "Дитя", "Трикстер"],
  en: ["Shadow", "Anima", "Animus", "Self", "Persona", "Old Wise One", "Great Mother", "Child", "Trickster"],
};

export const ARCHETYPES_INTRO = {
  ru: "Главные архетипы:",
  en: "The main archetypes:",
};

export const MEMORY_TIPS = {
  ru: [
    { label: "Первое:", text: "будильник на тихий звук, чтобы не выбрасывать себя из сна." },
    { label: "Второе:", text: "лежать неподвижно 30 секунд после пробуждения, восстанавливая сюжет." },
    { label: "Третье:", text: "записать сразу, даже три предложения. Через неделю-две сны начнут возвращаться." },
  ],
  en: [
    { label: "First:", text: "set a quiet alarm so you are not thrown out of the dream." },
    { label: "Second:", text: "lie still for 30 seconds after waking, reconstructing the storyline." },
    { label: "Third:", text: "write it down at once, even three sentences. In a week or two dreams will start to return." },
  ],
};

export default translations;
