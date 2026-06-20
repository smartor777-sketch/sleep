import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

// --- GOOGLE PLAY BILLING (disabled until re-enabled; see docs/WEB_SPEC.md) ---
// import 'package:in_app_purchase/in_app_purchase.dart';

import '../l10n/app_localizations.dart';
import '../providers/billing_provider.dart';
import '../utils/plans.dart';

class PaywallScreen extends StatelessWidget {
  const PaywallScreen({super.key});

  static Future<void> show(BuildContext context) {
    return Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const PaywallScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final billing = context.watch<BillingProvider>();

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.premiumTitle),
        centerTitle: true,
      ),
      body: billing.loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  // Header
                  Icon(Icons.auto_awesome, size: 64, color: theme.colorScheme.primary),
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
                  _FeatureRow(icon: Icons.all_inclusive, text: l10n.premiumFeature1),
                  const SizedBox(height: 12),
                  _FeatureRow(icon: Icons.speed, text: l10n.premiumFeature2),
                  const SizedBox(height: 12),
                  _FeatureRow(icon: Icons.hub, text: l10n.premiumFeature3),
                  const SizedBox(height: 32),

                  // --- GOOGLE PLAY BILLING (disabled until re-enabled; see docs/WEB_SPEC.md) ---
                  // Product cards, purchase and restore are disabled while the
                  // Google Play Billing integration is turned off. The plan
                  // tiers/limits still work; only the purchase flow is hidden.
                  // if (billing.products.isEmpty)
                  //   Padding(
                  //     padding: const EdgeInsets.symmetric(vertical: 24),
                  //     child: Text(
                  //       'Products loading...',
                  //       style: theme.textTheme.bodyMedium?.copyWith(
                  //         color: theme.colorScheme.onSurfaceVariant,
                  //       ),
                  //     ),
                  //   )
                  // else
                  //   ...billing.products.map((product) => _ProductCard(
                  //         product: product,
                  //         billing: billing,
                  //         l10n: l10n,
                  //       )),
                  //
                  // const SizedBox(height: 16),
                  //
                  // // Restore
                  // TextButton(
                  //   onPressed: billing.purchasing ? null : () => billing.restorePurchases(),
                  //   child: Text(l10n.premiumRestore),
                  // ),

                  // Pricing tiers — display only; buttons disabled until
                  // billing is wired up.
                  Builder(
                    builder: (context) {
                      final lang = Localizations.localeOf(context).languageCode;
                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          for (final p in plans) ...[
                            _PlanCard(plan: p, lang: lang),
                            const SizedBox(height: 10),
                          ],
                          const SizedBox(height: 6),
                          Text(
                            lang == 'ru'
                                ? 'Сначала 7 дней Pro бесплатно. После триала аккаунт переходит на Free, пока не оформите подписку.'
                                : 'Starts with a 7-day Pro trial. After the trial your account goes to Free until you subscribe.',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: theme.colorScheme.onSurfaceVariant,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ],
                      );
                    },
                  ),

                  // Placeholder shown while purchases are unavailable.
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    child: Text(
                      l10n.premiumComingSoon,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                      textAlign: TextAlign.center,
                    ),
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
        Expanded(
          child: Text(text, style: theme.textTheme.bodyLarge),
        ),
      ],
    );
  }
}

// --- GOOGLE PLAY BILLING (disabled until re-enabled; see docs/WEB_SPEC.md) ---
// class _ProductCard extends StatelessWidget {
//   const _ProductCard({
//     required this.product,
//     required this.billing,
//     required this.l10n,
//   });
//   final ProductDetails product;
//   final BillingProvider billing;
//   final AppLocalizations l10n;
//
//   String _label() {
//     if (product.id.contains('weekly')) return l10n.premiumWeekly;
//     if (product.id.contains('yearly')) return l10n.premiumYearly;
//     return l10n.premiumMonthly;
//   }
//
//   bool get _isYearly => product.id.contains('yearly');
//
//   @override
//   Widget build(BuildContext context) {
//     final theme = Theme.of(context);
//     return Card(
//       margin: const EdgeInsets.only(bottom: 12),
//       shape: RoundedRectangleBorder(
//         borderRadius: BorderRadius.circular(12),
//         side: _isYearly
//             ? BorderSide(color: theme.colorScheme.primary, width: 2)
//             : BorderSide.none,
//       ),
//       child: InkWell(
//         borderRadius: BorderRadius.circular(12),
//         onTap: billing.purchasing ? null : () => billing.buy(product),
//         child: Padding(
//           padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
//           child: Row(
//             children: [
//               Expanded(
//                 child: Column(
//                   crossAxisAlignment: CrossAxisAlignment.start,
//                   children: [
//                     Row(
//                       children: [
//                         Text(
//                           _label(),
//                           style: theme.textTheme.titleMedium?.copyWith(
//                             fontWeight: FontWeight.w600,
//                           ),
//                         ),
//                         if (_isYearly) ...[
//                           const SizedBox(width: 8),
//                           Container(
//                             padding: const EdgeInsets.symmetric(
//                               horizontal: 8,
//                               vertical: 2,
//                             ),
//                             decoration: BoxDecoration(
//                               color: theme.colorScheme.primaryContainer,
//                               borderRadius: BorderRadius.circular(8),
//                             ),
//                             child: Text(
//                               l10n.premiumYearlySave,
//                               style: theme.textTheme.labelSmall?.copyWith(
//                                 color: theme.colorScheme.onPrimaryContainer,
//                               ),
//                             ),
//                           ),
//                         ],
//                       ],
//                     ),
//                   ],
//                 ),
//               ),
//               Text(
//                 product.price,
//                 style: theme.textTheme.titleMedium?.copyWith(
//                   fontWeight: FontWeight.bold,
//                   color: theme.colorScheme.primary,
//                 ),
//               ),
//               if (billing.purchasing)
//                 const Padding(
//                   padding: EdgeInsets.only(left: 8),
//                   child: SizedBox(
//                     width: 16,
//                     height: 16,
//                     child: CircularProgressIndicator(strokeWidth: 2),
//                   ),
//                 ),
//             ],
//           ),
//         ),
//       ),
//     );
//   }
// }

class _PlanCard extends StatelessWidget {
  final Plan plan;
  final String lang;
  const _PlanCard({required this.plan, required this.lang});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final accent = theme.colorScheme.primary;
    final isBest = plan.highlight == PlanHighlight.best;
    final isPopular = plan.highlight == PlanHighlight.popular;

    return Stack(
      clipBehavior: Clip.none,
      children: [
        Container(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 14),
          decoration: BoxDecoration(
            color: theme.colorScheme.surfaceContainerHighest.withOpacity(0.4),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: isBest ? accent : theme.colorScheme.outlineVariant.withOpacity(0.4),
              width: isBest ? 2 : 1,
            ),
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      plan.periodLabel(lang),
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          formatPrice(plan.price, lang),
                          style: theme.textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        if (plan.months > 1) ...[
                          const SizedBox(width: 8),
                          Padding(
                            padding: const EdgeInsets.only(bottom: 4),
                            child: Text(
                              lang == 'ru'
                                  ? '${formatPrice(plan.perMonth, lang)}/мес'
                                  : '${formatPrice(plan.perMonth, lang)}/mo',
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: theme.colorScheme.onSurfaceVariant,
                              ),
                            ),
                          ),
                          if (plan.discountPct > 0) ...[
                            const SizedBox(width: 6),
                            Padding(
                              padding: const EdgeInsets.only(bottom: 4),
                              child: Text(
                                '−${plan.discountPct}%',
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: accent,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ],
                        ],
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              OutlinedButton(
                onPressed: null,
                child: Text(lang == 'ru' ? 'Скоро' : 'Soon'),
              ),
            ],
          ),
        ),
        if (isBest)
          Positioned(
            top: -8,
            left: 16,
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
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.6,
                ),
              ),
            ),
          ),
        if (isPopular)
          Positioned(
            top: -8,
            left: 16,
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
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.6,
                ),
              ),
            ),
          ),
      ],
    );
  }
}
