import { useState } from 'react';
import { Minus, Plus } from 'lucide-react';
import Modal from './Modal';
import { useApp } from '../lib/store';
import { t } from '../lib/i18n';
import { api } from '../lib/api';

const STEPS = 5;

type Gender = 'female' | 'male' | 'unknown' | null;

export default function OnboardingModal() {
  const open = useApp((s) => s.onboardingOpen);
  const close = useApp((s) => s.closeOnboarding);
  const refresh = useApp((s) => s.refreshUser);
  const lang = useApp((s) => s.lang);

  const [step, setStep] = useState(0);
  const [gender, setGender] = useState<Gender>(null);
  const [age, setAge] = useState<string>('');
  const [occupation, setOccupation] = useState('');
  const [family, setFamily] = useState('');
  const [interests, setInterests] = useState('');
  const [lifeContext, setLifeContext] = useState('');
  const [saving, setSaving] = useState(false);

  if (!open) return null;

  function genderLabel(g: Gender): string | null {
    if (g === 'female') return t('onboarding.genderFemale', lang);
    if (g === 'male') return t('onboarding.genderMale', lang);
    if (g === 'unknown') return t('onboarding.genderUnspecified', lang);
    return null;
  }

  function buildPayload(): string {
    const parts: string[] = [];
    const gl = genderLabel(gender);
    if (gl) parts.push(gl);
    if (age.trim()) {
      parts.push(lang === 'ru' ? `${age.trim()} лет` : `${age.trim()} years old`);
    }
    if (occupation.trim()) parts.push(occupation.trim());
    if (family.trim()) parts.push(family.trim());
    if (interests.trim()) parts.push(interests.trim());
    if (lifeContext.trim()) parts.push(lifeContext.trim());
    return parts.join('; ');
  }

  function clearCurrentStep() {
    if (step === 0) {
      setGender(null);
      setAge('');
    } else if (step === 1) {
      setOccupation('');
    } else if (step === 2) {
      setFamily('');
    } else if (step === 3) {
      setInterests('');
    } else if (step === 4) {
      setLifeContext('');
    }
  }

  async function finish() {
    setSaving(true);
    try {
      const payload = buildPayload();
      await api.updateMe({
        self_description: payload || ' ',
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

  function onSkip() {
    if (step === STEPS - 1) {
      finish();
      return;
    }
    clearCurrentStep();
    setStep((s) => s + 1);
  }

  function onNext() {
    if (step === STEPS - 1) {
      finish();
      return;
    }
    setStep((s) => s + 1);
  }

  const stepLabel = t('onboarding.step', lang)
    .replace('{step}', String(step + 1))
    .replace('{total}', String(STEPS));

  return (
    <Modal open={open} closable={false} size="md" testId="onboarding-modal">
      <div className="min-h-[460px] flex flex-col">
        <div className="mb-4">
          <h2 className="font-display text-2xl mb-1">{t('onboarding.title', lang)}</h2>
          <p className="muted-text text-xs">{stepLabel}</p>
        </div>

        <div className="flex gap-1.5 mb-5">
          {Array.from({ length: STEPS }).map((_, i) => (
            <span key={i}
              className="h-1.5 rounded-full transition-all flex-1"
              style={{
                background: i <= step ? 'rgb(var(--accent))' : 'rgba(255,255,255,0.15)',
              }}
            />
          ))}
        </div>

        <div className="flex-1">
          {step === 0 && (
            <div className="animate-fade-up">
              <p className="text-base mb-2">{t('onboarding.intro', lang)}</p>
              <p className="muted-text text-sm mb-5">{t('onboarding.genderNote', lang)}</p>
              <div className="flex gap-3 mb-5">
                {(['female', 'male', 'unknown'] as const).map((key) => (
                  <button
                    key={key}
                    onClick={() => setGender(gender === key ? null : key)}
                    className="flex-1 py-3 rounded-2xl border transition-all"
                    style={{
                      borderColor: gender === key ? 'rgb(var(--accent))' : 'rgba(255,255,255,0.18)',
                      borderWidth: gender === key ? 2 : 1,
                      background: gender === key ? 'rgba(var(--accent), 0.12)' : 'transparent',
                    }}
                    data-testid={`onboarding-gender-${key}`}
                  >
                    {genderLabel(key)}
                  </button>
                ))}
              </div>
              <div>
                <span className="text-sm muted-text mb-3 block">{t('onboarding.ageLabel', lang)}</span>
                <div className="flex items-center justify-center gap-4 bg-white/5 rounded-3xl py-5 px-4">
                  <button
                    type="button"
                    aria-label="decrease age"
                    onClick={() => {
                      const cur = parseInt(age, 10);
                      const next = Number.isFinite(cur) ? Math.max(12, cur - 1) : 25;
                      setAge(String(next));
                    }}
                    className="w-12 h-12 rounded-full btn-soft flex items-center justify-center shrink-0"
                    data-testid="onboarding-age-dec"
                  >
                    <Minus className="w-5 h-5" />
                  </button>
                  <input
                    type="number"
                    inputMode="numeric"
                    min={12}
                    max={90}
                    placeholder="—"
                    value={age}
                    onChange={(e) => {
                      const raw = e.target.value.replace(/\D/g, '').slice(0, 2);
                      if (raw === '') { setAge(''); return; }
                      const n = parseInt(raw, 10);
                      if (Number.isFinite(n)) setAge(String(Math.min(90, Math.max(12, n))));
                    }}
                    className="w-24 bg-transparent border-0 outline-none text-center font-display tabular-nums text-5xl focus:outline-none focus:ring-0"
                    data-testid="onboarding-age-input"
                  />
                  <button
                    type="button"
                    aria-label="increase age"
                    onClick={() => {
                      const cur = parseInt(age, 10);
                      const next = Number.isFinite(cur) ? Math.min(90, cur + 1) : 25;
                      setAge(String(next));
                    }}
                    className="w-12 h-12 rounded-full btn-soft flex items-center justify-center shrink-0"
                    data-testid="onboarding-age-inc"
                  >
                    <Plus className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {step === 1 && (
            <TextStep
              title={t('onboarding.occupationQuestion', lang)}
              hint={t('onboarding.occupationHint', lang)}
              placeholder={t('onboarding.occupationPlaceholder', lang)}
              value={occupation}
              onChange={setOccupation}
              testId="onboarding-occupation"
            />
          )}

          {step === 2 && (
            <TextStep
              title={t('onboarding.familyQuestion', lang)}
              hint={t('onboarding.familyHint', lang)}
              placeholder={t('onboarding.familyPlaceholder', lang)}
              value={family}
              onChange={setFamily}
              testId="onboarding-family"
            />
          )}

          {step === 3 && (
            <TextStep
              title={t('onboarding.interestsQuestion', lang)}
              hint={t('onboarding.interestsHint', lang)}
              placeholder={t('onboarding.interestsPlaceholder', lang)}
              value={interests}
              onChange={setInterests}
              testId="onboarding-interests"
            />
          )}

          {step === 4 && (
            <TextStep
              title={t('onboarding.lifeContextQuestion', lang)}
              hint={t('onboarding.lifeContextHint', lang)}
              placeholder={t('onboarding.lifeContextPlaceholder', lang)}
              value={lifeContext}
              onChange={setLifeContext}
              rows={6}
              testId="onboarding-life-context"
            />
          )}
        </div>

        <div className="mt-6 flex items-center justify-between gap-3">
          <button
            onClick={onSkip}
            className="btn-pill btn-ghost"
            disabled={saving}
            data-testid="onboarding-skip-btn"
          >
            {t('onboarding.skip', lang)}
          </button>
          <button
            onClick={onNext}
            className="btn-pill btn-primary"
            disabled={saving}
            data-testid={step === STEPS - 1 ? 'onboarding-finish-btn' : 'onboarding-next-btn'}
          >
            {step === STEPS - 1 ? t('onboarding.start', lang) : t('onboarding.next', lang)}
          </button>
        </div>
      </div>
    </Modal>
  );
}

interface TextStepProps {
  title: string;
  hint: string;
  placeholder: string;
  value: string;
  onChange: (v: string) => void;
  rows?: number;
  testId: string;
}

function TextStep({ title, hint, placeholder, value, onChange, rows = 4, testId }: TextStepProps) {
  return (
    <div className="animate-fade-up">
      <h3 className="text-lg font-medium mb-2">{title}</h3>
      <p className="muted-text text-sm mb-4">{hint}</p>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        maxLength={1000}
        placeholder={placeholder}
        className="input-base w-full resize-none"
        data-testid={`${testId}-input`}
      />
      <div className="text-right text-xs muted-text mt-1">{value.length}/1000</div>
    </div>
  );
}
