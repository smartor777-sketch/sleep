import { useCallback, useState } from 'react';
import Modal from './Modal';
import { api, ApiError, getDeviceId } from '../lib/api';
import { useApp } from '../lib/store';
import { t } from '../lib/i18n';
import { Send } from 'lucide-react';
import GoogleSignInButton from './GoogleSignInButton';

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function AuthModal({ open, onClose }: Props) {
  const lang = useApp((s) => s.lang);
  const refreshUser = useApp((s) => s.refreshUser);
  const refreshBilling = useApp((s) => s.refreshBilling);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  function reset() {
    setErr(null);
    setBusy(false);
  }

  const onGoogleCredential = useCallback(async (idToken: string) => {
    setErr(null); setBusy(true);
    const anonDevice = getDeviceId();
    try {
      await api.signInGoogle(idToken);
      try { await api.mergeAnonymous(anonDevice); } catch {}
      await refreshUser();
      refreshBilling().catch(() => {});
      onClose(); reset();
    } catch (e) {
      const ae = e as ApiError;
      setErr(ae.detail || ae.message || 'google_signin_failed');
    } finally {
      setBusy(false);
    }
  }, [onClose, refreshUser, refreshBilling]);

  return (
    <Modal open={open} onClose={() => { onClose(); reset(); }} title={t('profile.createAccount', lang)} size="sm" testId="auth-modal">
      <div className="space-y-4">
        <p className="text-sm muted-text text-center">
          {lang === 'ru'
            ? 'Войдите, чтобы сохранить сны и продолжить на любом устройстве.'
            : 'Sign in to keep your dreams safe and continue on any device.'}
        </p>

        {err && <div className="text-sm text-red-400 bg-red-500/10 rounded-xl px-3 py-2" data-testid="auth-error">{err}</div>}

        <div className="flex flex-col items-center gap-3 pt-1">
          <GoogleSignInButton onCredential={onGoogleCredential} locale={lang} disabled={busy} />

          <button
            type="button"
            disabled
            title={lang === 'ru' ? 'Скоро' : 'Coming soon'}
            className="btn-pill btn-soft !py-2 w-full max-w-[280px] justify-center cursor-not-allowed opacity-60"
            data-testid="auth-telegram-btn"
          >
            <Send className="w-4 h-4" />
            {lang === 'ru' ? 'Войти через Telegram' : 'Sign in with Telegram'}
            <span className="text-xs muted-text ml-1">({lang === 'ru' ? 'скоро' : 'soon'})</span>
          </button>
        </div>
      </div>
    </Modal>
  );
}
