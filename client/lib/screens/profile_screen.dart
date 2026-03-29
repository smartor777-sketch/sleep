import 'dart:io';

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';

import 'package:provider/provider.dart';

import '../l10n/app_localizations.dart';
import '../providers/auth_provider.dart';
import '../providers/billing_provider.dart';
import '../providers/profile_provider.dart';
import '../utils/snackbar.dart';
import 'email_login_screen.dart';
import 'email_register_screen.dart';
import 'paywall_screen.dart';
import 'verify_email_screen.dart';

class ProfileScreen extends StatefulWidget {
  final bool isDarkMode; // текущий режим
  final VoidCallback toggleTheme; // функция смены темы
  final Color accentColor;
  final Function(Color) setAccentColor;
  final Function(Locale) setLocale;
  final double textScale;
  final Function(double) setTextScale;
  final bool embedded;

  const ProfileScreen({
    super.key,
    required this.isDarkMode,
    required this.toggleTheme,
    required this.accentColor,
    required this.setAccentColor,
    required this.setLocale,
    required this.textScale,
    required this.setTextScale,
    this.embedded = false,
  });

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

const _archetypePieColors = [
  Color(0xFF7E57C2), // deep purple
  Color(0xFF26A69A), // teal
  Color(0xFFEF5350), // red
  Color(0xFFFF7043), // deep orange
  Color(0xFF42A5F5), // blue
  Color(0xFFAB47BC), // purple
  Color(0xFF66BB6A), // green
  Color(0xFFFFA726), // orange
  Color(0xFF8D6E63), // brown
  Color(0xFF78909C), // blue grey
];

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

    final content = SingleChildScrollView(
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
                borderSide: BorderSide(color: _accentColor, width: 2),
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
                      final updated = await context
                          .read<ProfileProvider>()
                          .saveAboutMe(_aboutText);
                      if (!mounted) return;
                      if (updated == null) {
                        showToast(
                          context,
                          AppLocalizations.of(context)!.profileSaveError,
                          isError: true,
                        );
                      } else {
                        showToast(
                          context,
                          AppLocalizations.of(context)!.savedSuccess,
                        );
                      }
                    },
              child: profile.loading
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : Text(AppLocalizations.of(context)!.save),
            ),
          ),
          const SizedBox(height: 32),

          // Статистика
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildStatCard(
                AppLocalizations.of(context)!.totalDreams,
                (stats?.totalDreams ?? 0).toString(),
                Colors.deepPurple,
              ),
              _buildStatCard(
                AppLocalizations.of(context)!.streak,
                (stats?.streakDays ?? 0).toString(),
                Colors.green,
              ),
            ],
          ),
          const SizedBox(height: 32),

          // График снов по последним 14 дням
          Text(
            AppLocalizations.of(context)!.dreamsLast14Days,
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 200,
            child: Padding(
              padding: const EdgeInsets.only(top: 8),
              child: BarChart(
                BarChartData(
                  minY: 0,
                  alignment: BarChartAlignment.spaceAround,
                  maxY: () {
                    final counts =
                        stats?.dreamsLast14Days.map((e) => e.count).toList() ??
                        [];
                    final maxCount = counts.isEmpty
                        ? 0
                        : counts.reduce((a, b) => a > b ? a : b);
                    return (maxCount < 3 ? 3 : maxCount + 1).toDouble();
                  }(),
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    horizontalInterval: 1,
                    getDrawingHorizontalLine: (value) => FlLine(
                      color: Theme.of(
                        context,
                      ).colorScheme.outline.withOpacity(0.2),
                      strokeWidth: 1,
                    ),
                  ),
                  borderData: FlBorderData(show: false),
                  titlesData: FlTitlesData(
                    topTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    rightTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 32,
                        interval: 1,
                        getTitlesWidget: (value, meta) {
                          if (value % 1 != 0) return const SizedBox.shrink();
                          if (value < 0) return const SizedBox.shrink();
                          return Text(
                            value.toInt().toString(),
                            style: const TextStyle(fontSize: 11),
                          );
                        },
                      ),
                    ),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: (value, meta) {
                          final days = stats?.dreamsLast14Days ?? [];
                          final index = value.toInt();
                          if (index >= 0 && index < days.length) {
                            final label = days[index].date;
                            final shouldShow =
                                index == 0 ||
                                index == days.length - 1 ||
                                index.isEven;
                            if (!shouldShow) {
                              return const SizedBox.shrink();
                            }
                            return SideTitleWidget(
                              meta: meta,
                              space: 6,
                              child: Text(
                                label.substring(8, 10),
                                style: const TextStyle(fontSize: 10),
                              ),
                            );
                          }
                          return const SizedBox.shrink();
                        },
                        reservedSize: 24,
                      ),
                    ),
                  ),
                  barGroups: (stats?.dreamsLast14Days ?? []).mapIndexed((
                    index,
                    entry,
                  ) {
                    return BarChartGroupData(
                      x: index,
                      barRods: [
                        BarChartRodData(
                          toY: entry.count.toDouble(),
                          color: _accentColor,
                          width: 10,
                        ),
                      ],
                    );
                  }).toList(),
                ),
              ),
            ),
          ),
          const SizedBox(height: 20),
          if ((stats?.archetypesTop.isNotEmpty ?? false)) ...[
            Text(
              AppLocalizations.of(context)!.archetypes,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            SizedBox(
              height: 200,
              child: PieChart(
                PieChartData(
                  sectionsSpace: 2,
                  centerSpaceRadius: 40,
                  sections: stats!.archetypesTop.mapIndexed((index, item) {
                    final total = stats.archetypesTop.fold<int>(
                      0, (sum, e) => sum + e.count);
                    final percent = total == 0
                        ? 0.0
                        : item.count / total * 100;
                    return PieChartSectionData(
                      value: item.count.toDouble(),
                      title: '${percent.round()}%',
                      titleStyle: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                      radius: 50,
                      color: _archetypePieColors[
                          index % _archetypePieColors.length],
                    );
                  }).toList(),
                ),
              ),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 12,
              runSpacing: 6,
              children: stats.archetypesTop.mapIndexed((index, item) {
                final color = _archetypePieColors[
                    index % _archetypePieColors.length];
                return Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 12,
                      height: 12,
                      decoration: BoxDecoration(
                        color: color,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 4),
                    Text(
                      '${item.name} (${item.count})',
                      style: const TextStyle(fontSize: 13),
                    ),
                  ],
                );
              }).toList(),
            ),
          ],
          const SizedBox(height: 24),
          Text(
            AppLocalizations.of(context)!.accentColorLabel,
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children:
                [
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
              Text(
                AppLocalizations.of(context)!.darkThemeLabel,
                style: const TextStyle(fontSize: 16),
              ),
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
              Text(
                AppLocalizations.of(context)!.fontSizeLabel,
                style: const TextStyle(fontSize: 16),
              ),
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
              Text(
                AppLocalizations.of(context)!.languageLabel,
                style: const TextStyle(fontSize: 16),
              ),
              TextButton(
                onPressed: () {
                  final current = Localizations.localeOf(context).languageCode;
                  final next = current == 'ru'
                      ? const Locale('en')
                      : const Locale('ru');
                  widget.setLocale(next);
                },
                child: Text(
                  Localizations.localeOf(context).languageCode.toUpperCase(),
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          _buildSubscriptionSection(context),
          const SizedBox(height: 24),
          _buildLinkSection(context),
        ],
      ),
    );

    if (widget.embedded) {
      return Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Text(
                AppLocalizations.of(context)!.profileTitle,
                style: Theme.of(context).textTheme.titleLarge,
              ),
            ),
          ),
          Expanded(child: content),
        ],
      );
    }

    return Scaffold(
      appBar: AppBar(title: Text(AppLocalizations.of(context)!.profileTitle)),
      body: content,
    );
  }

  Widget _buildStatCard(String title, String value, Color color) {
    return Expanded(
      child: Card(
        elevation: 3,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: Column(
            children: [
              Text(
                value,
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
              const SizedBox(height: 2),
              Text(title, style: const TextStyle(fontSize: 14)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSubscriptionSection(BuildContext context) {
    final billing = context.watch<BillingProvider>();
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final user = context.read<AuthProvider>().user;

    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  billing.hasFullAccess ? Icons.workspace_premium : Icons.star_border,
                  color: billing.hasFullAccess
                      ? Colors.amber
                      : theme.colorScheme.onSurfaceVariant,
                ),
                const SizedBox(width: 8),
                Text(
                  billing.hasFullAccess ? l10n.premiumActive : l10n.freeAccount,
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (billing.status?.isTrial == true && billing.status!.trialDaysLeft > 0)
              Text(l10n.premiumTrialDaysLeft(billing.status!.trialDaysLeft)),
            if (billing.status?.isPro == true && user?.subType == 'pro')
              Text(l10n.manageSubscription,
                  style: TextStyle(color: theme.colorScheme.onSurfaceVariant)),
            if (billing.isFree) ...[
              if (billing.analysesLeft != null)
                Text(l10n.analysesLeftThisWeek(billing.analysesLeft!)),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () => PaywallScreen.show(context),
                  icon: const Icon(Icons.auto_awesome),
                  label: Text(l10n.upgradeToPro),
                ),
              ),
            ],
          ],
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
        if (isGuest) ...[
          Text(
            l10n.createAccountSection,
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Text(
            l10n.signInToSave,
            style: const TextStyle(fontSize: 14),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const EmailRegisterScreen()),
              ),
              child: Text(l10n.createAccount),
            ),
          ),
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const EmailLoginScreen()),
              ),
              child: Text(l10n.signIn),
            ),
          ),
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: _linking ? null : _signInWithGoogle,
              icon: const Icon(Icons.login),
              label: const Text('Sign in with Google'),
            ),
          ),
        ] else ...[
          if (auth.user?.email != null && !(auth.user!.emailVerified)) ...[
            const SizedBox(height: 8),
            OutlinedButton(
              onPressed: () => Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => VerifyEmailScreen(email: auth.user!.email!),
                ),
              ),
              child: Text(l10n.emailNotVerified),
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
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: () => _confirmLogout(context),
              child: Text(l10n.logoutButton),
            ),
          ),
        ],
      ],
    );
  }

  Future<void> _signInWithGoogle() async {
    setState(() => _linking = true);
    try {
      await context.read<AuthProvider>().signInWithGoogle();
    } catch (e) {
      if (!mounted) return;
      final msg = e.toString();
      if (!msg.contains('cancelled')) {
        showToast(context, AppLocalizations.of(context)!.linkFailed, isError: true);
      }
    } finally {
      if (mounted) setState(() => _linking = false);
    }
  }

  Future<void> _confirmLogout(BuildContext context) async {
    final auth = context.read<AuthProvider>(); // захватываем до async
    final l10n = AppLocalizations.of(context)!;
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(l10n.logoutConfirm),
        content: Text(l10n.logoutConfirmMessage),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text(l10n.cancel),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: Text(l10n.logoutButton),
          ),
        ],
      ),
    );
    if (confirm == true) {
      await auth.logout();
    }
  }

  Future<void> _linkWithApple() async {
    setState(() => _linking = true);
    try {
      final credential = await SignInWithApple.getAppleIDCredential(
        scopes: [
          AppleIDAuthorizationScopes.email,
          AppleIDAuthorizationScopes.fullName,
        ],
      );
      final idToken = credential.identityToken;
      if (idToken == null) {
        _showError(AppLocalizations.of(context)!.appleTokenError);
        return;
      }
      final updated = await context
          .read<AuthProvider>()
          .authService
          .linkProvider(provider: 'apple', idToken: idToken);
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
