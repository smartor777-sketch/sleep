// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get startupError => 'Startup error';

  @override
  String get userLoadError => 'Failed to load user';

  @override
  String get dreamSaveError => 'Failed to save dream';

  @override
  String get dreamCopied => 'Dream copied';

  @override
  String get dreamDeleteError => 'Failed to delete dream';

  @override
  String get rateLimitError =>
      'Daily limit of 5 dreams reached. Try again later.';

  @override
  String get networkError => 'Network issue. Check your connection.';

  @override
  String get genericError => 'Request error. Please try again.';

  @override
  String get searchHint => 'Search dreams...';

  @override
  String get editDreamHint => 'Edit dream...';

  @override
  String get writeDreamHint => 'Write a dream...';

  @override
  String get emptyDreamsHint => 'Just write your dream';

  @override
  String get analysisFailed => 'Analysis failed';

  @override
  String get analyzingLabel => 'Analyzing...';

  @override
  String get messageFailed => 'No response received';

  @override
  String get dreamAnalysisTitle => 'Dream analysis';

  @override
  String get writeMessageHint => 'Write a message...';

  @override
  String get messageSendError => 'Failed to send message';

  @override
  String get profileTitle => 'Profile';

  @override
  String get aboutMeLabel => 'About me';

  @override
  String get profileSaveError => 'Failed to save profile';

  @override
  String get totalDreams => 'Total dreams';

  @override
  String get streak => 'Streak';

  @override
  String get avgTime => 'Avg time';

  @override
  String get dreamsByWeekday => 'Dreams by weekday';

  @override
  String get accentColorLabel => 'Choose accent color:';

  @override
  String get darkThemeLabel => 'Dark theme';

  @override
  String get fontSizeLabel => 'Font size';

  @override
  String get fontSizeSmall => 'Small';

  @override
  String get fontSizeMedium => 'Medium';

  @override
  String get fontSizeLarge => 'Large';

  @override
  String get languageLabel => 'Language';

  @override
  String get guest => 'Guest';

  @override
  String get accountLinked => 'Account linked';

  @override
  String get providers => 'Providers';

  @override
  String get noProviders => 'None';

  @override
  String get googleTokenError => 'Failed to get Google token';

  @override
  String get appleTokenError => 'Failed to get Apple token';

  @override
  String get identityAlreadyLinked =>
      'This account is already linked to another profile.';

  @override
  String get linkFailed => 'Failed to verify account. Please try again.';

  @override
  String get profileError => 'Profile error. Please try again.';

  @override
  String get editTitleLabel => 'Edit title';

  @override
  String get titleHint => 'Title';

  @override
  String get deleteDreamConfirm => 'Delete this dream?';

  @override
  String get cancel => 'Cancel';

  @override
  String get enterCredentials => 'Enter email and password';

  @override
  String get registerTitle => 'Registration';

  @override
  String get registerUnavailable => 'Registration is not yet available.';

  @override
  String get ok => 'OK';

  @override
  String get passwordLabel => 'Password';

  @override
  String get signIn => 'Sign in';

  @override
  String get createAccount => 'Create account';

  @override
  String get copy => 'Copy';

  @override
  String get edit => 'Edit';

  @override
  String get delete => 'Delete';

  @override
  String get analyze => 'Analyze';
}
