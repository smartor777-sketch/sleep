import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import 'config.dart';
import 'l10n/app_localizations.dart';
import 'models/user_me.dart';
import 'screens/main_chat_screen.dart';
import 'screens/onboarding_screen.dart';
import 'screens/startup_splash_screen.dart';
import 'providers/auth_provider.dart';
import 'providers/dreams_provider.dart';
import 'providers/profile_provider.dart';
import 'services/secure_storage_service.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

const String _appVersion = '0.3.2';

class _MyAppState extends State<MyApp> {
  bool isDarkMode = false;
  Color accentColor = Colors.deepPurple;
  Locale? _locale;
  double _textScale = 1.15;
  Future<void>? _bootstrap;
  final _settings = SecureStorageService();
  bool _updateChecked = false;

  void toggleTheme() {
    setState(() {
      isDarkMode = !isDarkMode;
    });
    _settings.setDarkMode(isDarkMode);
  }

  void setAccentColor(Color color) {
    setState(() {
      accentColor = color;
    });
    _settings.setAccentColor(color);
  }

  void setLocale(Locale locale) {
    setState(() {
      _locale = locale;
    });
  }

  void setTextScale(double value) {
    setState(() {
      _textScale = value;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProxyProvider<AuthProvider, DreamsProvider>(
          create: (context) => DreamsProvider(context.read<AuthProvider>()),
          update: (context, auth, previous) => previous ?? DreamsProvider(auth),
        ),
        ChangeNotifierProxyProvider<AuthProvider, ProfileProvider>(
          create: (context) => ProfileProvider(context.read<AuthProvider>()),
          update: (context, auth, previous) => previous ?? ProfileProvider(auth),
        ),
      ],
      child: MaterialApp(
        title: 'JungAI',
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        locale: _locale,
        builder: (context, child) {
          final media = MediaQuery.of(context);
          return MediaQuery(
            data: media.copyWith(textScaleFactor: _textScale),
            child: child ?? const SizedBox.shrink(),
          );
        },
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: accentColor,
            brightness: Brightness.light,
          ),
          switchTheme: SwitchThemeData(
            thumbColor: MaterialStateProperty.all(accentColor),
            trackColor: MaterialStateProperty.all(accentColor.withOpacity(0.3)),
          ),
          floatingActionButtonTheme: FloatingActionButtonThemeData(
            backgroundColor: accentColor,
          ),
        ),
        darkTheme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: accentColor,
            brightness: Brightness.dark,
          ),
          switchTheme: SwitchThemeData(
            thumbColor: MaterialStateProperty.all(accentColor),
            trackColor: MaterialStateProperty.all(accentColor.withOpacity(0.3)),
          ),
          floatingActionButtonTheme: FloatingActionButtonThemeData(
            backgroundColor: accentColor,
          ),
        ),
        themeMode: isDarkMode ? ThemeMode.dark : ThemeMode.light,
        home: Builder(
          builder: (context) {
            final auth = context.watch<AuthProvider>();
            _bootstrap ??= auth.bootstrap();
            if (auth.loading || (auth.user == null && auth.error == null)) {
              return const StartupSplashScreen();
            }
            if (auth.error != null) {
              return Scaffold(
                body: Center(child: Text(AppLocalizations.of(context)?.startupError ?? 'Startup error')),
              );
            }
            final user = auth.user;
            if (user == null) {
              return Scaffold(
                body: Center(child: Text(AppLocalizations.of(context)?.userLoadError ?? 'Failed to load user')),
              );
            }
            WidgetsBinding.instance.addPostFrameCallback((_) {
              _checkUpdate(context);
            });
            final needsOnboarding = !user.onboardingCompleted || (user.aboutMe?.trim().isEmpty ?? true);
            final mainScreen = MainChatScreen(
              isDarkMode: isDarkMode,
              toggleTheme: toggleTheme,
              accentColor: accentColor,
              setAccentColor: setAccentColor,
              setLocale: setLocale,
              textScale: _textScale,
              setTextScale: setTextScale,
            );
            if (!needsOnboarding) {
              return mainScreen;
            }
            return Stack(
              children: [
                mainScreen,
                OnboardingScreen(
                  onCompleted: () {
                    final current = auth.user;
                    if (current == null) return;
                    auth.updateUser(
                      UserMe(
                        id: current.id,
                        email: current.email,
                        isAnonymous: current.isAnonymous,
                        linkedProviders: current.linkedProviders,
                        aboutMe: current.aboutMe,
                        onboardingCompleted: true,
                      ),
                    );
                  },
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final dark = await _settings.getDarkMode();
    final color = await _settings.getAccentColor();
    if (!mounted) return;
    setState(() {
      isDarkMode = dark;
      if (color != null) accentColor = color;
    });
  }

  Future<void> _checkUpdate(BuildContext context) async {
    if (_updateChecked) return;
    _updateChecked = true;
    try {
      final response = await http.get(
        Uri.parse('$apiBaseUrl/api/v1/app/version'),
      ).timeout(const Duration(seconds: 5));
      if (response.statusCode != 200 || !mounted) return;
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final latest = data['version'] as String?;
      final url = data['download_url'] as String?;
      if (latest == null || url == null) return;
      if (_isNewer(latest, _appVersion)) {
        _showUpdateDialog(context, url);
      }
    } catch (_) {
      // Silent fail — don't block the app
    }
  }

  bool _isNewer(String remote, String local) {
    final r = remote.split('.').map(int.tryParse).toList();
    final l = local.split('.').map(int.tryParse).toList();
    for (var i = 0; i < r.length && i < l.length; i++) {
      if ((r[i] ?? 0) > (l[i] ?? 0)) return true;
      if ((r[i] ?? 0) < (l[i] ?? 0)) return false;
    }
    return r.length > l.length;
  }

  void _showUpdateDialog(BuildContext context, String url) {
    final l10n = AppLocalizations.of(context);
    if (l10n == null) return;
    showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(l10n.updateAvailable),
        content: Text(l10n.updateMessage),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: Text(l10n.later),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(dialogContext).pop();
              _launchUrl(url);
            },
            child: Text(l10n.updateNow),
          ),
        ],
      ),
    );
  }

  Future<void> _launchUrl(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }
}
