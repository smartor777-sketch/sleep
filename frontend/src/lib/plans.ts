// Pricing plans for the InnerCore web app. Mirror this list in
// client/lib/utils/plans.dart and backend/services/billing_service.py.

export type PlanId = 'monthly' | 'quarter' | 'half' | 'yearly';

export interface PlanPrice {
  rub: number;
  usd: number;
}

export interface Plan {
  id: PlanId;
  months: number;
  price: PlanPrice;
  /** Percentage discount vs paying 12 × monthly for the same span. */
  discountPct: number;
  /** Effective per-month price (rounded). */
  perMonth: PlanPrice;
  /** Highlight on the card (Best Value etc.). */
  highlight?: 'best' | 'popular';
}

const MONTHLY_RUB = 749;
const MONTHLY_USD = 10;

function plan(
  id: PlanId,
  months: number,
  rub: number,
  usd: number,
  highlight?: 'best' | 'popular',
): Plan {
  const fullRub = MONTHLY_RUB * months;
  const fullUsd = MONTHLY_USD * months;
  const discountPct = Math.round(((fullRub - rub) / fullRub) * 100);
  return {
    id,
    months,
    price: { rub, usd },
    discountPct,
    perMonth: {
      rub: Math.round(rub / months),
      usd: Math.round((usd / months) * 100) / 100,
    },
    highlight,
  };
}

export const PLANS: Plan[] = [
  plan('monthly', 1, MONTHLY_RUB, MONTHLY_USD),
  plan('quarter', 3, 1899, 25, 'popular'),
  plan('half', 6, 2999, 40),
  plan('yearly', 12, 5249, 70, 'best'),
];

export function formatPrice(p: PlanPrice, lang: 'ru' | 'en'): string {
  if (lang === 'ru') return `${p.rub.toLocaleString('ru-RU')} ₽`;
  return `$${p.usd}`;
}
