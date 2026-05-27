# PATCH 0.4.2 — Flutter Parity: Analysis Limits & Account Lifecycle

Версия: 1.0
Статус: Планирование (ТЗ)
Скоуп: только Flutter-клиент. Бэкенд и веб не меняются.
Дата: 2026-05-27

---

## 0. Контекст

При сверке `client/lib/services/*` с `frontend/src/lib/api.ts` (см. `docs/FRONTEND_MAP.md`) обнаружены два расхождения, требующих правки на стороне Flutter:

1. **Утечка лимита анализов для FREE-пользователей.** Flutter использует устаревший эндпоинт `POST /dreams/{id}/analyze`, который не проходит через `limits_service` и не возвращает 402. Веб уже использует современный `POST /analyses` с честной проверкой лимита.
2. **Отсутствие критичных операций аккаунта.** Flutter не умеет: восстановить пароль (`forgot-password`), удалить аккаунт (`DELETE /auth/account`), вызвать серверный `logout`. Веб уже умеет всё три.

Биллинг (`/billing/verify-purchase`) **в скоуп не входит** — переделка под не-Google провайдеры требует архитектурного решения, делаем когда выберется набор провайдеров.

---

## 1. Часть A — Переключение анализа на `POST /analyses`

### 1.1 Проблема

`POST /dreams/{id}/analyze` (`backend/api/dreams.py:93-128`) — legacy-эндпоинт без проверки лимитов:

- ❌ нет вызова `check_analysis_allowed`
- ❌ нет `increment_analysis_count`
- ❌ всегда возвращает 200 даже когда у FREE-пользователя исчерпан недельный лимит
- ✅ возвращает синхронно `DreamResponse` со статусом `analyzing`

`POST /analyses` (`backend/api/analyses.py:30-83`) — современный путь:

- ✅ `check_analysis_allowed` → 402 `analysis_limit_reached`
- ✅ `increment_analysis_count` после успешного старта
- ✅ возвращает 202 + `AnalysisTaskResponse { analysis_id, task_id, status, message }`

**Следствие сейчас:** во Flutter FREE-юзер может запустить произвольное количество анализов — паттерн `errorCode == 402 → PaywallScreen.show()` в UI существует (см. `analysis_chat_screen.dart:237-263`), но никогда не срабатывает, потому что бэкенд по legacy-эндпоинту не отдаёт 402.

### 1.2 Решение

Внутренний рефакторинг `DreamsProvider.triggerAnalysis(id)` без изменения публичной сигнатуры и без правки UI-экранов.

**Алгоритм:**

1. Получаем текущий объект сна из `_dreams` по id (для быстрого optimistic-апдейта).
2. Вызываем `AnalysisService.createAnalysis(dreamId)`:
   - На 402 он бросает `AnalysisLimitException` → конвертируем в `_errorCode = 402, _error = 'analysis_limit_reached'`, `notifyListeners()`, `return null`. UI покажет paywall (бранч уже есть).
   - На 202 получаем `AnalysisTask { analysisId, taskId, status }`.
3. Локально проставляем у сна `analysis_status = 'analyzing'`, `has_analysis = true`, `analysis_error_message = null`. Обновляем `_dreams[index]` и текущий рендер.
4. Запускаем существующий `_pollDreamUntilSettled(id)` — он раз в N секунд тянет `GET /dreams/{id}` пока `analysis_status` не станет `analyzed` или `analysis_failed`.
5. Возвращаем обновлённый локальный `Dream` (как и раньше).

`task_id` из ответа `/analyses` нам **не нужен** — пуллинг идёт по `Dream.analysis_status`, а не по task-status. Бэкенд сам обновит статус сна, когда Celery отработает.

### 1.3 Изменения по файлам

#### `client/lib/services/dreams_service.dart`

- **Удалить** метод `triggerAnalysis(String id)` (строки 92-96). Он больше нигде не нужен и тащит legacy-URL.

#### `client/lib/providers/dreams_provider.dart`

- В заголовке файла убедиться, что импортирован `AnalysisService` и его исключение `AnalysisLimitException` из `../services/analysis_service.dart` и `../services/api_exception.dart`.
- В конструкторе/инициализации провайдера принять `AnalysisService` (или создать через тот же `ApiClient`, что и `DreamsService`). Проверить, как сейчас инжектится `_service`, и добавить аналогично `_analysisService`.
- Заменить тело `triggerAnalysis(String id)` (строки 209-229):

  ```dart
  Future<Dream?> triggerAnalysis(String id) async {
    try {
      await _analysisService.createAnalysis(id);

      final index = _dreams.indexWhere((d) => d.id == id);
      if (index >= 0) {
        _dreams[index] = _dreams[index].copyWith(
          analysisStatus: 'analyzing',
          hasAnalysis: true,
          analysisErrorMessage: null,
        );
        notifyListeners();
        _pollDreamUntilSettled(id);
        return _dreams[index];
      }
      return null;
    } on AnalysisLimitException {
      _error = 'analysis_limit_reached';
      _errorCode = 402;
      notifyListeners();
      return null;
    } catch (e) {
      if (e is ApiException) {
        _error = e.message;
        _errorCode = e.statusCode;
      } else {
        _error = 'network_error';
      }
      notifyListeners();
      return null;
    }
  }
  ```

  Если у `Dream` модели нет `copyWith` со всеми тремя полями — добавить минимальный copyWith или присваивать через конструктор `Dream(...)` вручную (зависит от модели; проверить `client/lib/models/dream.dart` перед написанием).

#### `client/lib/screens/analysis_chat_screen.dart`

- **Не меняется.** UI продолжает звать `context.read<DreamsProvider>().triggerAnalysis(...)`. Сигнатура и поведение для UI идентичны.
- Поведение становится богаче: теперь 402 действительно будет приходить — бранч `provider.errorCode == 402` (строки 237-263) начнёт срабатывать.

#### `client/lib/screens/main_chat_screen.dart`

- **Не меняется.** Та же причина.

### 1.4 Где провайдер `DreamsProvider` берёт зависимости

Перед написанием кода: найти `DreamsProvider(...)` в `main.dart` / `providers_setup.dart` (или где провайдеры регистрируются) и убедиться, что в одном месте я могу проинжектить `AnalysisService` — иначе придётся создать его рядом с `DreamsService`. Если уже зарегистрирован — переиспользовать тот же инстанс.

### 1.5 Что НЕ делаем в этой части

- Не убираем legacy-эндпоинт `POST /dreams/{id}/analyze` на бэке. На него больше нет вызовов из Flutter и веба, но он остаётся для совместимости со старыми клиентами в проде, у которых может быть закешированная сборка. Эндпоинт можно удалить отдельным патчем после анализа Sentry/логов на отсутствие трафика к нему.
- Не меняем веб (там уже корректно).
- Не меняем сам `AnalysisService` — он уже умеет правильно ходить в `/analyses` и кидать `AnalysisLimitException`.

### 1.6 Риски

- **Регресс паттерна повторной попытки.** В `analysis_chat_screen.dart:283-291` есть кнопка retry для `analysis_failed`-снов. На бэке `create_analysis(..., allow_retry=True)` уже умеет это обрабатывать — проверено в `analyses.py:61`. Регресса быть не должно.
- **Двойной инкремент счётчика на race-condition.** Сейчас, если пользователь дважды быстро тапнет «Анализировать», `analyses.py` стартует две задачи только если первая ещё не создала `Analysis`. Внутри `create_analysis` есть единственная транзакционная вставка, так что вторая упадёт в `ValueError` → 409 в роутере. Клиент должен поймать 409 и не списать второй анализ. **Текущий код этого не делает** — `createAnalysis` падает в общий `_throwApi`. Это существующая проблема, не вводимая этим патчем. Возможный фикс: в `AnalysisService.createAnalysis` обрабатывать 409 как "уже анализируется" → не показывать ошибку, просто запустить пуллинг. **Решено: фикс 409 — out of scope этого патча, отметить в TODO.**

---

## 2. Часть B — Восстановление пароля, удаление аккаунта, корректный logout

### 2.1 Проблема

Flutter `AuthService` не имеет методов для:

- `POST /api/v1/auth/forgot-password` — пользователь email-аккаунта не может восстановить пароль на мобиле.
- `POST /api/v1/auth/reset-password` — без него API-полнота неполная; на мобиле требует deep-link, но сам метод нужен.
- `DELETE /api/v1/auth/account` — требование App Store / Google Play: «удалить аккаунт прямо в приложении». Без этого блокируется публикация.
- `POST /api/v1/auth/logout` — сейчас `AuthService.logout()` (строка 141) чистит только локальные токены; бэкенд не уведомляется. Сейчас сервер всё равно ничего не делает (stateless JWT, см. `backend/api/auth.py:567-577`), но контрактно правильнее звать его — будет совместимо с будущим blacklist'ом в Redis.

### 2.2 Решение — API-слой

Добавить 4 метода в `client/lib/services/auth_service.dart`:

```dart
Future<void> forgotPassword({required String email}) async {
  final response = await _api.post(
    '/api/v1/auth/forgot-password',
    body: {'email': email},
    auth: false,
  );
  if (response.statusCode == 400) {
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    throw Exception(data['detail'] ?? 'oauth_account_no_password');
  }
  if (response.statusCode != 200) {
    throw Exception('forgot_password_failed');
  }
}

Future<void> resetPassword({
  required String token,
  required String newPassword,
}) async {
  final response = await _api.post(
    '/api/v1/auth/reset-password',
    body: {'token': token, 'new_password': newPassword},
    auth: false,
  );
  if (response.statusCode == 400) {
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    throw Exception(data['detail'] ?? 'invalid_or_expired_token');
  }
  if (response.statusCode != 200) {
    throw Exception('reset_password_failed');
  }
}

Future<void> deleteAccount() async {
  final response = await _api.delete('/api/v1/auth/account');
  if (response.statusCode != 200) {
    throw Exception('delete_account_failed');
  }
  await _storage.clearTokens();
}
```

И поменять существующий `logout`:

```dart
Future<void> logout() async {
  try {
    await _api.post('/api/v1/auth/logout', body: const {});
  } catch (_) {
    // logout всегда успешен с точки зрения клиента — токены чистим в любом случае
  }
  await _storage.clearTokens();
}
```

### 2.3 Изменения по файлам

#### `client/lib/services/auth_service.dart`

- **Изменить** `logout()` (строки 141-143) на версию, зовущую `/api/v1/auth/logout` с safe-try-catch перед `clearTokens()`.
- **Добавить** методы `forgotPassword`, `resetPassword`, `deleteAccount` сразу после `logout()`.

#### `client/lib/providers/auth_provider.dart` (или эквивалент — найти где живёт состояние авторизации)

- Добавить методы-обёртки:
  - `Future<bool> forgotPassword(String email)` — вызывает `authService.forgotPassword`, ловит исключения в `_error/_errorCode`, возвращает bool.
  - `Future<bool> deleteAccount()` — вызывает `authService.deleteAccount`, на успехе переводит провайдер в `unauthenticated`-стейт (или эмулирует logout — те же действия что и `logout()` flow).
  - `Future<bool> resetPassword(String token, String newPassword)` — аналогично, для будущего deep-link экрана.
- Проверить существующий `logout()` в провайдере: он должен дёргать обновлённый `authService.logout()` — поведение для UI не меняется.

### 2.4 UI: что в скоупе этого патча

**В скоупе (минимально, для DELETE/account чтобы пройти модерацию сторов):**

1. В Profile-экране (`client/lib/screens/profile_screen.dart` или эквивалент — найти):
   - Кнопка **«Удалить аккаунт»** в зоне «Опасно».
   - Confirm-диалог с текстом из l10n: «Это удалит все ваши сны, анализы и историю. Действие необратимо.»
   - На подтверждение → `authProvider.deleteAccount()` → редирект на стартовый экран / `AuthGate`.

**В скоупе (минимально, для email-юзеров):**

2. На экране логина (или AuthModal-эквивалент) — кнопка/ссылка «Забыли пароль?»:
   - Открывает простой экран/sheet с одним полем email и кнопкой «Отправить».
   - На submit → `authProvider.forgotPassword(email)` → toast «Письмо отправлено» и возврат на login.

**ВНЕ скоупа (отложено):**

3. **Экран `reset-password`.** Требует deep-link инфраструктуры (`innercore://reset-password?token=...`), регистрации intent-filter в `AndroidManifest.xml` и universal-link entitlement на iOS. Метод API добавляем, экран — отдельным патчем, когда будем настраивать deep-links.
4. **UI кнопок Google Sign-In / link-provider в Profile.** Уже отложено в FRONTEND_MAP §13 — продолжаем откладывать.

### 2.5 i18n

В `client/lib/l10n/app_en.arb` и `app_ru.arb` (и других, если есть) добавить ключи:

- `deleteAccount` — «Delete account» / «Удалить аккаунт»
- `deleteAccountConfirmTitle` — «Delete account?» / «Удалить аккаунт?»
- `deleteAccountConfirmBody` — «This will permanently delete all your dreams, analyses, and chat history. This cannot be undone.» / «Это навсегда удалит все ваши сны, анализы и переписки. Действие необратимо.»
- `deleteAccountConfirmAction` — «Delete forever» / «Удалить навсегда»
- `deleteAccountCancel` — «Cancel» / «Отмена»
- `forgotPasswordLink` — «Forgot password?» / «Забыли пароль?»
- `forgotPasswordTitle` — «Reset your password» / «Сброс пароля»
- `forgotPasswordHelper` — «We'll email you a link to reset your password.» / «Мы пришлём ссылку для сброса на ваш email.»
- `forgotPasswordSubmit` — «Send link» / «Отправить ссылку»
- `forgotPasswordSent` — «If this email is registered, a reset link has been sent.» / «Если такой email зарегистрирован, мы отправили на него ссылку.»

После правки `.arb` запустить `flutter gen-l10n` (или дождаться авто-генерации в `flutter run`).

### 2.6 Риски и крайние случаи

- **`forgot-password` для OAuth-аккаунта.** Бэкенд возвращает 400 `Cannot reset password for OAuth2 accounts` (`auth.py:379-382`). UI должен показать понятный месседж — добавить в `app_en.arb` ключ `forgotPasswordOauthError` и обрабатывать в провайдере.
- **`delete-account` каскадно сносит всё.** Подтверждение через диалог обязательно. После — гарантированный clearTokens даже при сетевой ошибке (но мы делаем `clearTokens` только при 200 — это правильно, чтобы пользователь мог повторить попытку, если бэкенд упал на середине удаления).
- **Анонимный пользователь и delete-account.** `CurrentUser` зависимость на бэке вернёт текущего юзера независимо от того, anonymous он или нет. Удаление работает и для анонимов. **Кнопку в Profile показываем всем**, включая анонимных (у анонимного она тоже имеет смысл — сбросить устройство).
- **`logout` падает при невалидном access_token.** Текущая логика рефреша через `ApiClient` сама попытается обновить токен. Если рефреш-токен тоже мёртв — `_api.post('/auth/logout')` поднимет исключение → ловим в catch-all → всё равно делаем `clearTokens`. Корректно.

---

## 3. План работ (порядок коммитов)

1. **Коммит 1 — Analysis migration:** правки `dreams_service.dart` (удаление `triggerAnalysis`), `dreams_provider.dart` (новый `triggerAnalysis` через `AnalysisService`), регистрация `AnalysisService` в провайдере где нужно. Запуск `flutter analyze`, ручной smoke-тест на эмуляторе: создать сон → анализ → дождаться `analyzed`; на FREE-тарифе исчерпать лимит → ждать paywall.
2. **Коммит 2 — Auth API methods:** добавить `forgotPassword`, `resetPassword`, `deleteAccount`, обновить `logout` в `AuthService`. Добавить методы-обёртки в auth-провайдере. `flutter analyze`.
3. **Коммит 3 — i18n keys:** правка `.arb`-файлов, `flutter gen-l10n`.
4. **Коммит 4 — Delete Account UI:** кнопка в Profile + confirm-диалог + редирект.
5. **Коммит 5 — Forgot Password UI:** ссылка на login + bottom-sheet / экран ввода email + успешный toast.

После каждого коммита — `git status` и `flutter analyze`. Перед пушем — ещё раз `flutter test`, если тесты есть в репо (проверить наличие `client/test/`).

## 4. Acceptance criteria

### Часть A
- [ ] В `dreams_service.dart` нет вызова `/dreams/{id}/analyze`.
- [ ] FREE-юзер, исчерпавший недельный лимит, при нажатии «Анализировать» видит paywall (бранч `errorCode == 402`).
- [ ] PRO/TRIAL-юзер продолжает запускать анализы без ограничений.
- [ ] Polling после старта анализа продолжает работать — статус сна доходит до `analyzed` или `analysis_failed`.
- [ ] Кнопка retry на `analysis_failed`-сне продолжает работать.

### Часть B
- [ ] В Profile есть рабочая кнопка «Удалить аккаунт» с подтверждением.
- [ ] После успешного удаления юзер выкидывается на старт; повторный запуск приложения создаёт нового анонима.
- [ ] На экране логина есть «Забыли пароль?». Сабмит email возвращает success-toast (даже для несуществующего email — это by-design на бэке).
- [ ] `logout` теперь дёргает `/api/v1/auth/logout`, при сетевой ошибке всё равно чистит локальные токены.
- [ ] Все новые строки в `.arb` и сгенерированы в `AppLocalizations`.

## 5. Out of scope (явно отложено)

- Удаление legacy `POST /dreams/{id}/analyze` на бэке.
- Фикс race-condition 409 в `AnalysisService.createAnalysis`.
- Deep-link экран `/reset-password?token=...` во Flutter.
- UI кнопок Google Sign-In и link-provider в Profile.
- Перепиливание `/billing/verify-purchase` под не-Google провайдеров.
- Apple Sign-In.
