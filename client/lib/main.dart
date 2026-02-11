import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'l10n/app_localizations.dart';
import 'models/user_me.dart';
import 'screens/main_chat_screen.dart';
import 'providers/auth_provider.dart';
import 'providers/dreams_provider.dart';
import 'providers/profile_provider.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  bool isDarkMode = false;
  Color accentColor = Colors.deepPurple;
  Locale? _locale;
  double _textScale = 1.0;
  Future<void>? _bootstrap;

  void toggleTheme() {
    setState(() {
      isDarkMode = !isDarkMode;
    });
  }

  void setAccentColor(Color color) {
    setState(() {
      accentColor = color;
    });
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
              return const Scaffold(
                body: Center(child: CircularProgressIndicator()),
              );
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
            return MainChatScreen(
              isDarkMode: isDarkMode,
              toggleTheme: toggleTheme,
              accentColor: accentColor,
              setAccentColor: setAccentColor,
              setLocale: setLocale,
              textScale: _textScale,
              setTextScale: setTextScale,
            );
          },
        ),
      ),
    );
  }

  @override
  void initState() {
    super.initState();
  }
}
