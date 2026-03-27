// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Russian (`ru`).
class AppLocalizationsRu extends AppLocalizations {
  AppLocalizationsRu([String locale = 'ru']) : super(locale);

  @override
  String get startupError => 'Не удалось подключиться к серверу';

  @override
  String get retry => 'Повторить';

  @override
  String get downloadLatest => 'Скачать последнюю версию';

  @override
  String get userLoadError => 'Не удалось загрузить пользователя';

  @override
  String get dreamSaveError => 'Не удалось сохранить сон';

  @override
  String get dreamCopied => 'Сон скопирован';

  @override
  String get dreamDeleteError => 'Не удалось удалить сон';

  @override
  String get rateLimitError =>
      'Достигнут лимит 5 снов в день. Попробуйте позже.';

  @override
  String get networkError => 'Проблемы с сетью. Проверьте подключение.';

  @override
  String get genericError => 'Ошибка запроса. Попробуйте ещё раз.';

  @override
  String get searchHint => 'Поиск снов...';

  @override
  String get editDreamHint => 'Редактировать сон...';

  @override
  String get writeDreamHint => 'Напишите сон...';

  @override
  String get emptyDreamsHint => 'Просто запиши свой Сон';

  @override
  String get listeningLabel => 'Идёт запись...';

  @override
  String get recordingWarning => 'Запись идёт уже больше минуты';

  @override
  String get partialTranscription => 'Часть записи не удалось распознать';

  @override
  String get analysisFailed => 'Анализ не удался';

  @override
  String get analyzingLabel => 'Анализ...';

  @override
  String get messageFailed => 'Ответ не получен';

  @override
  String get dreamAnalysisTitle => 'Анализ сна';

  @override
  String get writeMessageHint => 'Напишите сообщение...';

  @override
  String get messageSendError => 'Не удалось отправить сообщение';

  @override
  String get retryAnalysis => 'Повторить анализ';

  @override
  String get editDate => 'Изменить дату';

  @override
  String get profileTitle => 'Профиль';

  @override
  String get aboutMeLabel => 'Обо мне';

  @override
  String get profileSaveError => 'Не удалось сохранить профиль';

  @override
  String get totalDreams => 'Всего снов';

  @override
  String get streak => 'Streak';

  @override
  String get avgTime => 'Среднее время';

  @override
  String get dreamsByWeekday => 'Сны по дням недели';

  @override
  String get dreamsLast14Days => 'Сны за 14 дней';

  @override
  String get archetypes => 'Архетипы';

  @override
  String get accentColorLabel => 'Выберите цвет акцента:';

  @override
  String get darkThemeLabel => 'Темная тема';

  @override
  String get fontSizeLabel => 'Размер шрифта';

  @override
  String get fontSizeSmall => 'Маленький';

  @override
  String get fontSizeMedium => 'Средний';

  @override
  String get fontSizeLarge => 'Большой';

  @override
  String get languageLabel => 'Язык';

  @override
  String get guest => 'Гость';

  @override
  String get accountLinked => 'Аккаунт привязан';

  @override
  String get providers => 'Провайдеры';

  @override
  String get noProviders => 'Нет';

  @override
  String get googleTokenError => 'Не удалось получить токен Google';

  @override
  String get appleTokenError => 'Не удалось получить токен Apple';

  @override
  String get identityAlreadyLinked =>
      'Этот аккаунт уже привязан к другому профилю.';

  @override
  String get linkFailed =>
      'Не удалось подтвердить аккаунт. Попробуйте ещё раз.';

  @override
  String get profileError => 'Ошибка профиля. Попробуйте ещё раз.';

  @override
  String get editTitleLabel => 'Изменить название';

  @override
  String get titleHint => 'Название';

  @override
  String get deleteDreamConfirm => 'Удалить этот сон?';

  @override
  String get cancel => 'Отмена';

  @override
  String get enterCredentials => 'Введите email и пароль';

  @override
  String get registerTitle => 'Регистрация';

  @override
  String get registerUnavailable => 'Регистрация пока недоступна.';

  @override
  String get ok => 'Ок';

  @override
  String get passwordLabel => 'Пароль';

  @override
  String get signIn => 'Войти';

  @override
  String get createAccount => 'Создать аккаунт';

  @override
  String get copy => 'Копировать';

  @override
  String get edit => 'Редактировать';

  @override
  String get delete => 'Удалить';

  @override
  String get analyze => 'Анализировать';

  @override
  String get save => 'Сохранить';

  @override
  String get savedSuccess => 'Сохранено';

  @override
  String get updateAvailable => 'Доступно обновление';

  @override
  String get updateMessage =>
      'Доступна новая версия приложения. Обновите для лучшей работы.';

  @override
  String get updateNow => 'Обновить';

  @override
  String get later => 'Позже';

  @override
  String get dreamChat => 'Чат сна';

  @override
  String get dreamChatHint =>
      'Выберите сон в плитке, чтобы открыть его анализ и чат.';

  @override
  String get onboardingTitle => 'Давайте познакомимся';

  @override
  String onboardingStep(int step, int total) {
    return 'Шаг $step из $total';
  }

  @override
  String get skip => 'Пропустить';

  @override
  String get finish => 'Завершить';

  @override
  String get next => 'Далее';

  @override
  String get occupationQuestion => 'Чем вы сейчас занимаетесь?';

  @override
  String get occupationHint =>
      'Например: студент, работа в найме, предпринимательство, творческая деятельность.';

  @override
  String get occupationPlaceholder => 'Расскажите о своём занятии';

  @override
  String get familyQuestion => 'Расскажите немного о семье или близких людях';

  @override
  String get familyHint =>
      'Например: живёте ли вы один, есть ли партнёр, дети или важные отношения.';

  @override
  String get familyPlaceholder => 'Ваш социальный контекст';

  @override
  String get interestsQuestion => 'Какие у вас увлечения или интересы?';

  @override
  String get interestsHint =>
      'Искусство, спорт, технологии, путешествия или что-то совсем своё.';

  @override
  String get interestsPlaceholder => 'Ваши интересы';

  @override
  String get lifeContextQuestion => 'Что сейчас особенно важно в вашей жизни?';

  @override
  String get lifeContextHint =>
      'Можно рассказать о целях, трудностях, изменениях или поисках.';

  @override
  String get lifeContextPlaceholder => 'Текущий жизненный контекст';

  @override
  String get onboardingIntro =>
      'Чтобы лучше понимать контекст ваших снов, расскажите немного о себе.';

  @override
  String get onboardingGenderNote =>
      'Пол и возраст можно пропустить, если не хочется отвечать.';

  @override
  String get ageLabel => 'Возраст';

  @override
  String get onboardingFailed => 'Не удалось завершить онбординг';

  @override
  String ageYears(String age) {
    return '$age лет';
  }

  @override
  String get genderFemale => 'Женщина';

  @override
  String get genderMale => 'Мужчина';

  @override
  String get genderUnspecified => 'Предпочитает не указывать пол';

  @override
  String get mapRefresh => 'Обновить';

  @override
  String get mapRefreshing =>
      'Карта обновляется. Пока показываем предыдущую версию.';

  @override
  String mapAddMoreDreams(int count) {
    return 'Добавьте ещё $count снов, чтобы активировать карту.';
  }

  @override
  String get mapUnavailable => 'Карта пока недоступна.';

  @override
  String mapSymbolLabel(String name) {
    return 'Символ: $name';
  }

  @override
  String mapLastSeen(String date) {
    return 'Последнее появление: $date';
  }

  @override
  String mapOccurrences(int count, int dreams) {
    return '$count вхождений в $dreams снах';
  }

  @override
  String get relatedSymbols => 'Связанные символы';

  @override
  String get whereAppears => 'Где встречается';

  @override
  String get openLastDream => 'Открыть последний сон';

  @override
  String get emailLabel => 'Email';

  @override
  String get confirmPasswordLabel => 'Подтвердите пароль';

  @override
  String get passwordMismatch => 'Пароли не совпадают';

  @override
  String get passwordTooShort => 'Пароль должен быть не менее 8 символов';

  @override
  String get registerButton => 'Создать аккаунт';

  @override
  String get loginButton => 'Войти';

  @override
  String get alreadyHaveAccount => 'Уже есть аккаунт? Войти';

  @override
  String get noAccountYet => 'Нет аккаунта? Зарегистрироваться';

  @override
  String get verifyEmailTitle => 'Подтверждение email';

  @override
  String verifyEmailHint(String email) {
    return 'Введите 6-значный код, отправленный на $email';
  }

  @override
  String get verifyButton => 'Подтвердить';

  @override
  String get resendCode => 'Отправить код снова';

  @override
  String get invalidCode => 'Неверный или устаревший код';

  @override
  String get emailNotVerified => 'Email не подтверждён';

  @override
  String get createAccountSection => 'Создать аккаунт';

  @override
  String get signInToSave =>
      'Создайте аккаунт, чтобы сохранить сны и получить доступ с других устройств.';

  @override
  String get registrationFailed => 'Ошибка регистрации. Попробуйте ещё раз.';

  @override
  String get loginFailed => 'Неверный email или пароль.';

  @override
  String get logoutButton => 'Выйти';

  @override
  String get logoutConfirm => 'Выйти из аккаунта?';

  @override
  String get logoutConfirmMessage =>
      'Вы войдёте как гость. Ваши сны останутся на устройстве.';

  @override
  String get forgotPassword => 'Забыли пароль?';
}
