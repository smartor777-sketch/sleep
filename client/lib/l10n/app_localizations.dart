import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_ru.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('ru'),
  ];

  /// No description provided for @startupError.
  ///
  /// In ru, this message translates to:
  /// **'Ошибка запуска'**
  String get startupError;

  /// No description provided for @userLoadError.
  ///
  /// In ru, this message translates to:
  /// **'Не удалось загрузить пользователя'**
  String get userLoadError;

  /// No description provided for @dreamSaveError.
  ///
  /// In ru, this message translates to:
  /// **'Не удалось сохранить сон'**
  String get dreamSaveError;

  /// No description provided for @dreamCopied.
  ///
  /// In ru, this message translates to:
  /// **'Сон скопирован'**
  String get dreamCopied;

  /// No description provided for @dreamDeleteError.
  ///
  /// In ru, this message translates to:
  /// **'Не удалось удалить сон'**
  String get dreamDeleteError;

  /// No description provided for @rateLimitError.
  ///
  /// In ru, this message translates to:
  /// **'Достигнут лимит 5 снов в день. Попробуйте позже.'**
  String get rateLimitError;

  /// No description provided for @networkError.
  ///
  /// In ru, this message translates to:
  /// **'Проблемы с сетью. Проверьте подключение.'**
  String get networkError;

  /// No description provided for @genericError.
  ///
  /// In ru, this message translates to:
  /// **'Ошибка запроса. Попробуйте ещё раз.'**
  String get genericError;

  /// No description provided for @searchHint.
  ///
  /// In ru, this message translates to:
  /// **'Поиск снов...'**
  String get searchHint;

  /// No description provided for @editDreamHint.
  ///
  /// In ru, this message translates to:
  /// **'Редактировать сон...'**
  String get editDreamHint;

  /// No description provided for @writeDreamHint.
  ///
  /// In ru, this message translates to:
  /// **'Напишите сон...'**
  String get writeDreamHint;

  /// No description provided for @emptyDreamsHint.
  ///
  /// In ru, this message translates to:
  /// **'Просто запиши свой Сон'**
  String get emptyDreamsHint;

  /// No description provided for @analysisFailed.
  ///
  /// In ru, this message translates to:
  /// **'Анализ не удался'**
  String get analysisFailed;

  /// No description provided for @analyzingLabel.
  ///
  /// In ru, this message translates to:
  /// **'Анализ...'**
  String get analyzingLabel;

  /// No description provided for @messageFailed.
  ///
  /// In ru, this message translates to:
  /// **'Ответ не получен'**
  String get messageFailed;

  /// No description provided for @dreamAnalysisTitle.
  ///
  /// In ru, this message translates to:
  /// **'Анализ сна'**
  String get dreamAnalysisTitle;

  /// No description provided for @writeMessageHint.
  ///
  /// In ru, this message translates to:
  /// **'Напишите сообщение...'**
  String get writeMessageHint;

  /// No description provided for @messageSendError.
  ///
  /// In ru, this message translates to:
  /// **'Не удалось отправить сообщение'**
  String get messageSendError;

  /// No description provided for @profileTitle.
  ///
  /// In ru, this message translates to:
  /// **'Профиль'**
  String get profileTitle;

  /// No description provided for @aboutMeLabel.
  ///
  /// In ru, this message translates to:
  /// **'Обо мне'**
  String get aboutMeLabel;

  /// No description provided for @profileSaveError.
  ///
  /// In ru, this message translates to:
  /// **'Не удалось сохранить профиль'**
  String get profileSaveError;

  /// No description provided for @totalDreams.
  ///
  /// In ru, this message translates to:
  /// **'Всего снов'**
  String get totalDreams;

  /// No description provided for @streak.
  ///
  /// In ru, this message translates to:
  /// **'Streak'**
  String get streak;

  /// No description provided for @avgTime.
  ///
  /// In ru, this message translates to:
  /// **'Среднее время'**
  String get avgTime;

  /// No description provided for @dreamsByWeekday.
  ///
  /// In ru, this message translates to:
  /// **'Сны по дням недели'**
  String get dreamsByWeekday;

  /// No description provided for @accentColorLabel.
  ///
  /// In ru, this message translates to:
  /// **'Выберите цвет акцента:'**
  String get accentColorLabel;

  /// No description provided for @darkThemeLabel.
  ///
  /// In ru, this message translates to:
  /// **'Темная тема'**
  String get darkThemeLabel;

  /// No description provided for @fontSizeLabel.
  ///
  /// In ru, this message translates to:
  /// **'Размер шрифта'**
  String get fontSizeLabel;

  /// No description provided for @fontSizeSmall.
  ///
  /// In ru, this message translates to:
  /// **'Маленький'**
  String get fontSizeSmall;

  /// No description provided for @fontSizeMedium.
  ///
  /// In ru, this message translates to:
  /// **'Средний'**
  String get fontSizeMedium;

  /// No description provided for @fontSizeLarge.
  ///
  /// In ru, this message translates to:
  /// **'Большой'**
  String get fontSizeLarge;

  /// No description provided for @languageLabel.
  ///
  /// In ru, this message translates to:
  /// **'Язык'**
  String get languageLabel;

  /// No description provided for @guest.
  ///
  /// In ru, this message translates to:
  /// **'Гость'**
  String get guest;

  /// No description provided for @accountLinked.
  ///
  /// In ru, this message translates to:
  /// **'Аккаунт привязан'**
  String get accountLinked;

  /// No description provided for @providers.
  ///
  /// In ru, this message translates to:
  /// **'Провайдеры'**
  String get providers;

  /// No description provided for @noProviders.
  ///
  /// In ru, this message translates to:
  /// **'Нет'**
  String get noProviders;

  /// No description provided for @googleTokenError.
  ///
  /// In ru, this message translates to:
  /// **'Не удалось получить токен Google'**
  String get googleTokenError;

  /// No description provided for @appleTokenError.
  ///
  /// In ru, this message translates to:
  /// **'Не удалось получить токен Apple'**
  String get appleTokenError;

  /// No description provided for @identityAlreadyLinked.
  ///
  /// In ru, this message translates to:
  /// **'Этот аккаунт уже привязан к другому профилю.'**
  String get identityAlreadyLinked;

  /// No description provided for @linkFailed.
  ///
  /// In ru, this message translates to:
  /// **'Не удалось подтвердить аккаунт. Попробуйте ещё раз.'**
  String get linkFailed;

  /// No description provided for @profileError.
  ///
  /// In ru, this message translates to:
  /// **'Ошибка профиля. Попробуйте ещё раз.'**
  String get profileError;

  /// No description provided for @editTitleLabel.
  ///
  /// In ru, this message translates to:
  /// **'Изменить название'**
  String get editTitleLabel;

  /// No description provided for @titleHint.
  ///
  /// In ru, this message translates to:
  /// **'Название'**
  String get titleHint;

  /// No description provided for @deleteDreamConfirm.
  ///
  /// In ru, this message translates to:
  /// **'Удалить этот сон?'**
  String get deleteDreamConfirm;

  /// No description provided for @cancel.
  ///
  /// In ru, this message translates to:
  /// **'Отмена'**
  String get cancel;

  /// No description provided for @enterCredentials.
  ///
  /// In ru, this message translates to:
  /// **'Введите email и пароль'**
  String get enterCredentials;

  /// No description provided for @registerTitle.
  ///
  /// In ru, this message translates to:
  /// **'Регистрация'**
  String get registerTitle;

  /// No description provided for @registerUnavailable.
  ///
  /// In ru, this message translates to:
  /// **'Регистрация пока недоступна.'**
  String get registerUnavailable;

  /// No description provided for @ok.
  ///
  /// In ru, this message translates to:
  /// **'Ок'**
  String get ok;

  /// No description provided for @passwordLabel.
  ///
  /// In ru, this message translates to:
  /// **'Пароль'**
  String get passwordLabel;

  /// No description provided for @signIn.
  ///
  /// In ru, this message translates to:
  /// **'Войти'**
  String get signIn;

  /// No description provided for @createAccount.
  ///
  /// In ru, this message translates to:
  /// **'Создать аккаунт'**
  String get createAccount;

  /// No description provided for @copy.
  ///
  /// In ru, this message translates to:
  /// **'Копировать'**
  String get copy;

  /// No description provided for @edit.
  ///
  /// In ru, this message translates to:
  /// **'Редактировать'**
  String get edit;

  /// No description provided for @delete.
  ///
  /// In ru, this message translates to:
  /// **'Удалить'**
  String get delete;

  /// No description provided for @analyze.
  ///
  /// In ru, this message translates to:
  /// **'Анализировать'**
  String get analyze;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'ru'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'ru':
      return AppLocalizationsRu();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
