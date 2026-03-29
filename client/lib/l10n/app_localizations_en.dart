// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get startupError => 'Could not connect to server';

  @override
  String get retry => 'Retry';

  @override
  String get downloadLatest => 'Download latest version';

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
  String get listeningLabel => 'Recording...';

  @override
  String get recordingWarning => 'Recording for over a minute';

  @override
  String get partialTranscription => 'Some parts could not be recognized';

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
  String get retryAnalysis => 'Retry analysis';

  @override
  String get editDate => 'Change date';

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
  String get dreamsLast14Days => 'Dreams over 14 days';

  @override
  String get archetypes => 'Archetypes';

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

  @override
  String get save => 'Save';

  @override
  String get savedSuccess => 'Saved';

  @override
  String get updateAvailable => 'Update available';

  @override
  String get updateMessage =>
      'A new version of the app is available. Update for the best experience.';

  @override
  String get updateNow => 'Update';

  @override
  String get later => 'Later';

  @override
  String get dreamChat => 'Dream chat';

  @override
  String get dreamChatHint =>
      'Select a dream in the grid to open its analysis and chat.';

  @override
  String get onboardingTitle => 'Let\'s get to know each other';

  @override
  String onboardingStep(int step, int total) {
    return 'Step $step of $total';
  }

  @override
  String get skip => 'Skip';

  @override
  String get finish => 'Finish';

  @override
  String get next => 'Next';

  @override
  String get occupationQuestion => 'What do you do?';

  @override
  String get occupationHint =>
      'For example: student, employment, entrepreneurship, creative work.';

  @override
  String get occupationPlaceholder => 'Tell about your occupation';

  @override
  String get familyQuestion => 'Tell about family or close people';

  @override
  String get familyHint =>
      'For example: do you live alone, have a partner, children or important relationships.';

  @override
  String get familyPlaceholder => 'Your social context';

  @override
  String get interestsQuestion => 'What are your hobbies or interests?';

  @override
  String get interestsHint =>
      'Art, sports, technology, travel or something unique.';

  @override
  String get interestsPlaceholder => 'Your interests';

  @override
  String get lifeContextQuestion =>
      'What is especially important in your life now?';

  @override
  String get lifeContextHint =>
      'You can talk about goals, difficulties, changes or searches.';

  @override
  String get lifeContextPlaceholder => 'Current life context';

  @override
  String get onboardingIntro =>
      'To better understand the context of your dreams, tell us about yourself.';

  @override
  String get onboardingGenderNote =>
      'Gender and age can be skipped if you don\'t want to answer.';

  @override
  String get ageLabel => 'Age';

  @override
  String get onboardingFailed => 'Failed to complete onboarding';

  @override
  String ageYears(String age) {
    return '$age years old';
  }

  @override
  String get genderFemale => 'Female';

  @override
  String get genderMale => 'Male';

  @override
  String get genderUnspecified => 'Prefers not to specify gender';

  @override
  String get mapRefresh => 'Refresh';

  @override
  String get mapRefreshing => 'Map is being updated. Showing previous version.';

  @override
  String mapAddMoreDreams(int count) {
    return 'Add $count more dreams to activate the map.';
  }

  @override
  String get mapUnavailable => 'Map is not available yet.';

  @override
  String mapSymbolLabel(String name) {
    return 'Symbol: $name';
  }

  @override
  String mapLastSeen(String date) {
    return 'Last seen: $date';
  }

  @override
  String mapOccurrences(int count, int dreams) {
    return '$count occurrences in $dreams dreams';
  }

  @override
  String get relatedSymbols => 'Related symbols';

  @override
  String get whereAppears => 'Where it appears';

  @override
  String get openLastDream => 'Open last dream';

  @override
  String get emailLabel => 'Email';

  @override
  String get confirmPasswordLabel => 'Confirm password';

  @override
  String get passwordMismatch => 'Passwords do not match';

  @override
  String get passwordTooShort => 'Password must be at least 8 characters';

  @override
  String get registerButton => 'Create account';

  @override
  String get loginButton => 'Sign in';

  @override
  String get alreadyHaveAccount => 'Already have an account? Sign in';

  @override
  String get noAccountYet => 'No account? Register';

  @override
  String get verifyEmailTitle => 'Verify email';

  @override
  String verifyEmailHint(String email) {
    return 'Enter the 6-digit code sent to $email';
  }

  @override
  String get verifyButton => 'Verify';

  @override
  String get resendCode => 'Resend code';

  @override
  String get invalidCode => 'Invalid or expired code';

  @override
  String get emailNotVerified => 'Email not verified';

  @override
  String get createAccountSection => 'Create account';

  @override
  String get signInToSave =>
      'Create an account to save your dreams and access them from other devices.';

  @override
  String get registrationFailed => 'Registration failed. Try again.';

  @override
  String get loginFailed => 'Incorrect email or password.';

  @override
  String get logoutButton => 'Sign out';

  @override
  String get logoutConfirm => 'Sign out?';

  @override
  String get logoutConfirmMessage =>
      'You will be signed in as a guest. Your dreams will remain on this device.';

  @override
  String get forgotPassword => 'Forgot password?';

  @override
  String get premiumTitle => 'InnerCore Pro';

  @override
  String get premiumSubtitle => 'Unlock the full potential of dream analysis';

  @override
  String get premiumFeature1 => 'Unlimited dream analyses';

  @override
  String get premiumFeature2 => 'Priority AI processing';

  @override
  String get premiumFeature3 => 'Advanced dream map';

  @override
  String get premiumWeekly => 'Weekly';

  @override
  String get premiumMonthly => 'Monthly';

  @override
  String get premiumYearly => 'Yearly';

  @override
  String get premiumYearlySave => 'Save 40%';

  @override
  String get premiumSubscribe => 'Subscribe';

  @override
  String get premiumRestore => 'Restore purchases';

  @override
  String get premiumActive => 'Pro active';

  @override
  String premiumExpiresAt(String date) {
    return 'Expires: $date';
  }

  @override
  String premiumTrialDaysLeft(int days) {
    return '$days trial days left';
  }

  @override
  String analysesLeftThisWeek(int count) {
    return '$count analyses left this week';
  }

  @override
  String get analysisLimitReached =>
      'Weekly analysis limit reached. Upgrade to Pro for unlimited access.';

  @override
  String get upgradeToPro => 'Upgrade to Pro';

  @override
  String get freeAccount => 'Free';

  @override
  String get manageSubscription => 'Manage subscription';
}
