// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Russian (`ru`).
class AppLocalizationsRu extends AppLocalizations {
  AppLocalizationsRu([String locale = 'ru']) : super(locale);

  @override
  String get startupError => 'Ошибка запуска';

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
}
