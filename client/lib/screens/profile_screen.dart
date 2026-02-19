import 'dart:io';

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';

import 'package:provider/provider.dart';

import '../l10n/app_localizations.dart';
import '../providers/auth_provider.dart';
import '../providers/profile_provider.dart';
import '../utils/snackbar.dart';

class ProfileScreen extends StatefulWidget {
  final bool isDarkMode;                 // текущий режим
  final VoidCallback toggleTheme;        // функция смены темы
  final Color accentColor;
  final Function(Color) setAccentColor;
  final Function(Locale) setLocale;
  final double textScale;
  final Function(double) setTextScale;

  const ProfileScreen({
    super.key,
    required this.isDarkMode,
    required this.toggleTheme,
    required this.accentColor,
    required this.setAccentColor,
    required this.setLocale,
    required this.textScale,
    required this.setTextScale,
  });

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  late bool _isDarkMode;
  late Color _accentColor;
  late TextEditingController _aboutController;
  String _aboutText = '';
  bool _linking = false;

  @override
  void initState() {
    super.initState();
    _isDarkMode = widget.isDarkMode;
    _accentColor = widget.accentColor;
    _aboutText = '';
    _aboutController = TextEditingController(text: _aboutText);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final auth = context.read<AuthProvider>();
      _aboutText = auth.user?.aboutMe ?? '';
      _aboutController.text = _aboutText;
      context.read<ProfileProvider>().loadStats();
      setState(() {});
    });
  }

  @override
  void didUpdateWidget(covariant ProfileScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.isDarkMode != widget.isDarkMode) {
      _isDarkMode = widget.isDarkMode;
    }
    if (oldWidget.accentColor != widget.accentColor) {
      _accentColor = widget.accentColor;
    }
    // user state handled by AuthProvider
  }

  @override
  void dispose() {
    _aboutController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final profile = context.watch<ProfileProvider>();
    final stats = profile.stats;
    final user = auth.user;
    if (profile.error != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _showError(_mapProfileError(profile.error));
        profile.clearError();
      });
    }

    return Scaffold(
      appBar: AppBar(title: Text(AppLocalizations.of(context)!.profileTitle)),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Email
            if (user != null && !(user.isAnonymous) && user.email != null) ...[
              Text(
                user.email!,
                style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 12),
            ],

            // About Me
            TextField(
              controller: _aboutController,
              minLines: 2,
              maxLines: 6,
              decoration: InputDecoration(
                labelText: AppLocalizations.of(context)!.aboutMeLabel,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide(
                    color: Theme.of(context).colorScheme.outline.withOpacity(0.5),
                    width: 2,
                  ),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide(
                    color: _accentColor,
                    width: 2,
                  ),
                ),
              ),
              onChanged: (value) {
                setState(() {
                  _aboutText = value;
                });
              },
            ),
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: _accentColor,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                onPressed: profile.loading
                    ? null
                    : () async {
                        final updated = await context.read<ProfileProvider>().saveAboutMe(_aboutText);
                        if (!mounted) return;
                        if (updated == null) {
                          showToast(context, AppLocalizations.of(context)!.profileSaveError, isError: true);
                        } else {
                          showToast(context, AppLocalizations.of(context)!.savedSuccess);
                        }
                      },
                child: profile.loading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : Text(AppLocalizations.of(context)!.save),
              ),
            ),
            const SizedBox(height: 32),

            // Статистика
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildStatCard(AppLocalizations.of(context)!.totalDreams, (stats?.totalDreams ?? 0).toString(), Colors.deepPurple),
                _buildStatCard(AppLocalizations.of(context)!.streak, (stats?.streakDays ?? 0).toString(), Colors.green),
              ],
            ),
            const SizedBox(height: 32),

            // График снов по дням
            Text(
              AppLocalizations.of(context)!.dreamsByWeekday,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            SizedBox(
              height: 200,
              child: Padding(
                padding: const EdgeInsets.only(top: 8),
                child: BarChart(
                  BarChartData(
                    alignment: BarChartAlignment.spaceAround,
                    maxY: ((stats?.dreamsByWeekday.values.isEmpty ?? true)
                            ? 1
                            : (stats?.dreamsByWeekday.values.reduce((a,b) => a>b?a:b) ?? 1))
                        .toDouble() + 1,
                    gridData: const FlGridData(show: false),
                    borderData: FlBorderData(show: false),
                    titlesData: FlTitlesData(
                      topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                      rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                      leftTitles: AxisTitles(
                        sideTitles: SideTitles(
                          showTitles: true,
                          reservedSize: 32,
                          interval: 1,
                          getTitlesWidget: (value, meta) {
                            if (value % 1 != 0) return const SizedBox.shrink();
                            return Text(value.toInt().toString());
                          },
                        ),
                      ),
                      bottomTitles: AxisTitles(
                        sideTitles: SideTitles(
                          showTitles: true,
                          getTitlesWidget: (value, meta) {
                            final days = (stats?.dreamsByWeekday.keys.toList() ??
                                ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']);
                            if (value.toInt() >= 0 && value.toInt() < days.length) {
                              return Text(days[value.toInt()]);
                            }
                            return const Text('');
                          },
                          reservedSize: 32,
                        ),
                      ),
                    ),
                    barGroups: (stats?.dreamsByWeekday.entries ??
                        {'Mon':0,'Tue':0,'Wed':0,'Thu':0,'Fri':0,'Sat':0,'Sun':0}.entries).mapIndexed((index, entry) {
                      return BarChartGroupData(
                        x: index,
                        barRods: [
                          BarChartRodData(
                            toY: entry.value.toDouble(),
                            color: _accentColor,
                            width: 18,
                          )
                        ],
                      );
                    }).toList(),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 24),
            Text(AppLocalizations.of(context)!.accentColorLabel, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                Colors.deepPurple,
                Colors.teal,
                Colors.orange,
                Colors.pink,
                Colors.lightBlue,
              ].map((color) {
                return GestureDetector(
                  onTap: () {
                    widget.setAccentColor(color);
                    setState(() {
                      _accentColor = color;
                    });
                  },
                  child: CircleAvatar(
                    backgroundColor: color,
                    radius: 20,
                    child: color == _accentColor
                        ? const Icon(Icons.check, color: Colors.white)
                        : null,
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 32),
            // Тёмная тема
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(AppLocalizations.of(context)!.darkThemeLabel, style: const TextStyle(fontSize: 16)),
                Switch(
                  value: _isDarkMode,
                  onChanged: (_) {
                    widget.toggleTheme();
                    setState(() {
                      _isDarkMode = !_isDarkMode;
                    });
                  },
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(AppLocalizations.of(context)!.fontSizeLabel, style: const TextStyle(fontSize: 16)),
                TextButton(
                  onPressed: () {
                    final next = _nextTextScale(widget.textScale);
                    widget.setTextScale(next);
                  },
                  child: Text(_fontScaleLabel(widget.textScale)),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(AppLocalizations.of(context)!.languageLabel, style: const TextStyle(fontSize: 16)),
                TextButton(
                  onPressed: () {
                    final current = Localizations.localeOf(context).languageCode;
                    final next = current == 'ru' ? const Locale('en') : const Locale('ru');
                    widget.setLocale(next);
                  },
                  child: Text(Localizations.localeOf(context).languageCode.toUpperCase()),
                ),
              ],
            ),
            const SizedBox(height: 24),
            _buildLinkSection(context),
          ],
        ),
      ),
    );
  }

  Widget _buildStatCard(String title, String value, Color color) {
    return Expanded(
      child: Card(
        elevation: 3,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Text(value, style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: color)),
              const SizedBox(height: 4),
              Text(title, style: const TextStyle(fontSize: 14)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLinkSection(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final isGuest = auth.user?.isAnonymous ?? true;
    final l10n = AppLocalizations.of(context)!;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (!isGuest) ...[
          Text(
            l10n.accountLinked,
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
        ],
        if (Platform.isIOS)
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _linking ? null : _linkWithApple,
              child: const Text('Sign in with Apple'),
            ),
          ),
        if (Platform.isAndroid)
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: _accentColor,
                foregroundColor: Colors.white,
              ),
              onPressed: _linking ? null : _linkWithGoogle,
              child: const Text('Continue with Google'),
            ),
          ),
      ],
    );
  }

  Future<void> _linkWithGoogle() async {
    setState(() => _linking = true);
    try {
      final googleSignIn = GoogleSignIn(scopes: ['email']);
      final account = await googleSignIn.signIn();
      final auth = await account?.authentication;
      final idToken = auth?.idToken;
      if (idToken == null) {
        _showError(AppLocalizations.of(context)!.googleTokenError);
        return;
      }
      final updated = await context.read<AuthProvider>().authService.linkProvider(
        provider: 'google',
        idToken: idToken,
      );
      context.read<AuthProvider>().updateUser(updated);
    } catch (e) {
      _handleLinkError(e);
    } finally {
      setState(() => _linking = false);
    }
  }

  Future<void> _linkWithApple() async {
    setState(() => _linking = true);
    try {
      final credential = await SignInWithApple.getAppleIDCredential(
        scopes: [AppleIDAuthorizationScopes.email, AppleIDAuthorizationScopes.fullName],
      );
      final idToken = credential.identityToken;
      if (idToken == null) {
        _showError(AppLocalizations.of(context)!.appleTokenError);
        return;
      }
      final updated = await context.read<AuthProvider>().authService.linkProvider(
        provider: 'apple',
        idToken: idToken,
      );
      context.read<AuthProvider>().updateUser(updated);
    } catch (e) {
      _handleLinkError(e);
    } finally {
      setState(() => _linking = false);
    }
  }

  void _handleLinkError(Object error) {
    final l10n = AppLocalizations.of(context)!;
    final message = error.toString().contains('identity_already_linked')
        ? l10n.identityAlreadyLinked
        : l10n.linkFailed;
    _showError(message);
  }

  String _mapProfileError(String? message) {
    final l10n = AppLocalizations.of(context)!;
    if (message == 'network_error') {
      return l10n.networkError;
    }
    return l10n.profileError;
  }

  void _showError(String message) {
    if (!mounted) return;
    showToast(context, message, isError: true);
  }

  double _nextTextScale(double current) {
    if (current < 1.1) return 1.15;
    if (current < 1.25) return 1.3;
    return 1.0;
  }

  String _fontScaleLabel(double current) {
    final l10n = AppLocalizations.of(context)!;
    if (current < 1.1) return l10n.fontSizeSmall;
    if (current < 1.25) return l10n.fontSizeMedium;
    return l10n.fontSizeLarge;
  }

}

// Extension для индексированной map
extension IterableExtensions<E> on Iterable<E> {
  Iterable<T> mapIndexed<T>(T Function(int index, E item) f) sync* {
    var i = 0;
    for (final e in this) {
      yield f(i++, e);
    }
  }
}
