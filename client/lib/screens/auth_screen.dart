import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../l10n/app_localizations.dart';
import '../providers/auth_provider.dart';
import '../services/auth_service.dart';
import '../utils/snackbar.dart';

/// Sign-in screen: Google + Telegram. No email/password — those are
/// removed on web too. Telegram uses the bot deep-link flow: backend
/// hands us a `https://t.me/<bot>?start=<token>`, we open it, the bot
/// fires /auth/telegram/confirm, we poll for status, and on completion
/// the AuthProvider has the new user + tokens.
class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  bool _googleBusy = false;
  bool _tgPreparing = false;
  bool _tgWaiting = false;
  String? _error;

  TelegramInitResult? _tgInit;
  Timer? _pollTimer;

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Future<void> _signInGoogle() async {
    setState(() {
      _googleBusy = true;
      _error = null;
    });
    try {
      await context.read<AuthProvider>().signInWithGoogle();
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _googleBusy = false);
    }
  }

  Future<void> _signInTelegram() async {
    setState(() {
      _tgPreparing = true;
      _error = null;
    });
    final auth = context.read<AuthProvider>();
    try {
      final init = await auth.startTelegramAuth();
      _tgInit = init;
      final uri = Uri.parse(init.deeplink);
      final launched = await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (!launched) {
        if (!mounted) return;
        setState(() {
          _error = AppLocalizations.of(context)!.telegramOpenFailed;
          _tgPreparing = false;
        });
        return;
      }
      if (!mounted) return;
      setState(() {
        _tgPreparing = false;
        _tgWaiting = true;
      });
      _startPolling(init.authToken);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _tgPreparing = false;
      });
    }
  }

  void _startPolling(String token) {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(seconds: 2), (timer) async {
      if (!mounted) {
        timer.cancel();
        return;
      }
      try {
        final status = await context.read<AuthProvider>().pollTelegramAuth(token);
        if (status == 'completed') {
          timer.cancel();
          if (!mounted) return;
          Navigator.of(context).pop(true);
        } else if (status == 'expired') {
          timer.cancel();
          if (!mounted) return;
          setState(() {
            _tgWaiting = false;
            _tgInit = null;
            _error = AppLocalizations.of(context)!.telegramSessionExpired;
          });
        }
      } catch (_) {
        // transient — keep polling
      }
    });
  }

  Future<void> _reopenTelegram() async {
    final init = _tgInit;
    if (init == null) return;
    final ok = await launchUrl(Uri.parse(init.deeplink), mode: LaunchMode.externalApplication);
    if (!ok && mounted) {
      showToast(context, AppLocalizations.of(context)!.telegramOpenFailed, isError: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final accent = theme.colorScheme.primary;

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.signIn),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 24),
              Text(
                l10n.signInHelloTitle,
                style: theme.textTheme.headlineSmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),
              Text(
                l10n.signInWhyHint,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurface.withOpacity(0.65),
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),
              if (_error != null)
                Container(
                  margin: const EdgeInsets.only(bottom: 16),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  decoration: BoxDecoration(
                    color: Colors.red.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    _error!,
                    style: const TextStyle(color: Colors.red),
                  ),
                ),
              if (_tgWaiting)
                Container(
                  margin: const EdgeInsets.only(bottom: 16),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  decoration: BoxDecoration(
                    color: accent.withOpacity(0.10),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2, color: accent),
                      ),
                      const SizedBox(width: 12),
                      Expanded(child: Text(l10n.telegramWaiting)),
                    ],
                  ),
                ),
              SizedBox(
                height: 52,
                child: OutlinedButton.icon(
                  onPressed: (_googleBusy || _tgWaiting) ? null : _signInGoogle,
                  icon: _googleBusy
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.account_circle_outlined),
                  label: Text(l10n.signInWithGoogle),
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                height: 52,
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: accent,
                    foregroundColor: Colors.white,
                  ),
                  onPressed: (_tgPreparing || _tgWaiting || _googleBusy)
                      ? null
                      : _signInTelegram,
                  icon: _tgPreparing
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Icon(Icons.send),
                  label: Text(
                    _tgWaiting
                        ? l10n.telegramReopen
                        : l10n.signInWithTelegram,
                    style: const TextStyle(color: Colors.white),
                  ),
                ),
              ),
              if (_tgWaiting) ...[
                const SizedBox(height: 8),
                TextButton(
                  onPressed: _reopenTelegram,
                  child: Text(l10n.telegramReopen),
                ),
              ],
              const Spacer(),
              Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Text(
                  l10n.signInDisclaimer,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurface.withOpacity(0.45),
                  ),
                  textAlign: TextAlign.center,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
