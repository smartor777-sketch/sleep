import 'package:flutter/material.dart';
import 'main_chat_screen.dart';
import '../models/user_profile.dart';

class LoginScreen extends StatefulWidget {
  final bool isDarkMode;
  final VoidCallback toggleTheme;
  final Color accentColor;
  final Function(Color) setAccentColor;

  const LoginScreen({
    super.key,
    required this.isDarkMode,
    required this.toggleTheme,
    required this.accentColor,
    required this.setAccentColor,
  });

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final FocusNode _emailFocus = FocusNode();
  final FocusNode _passwordFocus = FocusNode();
  bool _isLoading = false;
  String? _error;

  OutlineInputBorder _inputBorder(Color color) {
    return OutlineInputBorder(
      borderRadius: BorderRadius.circular(16),
      borderSide: BorderSide(color: color, width: 2),
    );
  }

  Future<void> _login() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    // Имитация запроса к backend
    await Future.delayed(const Duration(seconds: 1));

    if (_emailController.text.trim().isEmpty || _passwordController.text.trim().isEmpty) {
      setState(() {
        _error = 'Введите email и пароль';
        _isLoading = false;
      });
      return;
    }

    // Для MVP считаем, что любая комбинация верна
    setState(() {
      _isLoading = false;
    });

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => MainChatScreen(
          userProfile: UserProfile(email: _emailController.text),
          isDarkMode: widget.isDarkMode,
          toggleTheme: widget.toggleTheme,
          accentColor: widget.accentColor,
          setAccentColor: widget.setAccentColor,
        ),
      ),
    );
  }

  void _goToRegister() {
    // Для MVP просто показываем диалог (позже можно отдельный экран)
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Регистрация'),
        content: const Text('Регистрация пока недоступна.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Ок'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch, // растянуть по ширине
          children: [
            const SizedBox(height: 100), // для отступа сверху
            const Text(
              'JungAI',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 32),
            TextField(
              controller: _emailController,
              focusNode: _emailFocus,
              decoration: InputDecoration(
                labelText: 'Email',
                border: _inputBorder(
                  Theme.of(context).colorScheme.outline.withOpacity(0.5),
                ),
                focusedBorder: _inputBorder(widget.accentColor),
              ),
              keyboardType: TextInputType.emailAddress,
              textInputAction: TextInputAction.next,
              onSubmitted: (_) {
                FocusScope.of(context).requestFocus(_passwordFocus);
              },
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _passwordController,
              focusNode: _passwordFocus,
              decoration: InputDecoration(
                labelText: 'Пароль',
                border: _inputBorder(
                  Theme.of(context).colorScheme.outline.withOpacity(0.5),
                ),
                focusedBorder: _inputBorder(widget.accentColor),
              ),
              obscureText: true,
              textInputAction: TextInputAction.done,
            ),
            const SizedBox(height: 24),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Text(_error!, style: const TextStyle(color: Colors.red)),
              ),
            SizedBox(
              width: double.infinity,
              height: 48,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: widget.accentColor,
                  foregroundColor: Colors.white,
                  textStyle: const TextStyle(fontWeight: FontWeight.bold),
                ),
                onPressed: _isLoading ? null : _login,
                child: _isLoading
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text('Войти', style: TextStyle(color: Colors.white)),
              ),
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: _goToRegister,
              child: const Text('Создать аккаунт'),
            ),
          ],
        ),
      ),
    );
  }
}