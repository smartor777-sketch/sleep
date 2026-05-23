import { useState } from 'react';
import Modal from './Modal';
import { useApp } from '../lib/store';
import { t } from '../lib/i18n';
import { api } from '../lib/api';
import { Moon, Sparkles, BookOpen } from 'lucide-react';

const STEPS = 3;

export default function OnboardingModal() {
  const open = useApp((s) => s.onboardingOpen);
  const close = useApp((s) => s.closeOnboarding);
  const refresh = useApp((s) => s.refreshUser);
  const lang = useApp((s) => s.lang);
  const user = useApp((s) => s.user);

  const [step, setStep] = useState(0);
  const [about, setAbout] = useState(user?.profile?.about_me || '');
  const [saving, setSaving] = useState(false);

  if (!open) return null;

  async function finish(skip = false) {
    setSaving(true);
    try {
      await api.updateMe({
        self_description: skip ? (about || ' ') : about,
        onboarding_completed: true,
      });
      await refresh();
      close();
      setStep(0);
    } catch {
      // soft-fail; still close
      close();
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal open={open} closable={false} size="md" testId="onboarding-modal">
      <div className="min-h-[420px] flex flex-col">
        {/* Progress dots */}
        <div className="flex gap-1.5 justify-center mb-6">
          {Array.from({ length: STEPS }).map((_, i) => (
            <span key={i}
              className="h-1.5 rounded-full transition-all"
              style={{
                width: i === step ? 28 : 8,
                background: i <= step ? 'rgb(var(--accent))' : 'rgba(255,255,255,0.15)',
              }}
            />
          ))}
        </div>

        {step === 0 && (
          <div className="text-center flex-1 flex flex-col items-center justify-center animate-fade-up">
            <div className="w-20 h-20 rounded-full flex items-center justify-center mb-5"
                 style={{ background: 'radial-gradient(circle at 30% 30%, #FA9042, #8885FF 80%)' }}>
              <Moon className="w-9 h-9 text-white" />
            </div>
            <h2 className="font-display text-3xl mb-3">{t('onboarding.title', lang)}</h2>
            <p className="muted-text max-w-md">{t('onboarding.sub', lang)}</p>
          </div>
        )}

        {step === 1 && (
          <div className="text-center flex-1 flex flex-col items-center justify-center animate-fade-up">
            <div className="w-20 h-20 rounded-full flex items-center justify-center mb-5"
                 style={{ background: 'rgba(var(--accent), 0.15)' }}>
              <BookOpen className="w-9 h-9 accent-text" />
            </div>
            <h2 className="font-display text-2xl mb-3">
              {lang === 'ru' ? 'Цикл самопознания' : 'A cycle of self-knowledge'}
            </h2>
            <p className="muted-text max-w-md">
              {lang === 'ru'
                ? 'Запишите сон — получите юнгианский анализ — поговорите о нём с Oneiros. Постепенно складывается карта вашего бессознательного.'
                : 'Write a dream — receive a Jungian reading — talk it through with Oneiros. Slowly a map of your unconscious takes shape.'}
            </p>
          </div>
        )}

        {step === 2 && (
          <div className="flex-1 flex flex-col animate-fade-up">
            <div className="text-center mb-4">
              <div className="w-16 h-16 rounded-full mx-auto flex items-center justify-center mb-3"
                   style={{ background: 'rgba(var(--accent), 0.15)' }}>
                <Sparkles className="w-7 h-7 accent-text" />
              </div>
              <h2 className="font-display text-2xl mb-2">{t('onboarding.aboutTitle', lang)}</h2>
              <p className="muted-text max-w-md mx-auto">{t('onboarding.aboutDesc', lang)}</p>
            </div>
            <textarea
              value={about}
              onChange={(e) => setAbout(e.target.value)}
              maxLength={1000}
              rows={5}
              placeholder={t('onboarding.aboutPlaceholder', lang)}
              className="input-base resize-none"
              data-testid="onboarding-about-input"
            />
            <div className="text-right text-xs muted-text mt-1">{about.length}/1000</div>
          </div>
        )}

        <div className="mt-6 flex items-center justify-between gap-3">
          <button
            onClick={() => (step === 0 ? finish(true) : finish(true))}
            className="btn-pill btn-ghost"
            disabled={saving}
            data-testid="onboarding-skip-btn"
          >
            {t('onboarding.skip', lang)}
          </button>
          {step < STEPS - 1 ? (
            <button
              onClick={() => setStep(step + 1)}
              className="btn-pill btn-primary"
              data-testid="onboarding-next-btn"
            >
              {t('onboarding.next', lang)}
            </button>
          ) : (
            <button
              onClick={() => finish(false)}
              className="btn-pill btn-primary"
              disabled={saving}
              data-testid="onboarding-finish-btn"
            >
              {t('onboarding.start', lang)}
            </button>
          )}
        </div>
      </div>
    </Modal>
  );
}
