import { useState } from 'react';
import Modal from './Modal';
import { api, ApiError, getDeviceId } from '../lib/api';
import { useApp } from '../lib/store';
import { t } from '../lib/i18n';
import { Loader2 } from 'lucide-react';

type Mode = 'register' | 'login' | 'verify' | 'forgot';

interface Props {
  open: boolean;
  onClose: () => void;
  initialMode?: Mode;
}

export default function AuthModal({ open, onClose, initialMode = 'register' }: Props) {
  const lang = useApp((s) => s.lang);
  const refreshUser = useApp((s) => s.refreshUser);
  const refreshBilling = useApp((s) => s.refreshBilling);
  const [mode, setMode] = useState<Mode>(initialMode);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  function reset() {
    setEmail(''); setPassword(''); setCode(''); setErr(null); setInfo(null); setBusy(false);
  }

  async function doRegister() {
    setErr(null); setBusy(true);
    const anonDevice = getDeviceId();
    try {
      await api.register({
        email, password,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
      });
      // tokens now belong to new user; merge anonymous data
      try { await api.mergeAnonymous(anonDevice); } catch {}
      await refreshUser();
      refreshBilling().catch(() => {});
      setInfo(t('auth.codeSent', lang) + ' ' + email);
      setMode('verify');
    } catch (e) {
      const ae = e as ApiError;
      setErr(ae.detail || ae.message);
    } finally {
      setBusy(false);
    }
  }

  async function doLogin() {
    setErr(null); setBusy(true);
    const anonDevice = getDeviceId();
    try {
      await api.login(email, password);
      try { await api.mergeAnonymous(anonDevice); } catch {}
      await refreshUser();
      refreshBilling().catch(() => {});
      onClose(); reset();
    } catch (e) {
      const ae = e as ApiError;
      setErr(ae.detail || ae.message || 'Login failed');
    } finally { setBusy(false); }
  }

  async function doVerify() {
    setErr(null); setBusy(true);
    try {
      await api.verifyEmailCode(email, code);
      await refreshUser();
      onClose(); reset();
    } catch (e) {
      const ae = e as ApiError;
      setErr(ae.detail || 'Invalid code');
    } finally { setBusy(false); }
  }

  async function doResend() {
    setErr(null); setBusy(true);
    try { await api.resendCode(email); setInfo(t('auth.codeSent', lang) + ' ' + email); }
    catch (e) { setErr((e as ApiError).detail || 'Error'); }
    finally { setBusy(false); }
  }

  async function doForgot() {
    setErr(null); setBusy(true);
    try { await api.forgotPassword(email); setInfo('OK'); }
    catch (e) { setErr((e as ApiError).detail || 'Error'); }
    finally { setBusy(false); }
  }

  const title =
    mode === 'register' ? t('auth.register', lang) :
    mode === 'login' ? t('auth.login', lang) :
    mode === 'verify' ? t('auth.confirmEmail', lang) :
    t('auth.forgot', lang);

  return (
    <Modal open={open} onClose={() => { onClose(); reset(); }} title={title} size="sm" testId="auth-modal">
      <div className="space-y-3">
        {err && <div className="text-sm text-red-400 bg-red-500/10 rounded-xl px-3 py-2" data-testid="auth-error">{err}</div>}
        {info && <div className="text-sm accent-text bg-white/5 rounded-xl px-3 py-2">{info}</div>}

        {(mode === 'register' || mode === 'login' || mode === 'forgot') && (
          <input
            type="email" placeholder="email@example.com" autoComplete="email"
            value={email} onChange={(e) => setEmail(e.target.value)}
            className="input-base" data-testid="auth-email-input"
          />
        )}
        {(mode === 'register' || mode === 'login') && (
          <input
            type="password" placeholder="••••••••" autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            value={password} onChange={(e) => setPassword(e.target.value)}
            className="input-base" data-testid="auth-password-input"
          />
        )}
        {mode === 'verify' && (
          <>
            <input
              inputMode="numeric" maxLength={6} placeholder="000000"
              value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
              className="input-base text-center tracking-[0.5em] text-lg" data-testid="auth-code-input"
            />
            <button onClick={doResend} className="text-sm accent-text underline-offset-4 hover:underline" disabled={busy}>
              {t('auth.resend', lang)}
            </button>
          </>
        )}

        <button
          onClick={
            mode === 'register' ? doRegister :
            mode === 'login' ? doLogin :
            mode === 'verify' ? doVerify : doForgot
          }
          disabled={busy || (mode !== 'verify' && !email) || (mode === 'verify' && code.length < 6)}
          className="btn-pill btn-primary w-full"
          data-testid="auth-submit-btn"
        >
          {busy && <Loader2 className="w-4 h-4 animate-spin" />}
          {mode === 'register' ? t('auth.register', lang) :
            mode === 'login' ? t('auth.login', lang) :
            mode === 'verify' ? t('auth.verify', lang) : t('common.tryAgain', lang)}
        </button>

        <div className="text-center text-sm muted-text flex flex-col gap-2 pt-2">
          {mode === 'register' && (
            <>
              <button className="hover:underline" onClick={() => { setMode('login'); setErr(null); }}>
                {t('profile.haveAccount', lang)}
              </button>
            </>
          )}
          {mode === 'login' && (
            <>
              <button className="hover:underline" onClick={() => { setMode('register'); setErr(null); }}>
                {t('profile.createAccount', lang)}
              </button>
              <button className="hover:underline" onClick={() => { setMode('forgot'); setErr(null); }}>
                {t('auth.forgot', lang)}
              </button>
            </>
          )}
          {mode === 'forgot' && (
            <button className="hover:underline" onClick={() => { setMode('login'); setErr(null); }}>
              {t('auth.login', lang)}
            </button>
          )}
        </div>
      </div>
    </Modal>
  );
}
