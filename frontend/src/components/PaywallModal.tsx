import { useEffect, useState } from 'react';
import { useApp } from '../lib/store';
import { t } from '../lib/i18n';
import Modal from './Modal';
import { Infinity as InfIcon, MessageCircle, Map as MapIcon, BookHeart, Lock, Star, Sparkles } from 'lucide-react';
import { PLANS, PlanId, formatPrice } from '../lib/plans';

export default function PaywallModal() {
  const open = useApp((s) => s.paywallOpen);
  const close = useApp((s) => s.closePaywall);
  const reason = useApp((s) => s.paywallReason);
  const lang = useApp((s) => s.lang);
  const [selected, setSelected] = useState<PlanId>(
    PLANS.find((p) => p.highlight === 'best')?.id ?? PLANS[0].id
  );

  useEffect(() => {
    if (!open) {
      setSelected(PLANS.find((p) => p.highlight === 'best')?.id ?? PLANS[0].id);
    }
  }, [open]);

  const features = [
    { icon: InfIcon, label: t('paywall.feature.unlimited', lang) },
    { icon: MessageCircle, label: t('paywall.feature.chat', lang) },
    { icon: MapIcon, label: t('paywall.feature.map', lang) },
    { icon: BookHeart, label: t('paywall.feature.memory', lang) },
  ];

  function periodLabel(months: number): string {
    if (lang === 'ru') {
      if (months === 1) return '1 месяц';
      if (months === 3) return '3 месяца';
      if (months === 6) return '6 месяцев';
      return '12 месяцев';
    }
    return months === 1 ? '1 month' : `${months} months`;
  }

  function perMonthLabel(perMonth: { rub: number; usd: number }): string {
    const formatted = formatPrice(perMonth, lang);
    return lang === 'ru' ? `${formatted}/мес` : `${formatted}/mo`;
  }

  return (
    <Modal open={open} onClose={close} size="md" testId="paywall-modal" closable>
      <div className="text-center pt-2 pb-3">
        <img
          src="/icon-background.png"
          alt=""
          aria-hidden="true"
          className="mx-auto w-16 h-16 rounded-full object-cover mb-4"
        />
        <h2 className="font-display text-2xl mb-2">{t('paywall.title', lang)}</h2>
        <p className="muted-text max-w-md mx-auto text-sm">{t('paywall.sub', lang)}</p>
        {reason && (
          <div
            className="mt-3 inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm accent-text"
            style={{ background: 'rgba(var(--accent), 0.14)' }}
          >
            <Lock className="w-3.5 h-3.5" />
            {reason}
          </div>
        )}
      </div>

      <ul className="grid sm:grid-cols-2 gap-2 mt-1 mb-5 max-w-2xl mx-auto">
        {features.map((f, i) => (
          <li key={i} className="flex items-center gap-2.5 px-3 py-2 card-surface rounded-xl">
            <span className="w-7 h-7 rounded-full flex items-center justify-center shrink-0"
                  style={{ background: 'rgba(var(--accent), 0.15)' }}>
              <f.icon className="w-3.5 h-3.5 accent-text" />
            </span>
            <span className="text-sm">{f.label}</span>
          </li>
        ))}
      </ul>

      <div
        role="radiogroup"
        aria-label={lang === 'ru' ? 'Выбрать тариф' : 'Choose a plan'}
        className="grid grid-cols-2 gap-2 mb-4"
        data-testid="paywall-plans"
      >
        {PLANS.map((p) => {
          const isBest = p.highlight === 'best';
          const isPopular = p.highlight === 'popular';
          const isSelected = selected === p.id;
          return (
            <button
              type="button"
              role="radio"
              aria-checked={isSelected}
              key={p.id}
              data-testid={`plan-${p.id}`}
              onClick={() => setSelected(p.id)}
              className="relative card-surface rounded-2xl px-3 py-3.5 flex flex-col text-left transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1"
              style={{
                borderColor: isSelected
                  ? 'rgb(var(--accent))'
                  : isBest
                    ? 'rgba(var(--accent), 0.4)'
                    : undefined,
                borderWidth: isSelected || isBest ? 2 : undefined,
                background: isSelected ? 'rgba(var(--accent), 0.08)' : undefined,
              }}
            >
              {isBest && (
                <span className="absolute -top-2 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wide accent-bg text-white flex items-center gap-1">
                  <Star className="w-3 h-3" /> {lang === 'ru' ? 'выгода' : 'best'}
                </span>
              )}
              {isPopular && (
                <span className="absolute -top-2 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wide bg-white/10 muted-text flex items-center gap-1">
                  <Sparkles className="w-3 h-3" /> {lang === 'ru' ? 'популярно' : 'popular'}
                </span>
              )}

              <div className="flex items-start gap-2">
                <span
                  aria-hidden="true"
                  className="mt-0.5 w-4 h-4 rounded-full flex items-center justify-center shrink-0 border-2 transition-colors"
                  style={{
                    borderColor: isSelected ? 'rgb(var(--accent))' : 'rgba(var(--accent), 0.35)',
                  }}
                >
                  {isSelected && (
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{ background: 'rgb(var(--accent))' }}
                    />
                  )}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="text-xs muted-text mb-1">{periodLabel(p.months)}</div>
                  <div className="font-display text-xl leading-tight tabular-nums">
                    {formatPrice(p.price, lang)}
                  </div>
                  {p.months > 1 && (
                    <div className="text-[11px] muted-text tabular-nums mt-0.5">
                      {perMonthLabel(p.perMonth)}
                      {p.discountPct > 0 && (
                        <span className="ml-1 accent-text">−{p.discountPct}%</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      <div className="text-center muted-text text-xs mb-4 max-w-md mx-auto">
        {lang === 'ru'
          ? 'Сначала 7 дней Pro бесплатно. После триала аккаунт переходит на Free, пока вы не оформите подписку.'
          : 'Starts with a 7-day Pro trial. After the trial your account goes to Free until you subscribe.'}
      </div>

      <div className="flex flex-col items-center gap-2">
        <button
          type="button"
          disabled
          title={lang === 'ru' ? 'Скоро' : 'Coming soon'}
          className="btn-pill btn-primary px-8 w-full max-w-[280px] cursor-not-allowed opacity-70"
          data-testid="paywall-subscribe-btn"
        >
          {lang === 'ru' ? 'Подписаться' : 'Subscribe'}
        </button>
        <span className="muted-text text-[11px]">
          {lang === 'ru' ? 'Оплата скоро будет доступна' : 'Checkout coming soon'}
        </span>
        <button
          onClick={close}
          className="btn-pill btn-ghost px-6 mt-1"
          data-testid="paywall-close-btn"
        >
          {t('paywall.close', lang)}
        </button>
      </div>
    </Modal>
  );
}
