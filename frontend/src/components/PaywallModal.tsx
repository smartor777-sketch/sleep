import { useApp } from '../lib/store';
import { t } from '../lib/i18n';
import Modal from './Modal';
import { Sparkles, Infinity as InfIcon, MessageCircle, Map as MapIcon, BookHeart, Lock } from 'lucide-react';

export default function PaywallModal() {
  const open = useApp((s) => s.paywallOpen);
  const close = useApp((s) => s.closePaywall);
  const reason = useApp((s) => s.paywallReason);
  const lang = useApp((s) => s.lang);

  const features = [
    { icon: InfIcon, label: t('paywall.feature.unlimited', lang) },
    { icon: MessageCircle, label: t('paywall.feature.chat', lang) },
    { icon: MapIcon, label: t('paywall.feature.map', lang) },
    { icon: BookHeart, label: t('paywall.feature.memory', lang) },
  ];

  return (
    <Modal open={open} onClose={close} size="md" testId="paywall-modal" closable>
      <div className="text-center pt-2 pb-4">
        <div
          className="mx-auto w-20 h-20 rounded-full flex items-center justify-center mb-5"
          style={{ background: 'radial-gradient(circle at 30% 30%, #FA9042, #8885FF 75%)' }}
        >
          <Sparkles className="w-8 h-8 text-white" />
        </div>
        <h2 className="font-display text-2xl mb-2">{t('paywall.title', lang)}</h2>
        <p className="muted-text max-w-md mx-auto">{t('paywall.sub', lang)}</p>
        {reason && (
          <div className="mt-3 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/15 text-amber-300 text-sm">
            <Lock className="w-3.5 h-3.5" />
            {reason}
          </div>
        )}
      </div>

      <ul className="space-y-3 mt-2 mb-6 max-w-md mx-auto">
        {features.map((f, i) => (
          <li key={i} className="flex items-center gap-3 px-4 py-3 card-surface rounded-2xl">
            <span className="w-9 h-9 rounded-full flex items-center justify-center"
                  style={{ background: 'rgba(var(--accent), 0.15)' }}>
              <f.icon className="w-4 h-4 accent-text" />
            </span>
            <span>{f.label}</span>
          </li>
        ))}
      </ul>

      <div className="text-center muted-text text-sm mb-4">{t('paywall.soon', lang)}</div>
      <div className="flex justify-center">
        <button onClick={close} className="btn-pill btn-primary px-8" data-testid="paywall-close-btn">
          {t('paywall.close', lang)}
        </button>
      </div>
    </Modal>
  );
}
