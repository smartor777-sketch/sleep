import { useCallback, useState } from 'react';
import Modal from './Modal';
import { api, ApiError, getDeviceId } from '../lib/api';
import { useApp } from '../lib/store';
import { t } from '../lib/i18n';
import { Loader2 } from 'lucide-react';

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function AuthModal({ open, onClose }: Props) {
  const lang = useApp((s) => s.lang);
  const refreshUser = useApp((s) => s.refreshUser);
  const refreshBilling = useApp((s) => s.refreshBilling);

  const [emailMode, setEmailMode] = useState<'login' | 'register'>('register');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [emailBusy, setEmailBusy] = useState(false);

  // Verification-code step shown after registration
  const [pendingVerify, setPendingVerify] = useState(false);
  const [code, setCode] = useState('');
  const [verifyBusy, setVerifyBusy] = useState(false);

  const [err, setErr] = useState<string | null>(null);

  function reset() {
    setEmailMode('register');
    setEmail('');
    setPassword('');
    setFirstName('');
    setEmailBusy(false);
    setPendingVerify(false);
    setCode('');
    setVerifyBusy(false);
    setErr(null);
  }

  async function finishAuth() {
    const anonDevice = getDeviceId();
    try { await api.mergeAnonymous(anonDevice); } catch {}
    await refreshUser();
    refreshBilling().catch(() => {});
    onClose(); reset();
  }

  const submitEmail = useCallback(async () => {
    if (emailBusy) return;
    setEmailBusy(true);
    setErr(null);
    try {
      if (emailMode === 'login') {
        await api.login(email.trim(), password);
        await finishAuth();
      } else {
        await api.register({
          email: email.trim(),
          password,
          first_name: firstName.trim() || undefined,
        });
        setPendingVerify(true);
      }
    } catch (e) {
      const ae = e as ApiError;
      setErr(ae.detail || ae.message || (emailMode === 'login' ? 'login_failed' : 'register_failed'));
    } finally {
      setEmailBusy(false);
    }
  }, [emailMode, email, password, firstName, emailBusy]);

  const submitCode = useCallback(async () => {
    if (verifyBusy) return;
    setVerifyBusy(true);
    setErr(null);
    try {
      await api.verifyEmailCode(email.trim(), code.trim());
      await finishAuth();
    } catch (e) {
      const ae = e as ApiError;
      setErr(ae.detail || ae.message || 'invalid_code');
    } finally {
      setVerifyBusy(false);
    }
  }, [code, email, verifyBusy]);

  const resendCode = useCallback(async () => {
    if (verifyBusy) return;
    setVerifyBusy(true);
    setErr(null);
    try {
      await api.resendCode(email.trim());
      setErr(null);
    } catch (e) {
      const ae = e as ApiError;
      setErr(ae.detail || ae.message || 'resend_failed');
    } finally {
      setVerifyBusy(false);
    }
  }, [email, verifyBusy]);

  return (
    <Modal open={open} onClose={() => { onClose(); reset(); }} title={t('profile.createAccount', lang)} size="sm" testId="auth-modal">
      <div className="space-y-4">
        <p className="text-sm muted-text text-center">
          {lang === 'ru'
            ? 'Войдите, чтобы сохранить сны и продолжить на любом устройстве.'
            : 'Sign in to keep your dreams safe and continue on any device.'}
        </p>

        {err && (
          <div className="text-sm text-red-400 bg-red-500/10 rounded-xl px-3 py-2" data-testid="auth-error">{err}</div>
        )}

        {!pendingVerify ? (
          <div className="flex flex-col gap-2">
            <div className="flex rounded-full bg-[var(--surface)] p-1 text-sm border border-[var(--line)]">
              {(['register', 'login'] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setEmailMode(mode)}
                  className={`flex-1 rounded-full py-1.5 font-medium transition-colors ${
                    emailMode === mode
                      ? 'bg-[var(--accent)] text-[var(--on-accent)] shadow-sm'
                      : 'text-[var(--muted)] hover:text-[var(--text)]'
                  }`}
                  data-testid={`email-mode-${mode}`}
                >
                  {lang === 'ru'
                    ? (mode === 'register' ? 'Регистрация' : 'Вход')
                    : (mode === 'register' ? 'Sign up' : 'Sign in')}
                </button>
              ))}
            </div>

            <form
              className="flex flex-col gap-2"
              onSubmit={(e) => { e.preventDefault(); submitEmail(); }}
            >
              {emailMode === 'register' && (
                <input
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder={lang === 'ru' ? 'Имя' : 'Name'}
                  className="rounded-xl bg-white/5 border border-white/10 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                  data-testid="email-first-name"
                />
              )}
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email"
                className="rounded-xl bg-white/5 border border-white/10 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                data-testid="email-field"
              />
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={lang === 'ru' ? 'Пароль (мин. 8 символов)' : 'Password (min 8 chars)'}
                className="rounded-xl bg-white/5 border border-white/10 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                data-testid="password-field"
              />
              <button
                type="submit"
                disabled={emailBusy}
                className="btn-pill btn-primary !py-2.5 w-full justify-center disabled:opacity-50"
                data-testid="email-submit"
              >
                {emailBusy ? <Loader2 className="w-5 h-5 animate-spin" /> : null}
                {lang === 'ru'
                  ? (emailMode === 'register' ? 'Создать аккаунт' : 'Войти')
                  : (emailMode === 'register' ? 'Create account' : 'Sign in')}
              </button>
            </form>
          </div>
        ) : (
          <form
            className="flex flex-col gap-2"
            onSubmit={(e) => { e.preventDefault(); submitCode(); }}
          >
            <p className="text-sm muted-text text-center">{t('auth.codeSent', lang)} <span className="accent-text">{email}</span></p>
            <input
              type="text"
              required
              inputMode="numeric"
              pattern="[0-9]{6}"
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
              placeholder={t('auth.code', lang)}
              className="rounded-xl bg-white/5 border border-white/10 px-4 py-2.5 text-sm text-center tracking-[0.5em] focus:outline-none focus:ring-2 focus:ring-accent"
              data-testid="code-field"
            />
            <button
              type="submit"
              disabled={verifyBusy}
              className="btn-pill btn-primary !py-2.5 w-full justify-center disabled:opacity-50"
              data-testid="verify-code-submit"
            >
              {verifyBusy ? <Loader2 className="w-5 h-5 animate-spin" /> : null}
              {t('auth.verify', lang)}
            </button>
            <button
              type="button"
              onClick={resendCode}
              disabled={verifyBusy}
              className="text-sm accent-text text-center disabled:opacity-50"
              data-testid="resend-code"
            >
              {t('auth.resend', lang)}
            </button>
          </form>
        )}
      </div>
    </Modal>
  );
}