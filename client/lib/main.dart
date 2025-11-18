import 'package:flutter/material.dart';
import 'screens/login_screen.dart';

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

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'JungAI',
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
      home: LoginScreen(
        isDarkMode: isDarkMode,
        toggleTheme: toggleTheme,
        accentColor: accentColor,
        setAccentColor: setAccentColor,
      ),
    );
  }
}