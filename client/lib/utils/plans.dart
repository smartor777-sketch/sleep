// Pricing plans for InnerCore mobile. Mirrors frontend/src/lib/plans.ts —
// keep both in sync when editing prices. No real billing yet; the screen
// only renders these tiers with "Coming soon" buttons.

enum PlanId { monthly, quarter, half, yearly }

enum PlanHighlight { none, popular, best }

class PlanPrice {
  final int rub;
  final double usd;
  const PlanPrice({required this.rub, required this.usd});
}

class Plan {
  final PlanId id;
  final int months;
  final PlanPrice price;
  final PlanPrice perMonth;
  final int discountPct;
  final PlanHighlight highlight;
  const Plan({
    required this.id,
    required this.months,
    required this.price,
    required this.perMonth,
    required this.discountPct,
    required this.highlight,
  });

  String periodLabel(String lang) {
    if (lang == 'ru') {
      switch (months) {
        case 1: return '1 месяц';
        case 3: return '3 месяца';
        case 6: return '6 месяцев';
        default: return '12 месяцев';
      }
    }
    return months == 1 ? '1 month' : '$months months';
  }
}

const int _monthlyRub = 749;
const double _monthlyUsd = 10.0;

Plan _mk(PlanId id, int months, int rub, double usd, [PlanHighlight h = PlanHighlight.none]) {
  final fullRub = _monthlyRub * months;
  final discountPct = (((fullRub - rub) / fullRub) * 100).round();
  return Plan(
    id: id,
    months: months,
    price: PlanPrice(rub: rub, usd: usd),
    perMonth: PlanPrice(
      rub: (rub / months).round(),
      usd: ((usd / months) * 100).roundToDouble() / 100,
    ),
    discountPct: discountPct,
    highlight: h,
  );
}

final List<Plan> plans = [
  _mk(PlanId.monthly, 1, _monthlyRub, _monthlyUsd),
  _mk(PlanId.quarter, 3, 1899, 25, PlanHighlight.popular),
  _mk(PlanId.half, 6, 2999, 40),
  _mk(PlanId.yearly, 12, 5249, 70, PlanHighlight.best),
];

String formatPrice(PlanPrice p, String lang) {
  if (lang == 'ru') {
    // 1 234 ₽ format
    final s = p.rub.toString();
    final buf = StringBuffer();
    for (int i = 0; i < s.length; i++) {
      if (i > 0 && (s.length - i) % 3 == 0) buf.write(' ');
      buf.write(s[i]);
    }
    return '${buf.toString()} ₽';
  }
  final usd = p.usd == p.usd.truncateToDouble()
      ? p.usd.toInt().toString()
      : p.usd.toString();
  return '\$$usd';
}
