import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../l10n/app_localizations.dart';
import '../providers/billing_provider.dart';
import '../utils/plans.dart';

class PaywallScreen extends StatefulWidget {
  const PaywallScreen({super.key});

  static Future<void> show(BuildContext context) {
    return Navigator.of(
      context,
    ).push(MaterialPageRoute(builder: (_) => const PaywallScreen()));
  }

  @override
  State<PaywallScreen> createState() => _PaywallScreenState();
}

class _PaywallScreenState extends State<PaywallScreen> {
  late PlanId _selected = plans
      .firstWhere(
        (p) => p.highlight == PlanHighlight.best,
        orElse: () => plans.last,
      )
      .id;
  String? _checkoutError;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final billing = context.watch<BillingProvider>();

    return Scaffold(
      appBar: AppBar(title: Text(l10n.premiumTitle), centerTitle: true),
      body: billing.loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  // Header
                  Icon(
                    Icons.auto_awesome,
                    size: 64,
                    color: theme.colorScheme.primary,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    l10n.premiumTitle,
                    style: theme.textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    l10n.premiumSubtitle,
                    style: theme.textTheme.bodyLarge?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 32),

                  // Features
                  _FeatureRow(
                    icon: Icons.all_inclusive,
                    text: l10n.premiumFeature1,
                  ),
                  const SizedBox(height: 12),
                  _FeatureRow(icon: Icons.speed, text: l10n.premiumFeature2),
                  const SizedBox(height: 12),
                  _FeatureRow(icon: Icons.hub, text: l10n.premiumFeature3),
                  const SizedBox(height: 32),

                  // Pricing tiers — 2×2 grid, radio-style. Subscribe button below.
                  Builder(
                    builder: (context) {
                      final lang = Localizations.localeOf(context).languageCode;
                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          for (int i = 0; i < plans.length; i += 2)
                            Padding(
                              padding: const EdgeInsets.only(bottom: 12),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  Expanded(
                                    child: _PlanCard(
                                      plan: plans[i],
                                      lang: lang,
                                      selected: _selected == plans[i].id,
                                      onTap: () => setState(
                                        () => _selected = plans[i].id,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  if (i + 1 < plans.length)
                                    Expanded(
                                      child: _PlanCard(
                                        plan: plans[i + 1],
                                        lang: lang,
                                        selected: _selected == plans[i + 1].id,
                                        onTap: () => setState(
                                          () => _selected = plans[i + 1].id,
                                        ),
                                      ),
                                    )
                                  else
                                    const Expanded(child: SizedBox.shrink()),
                                ],
                              ),
                            ),
                          const SizedBox(height: 8),
                          SizedBox(
                            width: double.infinity,
                            height: 52,
                            child: ElevatedButton(
                              style: ElevatedButton.styleFrom(
                                backgroundColor: theme.colorScheme.primary,
                                foregroundColor: Colors.white,
                                disabledBackgroundColor: theme
                                    .colorScheme
                                    .primary
                                    .withOpacity(0.5),
                                disabledForegroundColor: Colors.white,
                              ),
                              onPressed: billing.creatingPayment
                                  ? null
                                  : () => _startCheckout(context),
                              child: billing.creatingPayment
                                  ? const SizedBox(
                                      width: 22,
                                      height: 22,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        color: Colors.white,
                                      ),
                                    )
                                  : Text(
                                      lang == 'ru'
                                          ? 'Подписаться'
                                          : 'Subscribe',
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w600,
                                        fontSize: 16,
                                      ),
                                    ),
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            lang == 'ru'
                                ? 'Безопасная оплата через YooKassa.'
                                : 'Secure checkout via YooKassa.',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: theme.colorScheme.onSurfaceVariant,
                            ),
                            textAlign: TextAlign.center,
                          ),
                          if (_checkoutError != null) ...[
                            const SizedBox(height: 8),
                            Text(
                              _checkoutError!,
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: theme.colorScheme.error,
                              ),
                              textAlign: TextAlign.center,
                            ),
                          ],
                          const SizedBox(height: 16),
                          Text(
                            lang == 'ru'
                                ? 'Сначала 14 дней Pro бесплатно. После триала аккаунт переходит на Free, пока не оформите подписку.'
                                : 'Starts with a 14-day Pro trial. After the trial your account goes to Free until you subscribe.',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: theme.colorScheme.onSurfaceVariant,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ],
                      );
                    },
                  ),

                  if (billing.error != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 16),
                      child: Text(
                        billing.error!,
                        style: TextStyle(color: theme.colorScheme.error),
                        textAlign: TextAlign.center,
                      ),
                    ),
                ],
              ),
            ),
    );
  }

  Future<void> _startCheckout(BuildContext context) async {
    final lang = Localizations.localeOf(context).languageCode;
    final billing = context.read<BillingProvider>();
    final plan = plans.firstWhere((p) => p.id == _selected);

    setState(() => _checkoutError = null);
    try {
      final url = await billing.createPayment(plan.apiId);
      if (!mounted) return;
      await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _checkoutError = lang == 'ru'
            ? 'Не удалось создать платёж.'
            : 'Failed to create payment.';
      });
    }
  }
}

class _FeatureRow extends StatelessWidget {
  const _FeatureRow({required this.icon, required this.text});
  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      children: [
        Icon(icon, size: 24, color: theme.colorScheme.primary),
        const SizedBox(width: 12),
        Expanded(child: Text(text, style: theme.textTheme.bodyLarge)),
      ],
    );
  }
}

class _PlanCard extends StatelessWidget {
  final Plan plan;
  final String lang;
  final bool selected;
  final VoidCallback onTap;
  const _PlanCard({
    required this.plan,
    required this.lang,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final accent = theme.colorScheme.primary;
    final isBest = plan.highlight == PlanHighlight.best;
    final isPopular = plan.highlight == PlanHighlight.popular;
    final borderColor = selected
        ? accent
        : isBest
        ? accent
        : theme.colorScheme.outlineVariant.withOpacity(0.4);
    final borderWidth = selected || isBest ? 2.0 : 1.0;

    return Semantics(
      button: true,
      checked: selected,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(20),
            child: Container(
              padding: const EdgeInsets.fromLTRB(14, 14, 14, 14),
              decoration: BoxDecoration(
                color: selected
                    ? accent.withOpacity(0.10)
                    : theme.colorScheme.surfaceContainerHighest.withOpacity(
                        0.4,
                      ),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: borderColor, width: borderWidth),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      _Radio(selected: selected, accent: accent),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          plan.periodLabel(lang),
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    formatPrice(plan.price, lang),
                    style: theme.textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  if (plan.months > 1) ...[
                    const SizedBox(height: 2),
                    Wrap(
                      crossAxisAlignment: WrapCrossAlignment.center,
                      spacing: 6,
                      children: [
                        Text(
                          lang == 'ru'
                              ? '${formatPrice(plan.perMonth, lang)}/мес'
                              : '${formatPrice(plan.perMonth, lang)}/mo',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onSurfaceVariant,
                          ),
                        ),
                        if (plan.discountPct > 0)
                          Text(
                            '−${plan.discountPct}%',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: accent,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
          ),
          if (isBest)
            Positioned(
              top: -8,
              left: 12,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: accent,
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                  lang == 'ru' ? 'ВЫГОДА' : 'BEST',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 9,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.6,
                  ),
                ),
              ),
            ),
          if (isPopular)
            Positioned(
              top: -8,
              left: 12,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: theme.colorScheme.surfaceContainerHighest,
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                  lang == 'ru' ? 'ПОПУЛЯРНО' : 'POPULAR',
                  style: TextStyle(
                    color: theme.colorScheme.onSurfaceVariant,
                    fontSize: 9,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.6,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _Radio extends StatelessWidget {
  final bool selected;
  final Color accent;
  const _Radio({required this.selected, required this.accent});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      width: 18,
      height: 18,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        border: Border.all(
          color: selected ? accent : theme.colorScheme.outlineVariant,
          width: 2,
        ),
      ),
      child: Center(
        child: selected
            ? Container(
                width: 8,
                height: 8,
                decoration: BoxDecoration(
                  color: accent,
                  shape: BoxShape.circle,
                ),
              )
            : null,
      ),
    );
  }
}
