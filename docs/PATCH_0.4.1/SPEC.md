# PATCH 0.4.1 — Auth, Billing & Dream UX

Версия: 1.2
Статус: Планирование
Цель: Google Play
Package: com.okoloboga.jungai

---

## Обзор

Патч вводит три взаимосвязанных системы:

1. **Email-авторизация** — регистрация и вход по email + пароль
2. **Google Sign-In** — OAuth 2.0 через Google
3. **Google Play Billing** — подписки Premium через In-App Purchase

Анонимный режим (device_id) сохраняется как fallback для новых пользователей.
При первом входе через email или Google анонимный аккаунт **мержится** с постоянным.

---

## 1. Email-авторизация

### 1.1 Что уже есть (backend)

- `POST /api/v1/auth/register` — регистрация
- `POST /api/v1/auth/login` — вход
- `POST /api/v1/auth/verify-email` — подтверждение 6-значного кода из письма
- `POST /api/v1/auth/forgot-password` — сброс пароля
- Таблицы `email_verifications`, `password_resets`
- SMTP настройки в `.env`

→ Бекенд реализован полностью. Нужен только UI.

### 1.2 Flutter UI

**Новые экраны:**

```
lib/screens/auth/
  auth_gate_screen.dart       — выбор способа входа
  email_login_screen.dart     — вход по email
  email_register_screen.dart  — регистрация
  forgot_password_screen.dart — сброс пароля
  verify_email_screen.dart    — ввод 6-значного кода из письма
```

**Флоу:**

```
Запуск приложения
  └─ Анонимный пользователь
       └─ Кнопка "Войти / Создать аккаунт" (в Profile)
            └─ AuthGateScreen
                 ├─ Email → EmailLoginScreen / EmailRegisterScreen
                 └─ Google → Google Sign-In flow
```

**Мерж анонима в постоянный аккаунт:**

При успешном входе/регистрации:
- Сохранить `device_id` текущего анонимного пользователя
- Backend: перенести все `dreams`, `analyses`, `analysis_messages` на новый `user_id`
- Удалить анонимный аккаунт
- Сохранить новый JWT в SecureStorage

### 1.3 Backend — эндпоинт мержа

```
POST /api/v1/auth/merge-anonymous
Body: { anonymous_device_id: string }
Auth: Bearer <новый токен>
```

Логика:
1. Найти анонимного пользователя по `device_id`
2. Перенести все его данные (dreams, analyses, messages, chunks, symbols) на текущего пользователя
3. Удалить анонимного пользователя

---

## 2. Google Sign-In

### 2.1 Настройка Google Cloud Console

1. Создать проект в [console.cloud.google.com](https://console.cloud.google.com)
2. Включить **Google Sign-In API**
3. OAuth consent screen:
   - User type: External
   - App name: JungAI
   - Support email: (ваш gmail)
   - Scopes: `email`, `profile`, `openid`
4. Создать OAuth credentials:
   - Тип: Android
   - Package name: `com.okoloboga.jungai`
   - SHA-1 debug: `keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android`
   - SHA-1 release: из `jungai-release.jks` (добавить оба fingerprint в консоли)
   - → Получить `google-services.json`
5. Создать Web client credentials (для бекенда):
   - Тип: Web application
   - → Получить `GOOGLE_CLIENT_ID` и `GOOGLE_CLIENT_SECRET`

### 2.2 Flutter

Пакет: `google_sign_in` (уже в `pubspec.yaml`)

```dart
// lib/services/google_auth_service.dart
class GoogleAuthService {
  final _googleSignIn = GoogleSignIn(scopes: ['email', 'profile']);

  Future<String?> signIn() async {
    final account = await _googleSignIn.signIn();
    if (account == null) return null;
    final auth = await account.authentication;
    return auth.idToken; // отправляем на бекенд
  }
}
```

Файл `google-services.json` → `android/app/google-services.json`

### 2.3 Backend — что уже есть и что добавить

Уже есть:
- `OAuthIdentity` модель
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` в env/config

Добавить:
- `POST /api/v1/auth/google` — принять `id_token`, верифицировать через Google, вернуть JWT
- Верификация: `google-auth-library` или ручная проверка через `https://oauth2.googleapis.com/tokeninfo`

```python
# backend/api/auth.py — новый эндпоинт
@router.post("/google")
async def google_auth(token: GoogleTokenRequest, db: DatabaseSession):
    # 1. Верифицировать id_token через Google
    # 2. Найти или создать пользователя по google_subject
    # 3. Вернуть JWT пару
```

---

## 3. Монетизация — тарифы и Paywall

### 3.1 Структура тарифов

```
FREE → TRIAL (7 дней) → PRO
```

#### FREE (по умолчанию)
| Функция | Лимит |
|---|---|
| Запись снов | ∞ |
| Анализов | 2 / неделя |
| Чат по сну | ❌ |
| Карта символов | ❌ |
| user.md / долгая память | ❌ |

Цель FREE: сформировать привычку и накопить данные. Пользователь видит ценность, но упирается в лимит анализа.

#### TRIAL
- 7 дней полного доступа без ограничений
- Активируется автоматически при первой регистрации (email или Google)
- После trial → автоматически возврат в FREE, если нет покупки
- Не требует привязки карты

#### PRO — три тарифа

| ID | Название | Цена | Назначение |
|---|---|---|---|
| `pro_weekly` | Неделя | $2.99/нед | Decoy — импульсная покупка, делает месяц дешёвым |
| `pro_monthly` | Месяц | $6.99/мес | Основной тариф |
| `pro_yearly` | Год | $49.99/год (~$4.16/мес) | Максимальный LTV, якорь цены |

PRO даёт полный доступ: ∞ анализы, чат, карта, user.md.

---

### 3.2 Paywall — UX и подача

**Принцип: пользователь видит не 3 варианта, а 1 решение + альтернативы.**

```
┌─────────────────────────────────────┐
│  Разблокируйте полный анализ снов   │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  ГОД          ★ BEST VALUE  │    │  ← выделен, выбран по умолчанию
│  │  $49.99/год · $4.16/мес     │    │
│  └─────────────────────────────┘    │
│                                     │
│  МЕСЯЦ                              │
│  $6.99/месяц                        │
│                                     │
│  НЕДЕЛЯ                             │  ← мелким шрифтом
│  $2.99/неделю                       │
│                                     │
│  [  Начать — 7 дней бесплатно  ]    │
│  Отмена в любое время               │
└─────────────────────────────────────┘
```

**Психология:**
- **Anchoring**: сначала виден $49.99 → $6.99 кажется дёшево
- **Decoy**: Weekly нужен не для дохода, а чтобы Monthly выглядел разумно
- **Yearly** — основной источник дохода, помечен BEST VALUE

**Триггер показа Paywall:**

```
1. После 7 дней trial (автоматически при запуске)
2. При нажатии на кнопку "Чат" (FREE) → открывается Paywall
3. При нажатии на "Карта" (FREE) → открывается Paywall
4. При нажатии "Анализировать" (FREE, лимит исчерпан) → Paywall
   → заголовок: "Вы достигли лимита анализов"
   → подзаголовок: "У вас X снов без анализа"
   → далее стандартный экран выбора тарифа
```

Фичи **видны** в интерфейсе, но при нажатии показывают Paywall (не скрыты).
Кнопка "7 дней бесплатно" показывается только если пользователь ещё не использовал trial.

---

### 3.3 Google Play Console

1. Создать аккаунт разработчика ($25 разово)
2. Добавить приложение, package: `com.okoloboga.jungai`
3. **Monetize → Subscriptions** — создать 3 base plan:
   - `pro_weekly` — $2.99, биллинг каждые 7 дней
   - `pro_monthly` — $6.99, биллинг каждые 30 дней
   - `pro_yearly` — $49.99, биллинг каждые 365 дней
4. Для каждого — добавить **free trial offer** на 7 дней
   (Google Play trial = app-level TRIAL — одно и то же, не дублировать логику)
5. Подключить Google Play Developer API:
   - IAM → Service account → JSON key
   - Env: `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON`

**Release keystore (создать перед сабмитом):**
```bash
keytool -genkey -v \
  -keystore jungai-release.jks \
  -alias jungai \
  -keyalg RSA -keysize 2048 \
  -validity 10000
```
Сохранить `jungai-release.jks` в безопасном месте (не в репозитории).
Добавить в `android/key.properties`:
```
storePassword=<пароль>
keyPassword=<пароль>
keyAlias=jungai
storeFile=../../jungai-release.jks
```

---

### 3.4 Backend

**Новые поля на `users`** (в существующей таблице):
```sql
-- уже есть: sub_type VARCHAR(16), sub_expires_at TIMESTAMPTZ
-- добавить в миграции 004:
ALTER TABLE users ADD COLUMN trial_started_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN analyses_week_count INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN analyses_week_reset_at TIMESTAMPTZ;
```

**Существующие пользователи** при релизе 0.4.1: остаются на FREE (trial не выдаётся задним числом).
TRIAL выдаётся только при первой регистрации через email или Google после выхода патча.

**Новая таблица** `subscriptions`:
```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    provider VARCHAR(32) NOT NULL,          -- 'google_play'
    product_id VARCHAR(128) NOT NULL,       -- 'pro_monthly'
    purchase_token TEXT NOT NULL UNIQUE,
    status VARCHAR(32) NOT NULL,            -- 'active' | 'expired' | 'cancelled'
    starts_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Новые эндпоинты:**

```
POST /api/v1/billing/verify-purchase
Body: { purchase_token: string, product_id: string }
→ Верифицировать через Google Play Developer API
→ Записать в subscriptions
→ Обновить users.sub_type = 'pro', users.sub_expires_at

GET /api/v1/billing/status
→ { sub_type, sub_expires_at, trial_days_left, analyses_left_this_week }

POST /api/v1/billing/webhook   ← Google Play RTDN
→ Real-time Developer Notification
→ Обновить статус при отмене / возобновлении / истечении
```

**Лимит анализов для FREE:**

```python
# backend/services/limits_service.py
async def check_analysis_allowed(user: User, db) -> bool:
    if user.sub_type in ('pro', 'trial'):
        return True
    # Сбросить счётчик если прошла неделя
    now = datetime.now(timezone.utc)
    if user.analyses_week_reset_at is None or \
       (now - user.analyses_week_reset_at).days >= 7:
        user.analyses_week_count = 0
        user.analyses_week_reset_at = now
    return user.analyses_week_count < 2
```

**Python библиотека:** `google-api-python-client`

**Env переменные:**
```
GOOGLE_PLAY_PACKAGE_NAME=com.okoloboga.jungai
GOOGLE_PLAY_SERVICE_ACCOUNT_JSON='{...}'
```

---

### 3.5 Flutter

Пакет: `in_app_purchase` (добавить в pubspec.yaml)

**Новые файлы:**
```
lib/services/billing_service.dart    — IAP логика
lib/providers/billing_provider.dart  — состояние подписки
lib/screens/paywall_screen.dart      — экран выбора тарифа
lib/widgets/paywall_trigger.dart     — обёртка для защищённых фич
```

**BillingService:**
```dart
class BillingService {
  static const _productIds = {'pro_weekly', 'pro_monthly', 'pro_yearly'};
  final InAppPurchase _iap = InAppPurchase.instance;

  Future<void> initialize() async {
    _iap.purchaseStream.listen(_onPurchaseUpdate);
    await _iap.restorePurchases();
  }

  Future<List<ProductDetails>> loadProducts() async {
    final response = await _iap.queryProductDetails(_productIds);
    return response.productDetails;
  }

  Future<void> buy(ProductDetails product) async {
    final param = PurchaseParam(productDetails: product);
    await _iap.buyNonConsumable(purchaseParam: param);
  }

  Future<void> _onPurchaseUpdate(List<PurchaseDetails> purchases) async {
    for (final p in purchases) {
      if (p.status == PurchaseStatus.purchased ||
          p.status == PurchaseStatus.restored) {
        await _verifyOnBackend(p);
        await _iap.completePurchase(p);
      }
    }
  }
}
```

**PaywallTrigger — защита фич:**
```dart
// Обёртка: при нажатии проверяет тариф, иначе открывает Paywall
class PaywallTrigger extends StatelessWidget {
  final Widget child;
  final VoidCallback onAllowed;

  @override
  Widget build(BuildContext context) {
    final billing = context.watch<BillingProvider>();
    return GestureDetector(
      onTap: billing.hasAccess
          ? onAllowed
          : () => PaywallScreen.show(context),
      child: child,
    );
  }
}
```

---

## 4. UI/UX изменения в Profile

Текущий Profile Screen расширяется:

```
Profile
  ├─ [Не залогинен] → кнопка "Войти / Создать аккаунт"
  ├─ [Залогинен анонимно] → "Привязать аккаунт" (email или Google)
  ├─ [Залогинен] → email, имя, кнопка выйти
  └─ Подписка
       ├─ [Free] → карточка "Перейти на Premium"
       └─ [Premium] → дата окончания, управление
```

---

## 5. Новые файлы

### Backend
```
backend/api/billing.py
backend/services/google_auth_service.py
backend/services/billing_service.py
backend/models/subscription.py
backend/alembic/versions/004_add_subscriptions.py
```

### Client
```
client/lib/screens/auth/auth_gate_screen.dart
client/lib/screens/auth/email_login_screen.dart
client/lib/screens/auth/email_register_screen.dart
client/lib/screens/auth/forgot_password_screen.dart
client/lib/screens/auth/verify_email_screen.dart
client/lib/screens/billing/premium_screen.dart
client/lib/services/google_auth_service.dart
client/lib/services/billing_service.dart
client/lib/providers/billing_provider.dart
android/app/google-services.json  ← получить из Google Console
```

---

## 6. Dream UX — ручной анализ, заголовок, градиент

### 6.1 Проблема

Сейчас анализ запускается автоматически при сохранении сна. Это убирает у пользователя контроль: он не может сначала перечитать сон, исправить текст и только потом запросить анализ.

### 6.2 Новый флоу записи сна

```
Пользователь записывает сон → Сохраняет
  └─ Открывается экран сна (AnalysisChatScreen)
       ├─ [Нет анализа] → большая кнопка "Анализировать"
       │                   вместо поля ввода сообщения
       └─ [Анализ есть] → поле ввода сообщения для чата
```

Анализ запускается только по нажатию кнопки — не автоматически.

### 6.3 Backend — убрать автозапуск анализа

**Файл:** `backend/api/dreams.py` (или где сейчас вызывается `analyze_dream_task.delay()`)

- Убрать вызов Celery-задачи при создании сна
- Добавить эндпоинт для ручного запуска:

```
POST /api/v1/dreams/{dream_id}/analyze
→ Запустить analyze_dream_task
→ Вернуть { task_id, status: "pending" }
```

### 6.4 Flutter — кнопка «Анализировать»

**Файл:** `client/lib/screens/analysis_chat_screen.dart`

Логика отображения нижней панели:

```dart
// Вместо поля ввода — кнопка, если анализа нет
if (analysis == null || analysis.status == AnalysisStatus.none) {
  return _buildAnalyzeButton();  // большая кнопка по центру
}
if (analysis.status == AnalysisStatus.pending ||
    analysis.status == AnalysisStatus.processing) {
  return _buildAnalysisProgress();  // индикатор прогресса
}
// Анализ завершён — обычное поле ввода
return _buildMessageInput();
```

Кнопка «Анализировать»:
- Полноширинная, крупная
- При нажатии: `POST /api/v1/dreams/{id}/analyze` → переходит в состояние `pending`
- Пока идёт анализ — показывает пульсирующий индикатор с текстом
- Polling: использовать существующий механизм (пиктограмма загрузки на карточке сна уже работает).
  Открытый `AnalysisChatScreen` подписывается на обновления анализа через тот же механизм.

### 6.5 Заголовок по умолчанию — первые 3 слова

**Где:** клиент, при сохранении нового сна.

```dart
String _defaultTitle(String content) {
  final words = content.trim().split(RegExp(r'\s+')).take(3);
  return words.join(' ');
}
```

Применяется если пользователь не ввёл title вручную.
Записывается в `Dream.title` при создании.

### 6.6 Градиент по умолчанию

Все карточки снов без заданного градиента используют:
- `gradient_color_1 = #FA9042`
- `gradient_color_2 = #8885FF`

**Где менять:** `client/lib/widgets/dream_card.dart` (или где рендерится карточка) — fallback цвета при `null`.

### 6.7 LLM устанавливает Title и Gradient после анализа

После завершения анализа LLM возвращает не только текст анализа, но и метаданные сна.

**Промпт (добавить инструкцию):**

```
В конце ответа добавь JSON-блок:
<dream_meta>
{
  "title": "Краткое поэтическое название сна (3-5 слов)",
  "gradient_from": "#RRGGBB",
  "gradient_to": "#RRGGBB"
}
</dream_meta>

Цвета должны отражать эмоциональный тон сна.
Тёплые тона (красный, оранжевый) — тревога, страсть.
Холодные (синий, фиолетовый) — спокойствие, глубина.
Тёмные — тяжёлые темы. Светлые — позитивные.
```

**Backend — парсинг метаданных:**

```python
# backend/services/analysis_service.py (или tasks.py)
import re, json

def extract_dream_meta(llm_response: str) -> dict | None:
    match = re.search(r'<dream_meta>(.*?)</dream_meta>', llm_response, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(1).strip())
    except Exception:
        return None

# После завершения анализа:
meta = extract_dream_meta(result_text)
if meta:
    dream.title = meta.get('title') or dream.title
    dream.gradient_color_1 = meta.get('gradient_from')
    dream.gradient_color_2 = meta.get('gradient_to')
    # Убрать <dream_meta>...</dream_meta> из текста анализа
    clean_result = re.sub(r'<dream_meta>.*?</dream_meta>', '', result_text, flags=re.DOTALL).strip()
```

---

## 7. Зависимости и порядок работы

```
Dream UX (независимо, можно раньше):
  1. Backend: убрать автозапуск, добавить POST /dreams/{id}/analyze
  2. Backend: парсинг <dream_meta> в tasks.py + обновление dream
  3. Backend: обновить промпт с инструкцией dream_meta
  4. Flutter: кнопка «Анализировать» в AnalysisChatScreen
  5. Flutter: default title (первые 3 слова) при создании
  6. Flutter: default gradient FA9042→8885FF в карточке

Auth & Billing (требует внешних настроек):
  7. Google Cloud Console — создать проект, получить google-services.json
  8. Backend: /auth/google + /auth/merge-anonymous
  9. Flutter: AuthGateScreen + EmailLogin + GoogleSignIn
  10. Google Play Console — создать продукты подписок
  11. Backend: /billing/verify-purchase + /billing/webhook
  12. Flutter: BillingService + PremiumScreen
  13. Alembic: миграция 004 (subscriptions table)
  14. Тестирование покупок через Google Play test environment
```

---

## 8. Acceptance Criteria

**Dream UX:**
1. Новый сон сохраняется без автоматического запуска анализа
2. В экране сна вместо поля ввода — кнопка «Анализировать»
3. После нажатия кнопки — индикатор прогресса
4. После завершения анализа — поле ввода сообщений
5. Title нового сна по умолчанию = первые 3 слова
6. Карточка сна без градиента показывает FA9042 → 8885FF
7. После анализа LLM заполняет title и gradient цвета
8. Текст анализа не содержит `<dream_meta>` блок

**Auth:**
9. Регистрация и вход по email работают
10. Вход через Google работает
11. Анонимные данные переносятся при первом входе
12. Сброс пароля работает через email

**Billing:**
13. Экран Premium отображает цену из Google Play
14. Покупка верифицируется на бекенде
15. После покупки снимаются лимиты
16. Отмена подписки обрабатывается через RTDN webhook

**Общее:**
17. Все строки локализованы (EN + RU)
