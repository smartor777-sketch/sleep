# PATCH 0.4.1 — Auth & Billing

Версия: 1.0
Статус: Планирование
Цель: Google Play

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
- `POST /api/v1/auth/verify-email` — подтверждение email
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
  verify_email_screen.dart    — ожидание подтверждения email
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
   - Package name: (из `android/app/build.gradle`)
   - SHA-1: `keytool -list -v -keystore ~/.android/debug.keystore`
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

## 3. Google Play Billing

### 3.1 Архитектура

```
Клиент (Flutter)
  └─ in_app_purchase
       └─ Google Play
            └─ Purchase token
                 └─ POST /api/v1/billing/verify-purchase
                      └─ Backend → Google Play Developer API
                           └─ Обновить sub_type + sub_expires_at
```

### 3.2 Google Play Console

1. Создать аккаунт разработчика Google Play ($25 разово)
2. Добавить приложение
3. В разделе **Monetize → Subscriptions** создать продукты:
   - `premium_monthly` — месячная подписка
   - `premium_annual` — годовая подписка (опционально)
4. Подключить Google Play Developer API:
   - Service account → JSON key → `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON`

### 3.3 Flutter

Пакет: `in_app_purchase` (добавить в pubspec.yaml)

```dart
// lib/services/billing_service.dart
class BillingService {
  final InAppPurchase _iap = InAppPurchase.instance;

  Future<void> initialize() async {
    _iap.purchaseStream.listen(_onPurchaseUpdate);
  }

  Future<void> buyPremiumMonthly() async {
    const productId = 'premium_monthly';
    final details = await _iap.queryProductDetails({productId});
    final param = PurchaseParam(productDetails: details.productDetails.first);
    await _iap.buyNonConsumable(purchaseParam: param);
  }

  Future<void> _onPurchaseUpdate(List<PurchaseDetails> purchases) async {
    for (final purchase in purchases) {
      if (purchase.status == PurchaseStatus.purchased) {
        await _verifyOnBackend(purchase.verificationData.serverVerificationData);
        await _iap.completePurchase(purchase);
      }
    }
  }
}
```

### 3.4 Backend

**Новая таблица** `subscriptions`:
```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(32) NOT NULL,       -- 'google_play'
    product_id VARCHAR(128) NOT NULL,    -- 'premium_monthly'
    purchase_token TEXT NOT NULL,
    status VARCHAR(32) NOT NULL,         -- 'active' | 'expired' | 'cancelled'
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
→ Верифицировать через Google Play API
→ Обновить users.sub_type = 'premium', users.sub_expires_at
→ Сохранить в subscriptions

GET /api/v1/billing/status
→ Вернуть текущий статус подписки

POST /api/v1/billing/webhook  (Google Play RTDN)
→ Real-time Developer Notification
→ Обновить статус при отмене / возобновлении
```

**Env переменные:**
```
GOOGLE_PLAY_PACKAGE_NAME=com.example.jungai
GOOGLE_PLAY_SERVICE_ACCOUNT_JSON='{...}'
```

**Python библиотека:** `google-api-python-client`

### 3.5 Premium — что даёт подписка

Определить логику ограничений для бесплатного тарифа:

| Функция | Free | Premium |
|---|---|---|
| Снов в день | 5 | Без лимита |
| Анализов в день | 5 | Без лимита |
| Карта символов | ✅ | ✅ |
| user.md / долгая память | ❌ | ✅ |
| Чат по сну | Ограничен | Без лимита |

> Конкретные лимиты — на усмотрение.

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

## 6. Зависимости и порядок работы

```
1. Google Cloud Console — создать проект, получить google-services.json
2. Backend: /auth/google + /auth/merge-anonymous
3. Flutter: AuthGateScreen + EmailLogin + GoogleSignIn
4. Google Play Console — создать продукты подписок
5. Backend: /billing/verify-purchase + /billing/webhook
6. Flutter: BillingService + PremiumScreen
7. Alembic: миграция 004 (subscriptions table)
8. Тестирование покупок через Google Play test environment
```

---

## 7. Acceptance Criteria

1. Пользователь может зарегистрироваться по email и подтвердить почту
2. Пользователь может войти по email + пароль
3. Пользователь может войти через Google
4. Анонимные данные переносятся при первом входе (мерж)
5. Сброс пароля работает через email
6. Пользователь видит экран Premium с ценой из Google Play
7. Покупка подписки проходит и верифицируется на бекенде
8. После покупки `sub_type = 'premium'` и снимаются лимиты
9. Отмена подписки обрабатывается через RTDN webhook
10. Все строки локализованы (EN + RU)
