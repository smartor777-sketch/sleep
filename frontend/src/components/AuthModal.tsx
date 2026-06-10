import { useCallback, useEffect, useRef, useState } from 'react';
import Modal from './Modal';
import { api, ApiError, getDeviceId, setTokens } from '../lib/api';
import { useApp } from '../lib/store';
import { t } from '../lib/i18n';
import { Loader2, Send } from 'lucide-react';
import GoogleSignInButton from './GoogleSignInButton';

interface Props {
  open: boolean;
  onClose: () => void;
}

type TgState =
  | { kind: 'idle' }
  | { kind: 'waiting'; token: string; deeplink: string }
  | { kind: 'done' }
  | { kind: 'expired' };

export default function AuthModal({ open, onClose }: Props) {
  const lang = useApp((s) => s.lang);
  const refreshUser = useApp((s) => s.refreshUser);
  const refreshBilling = useApp((s) => s.refreshBilling);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [tg, setTg] = useState<TgState>({ kind: 'idle' });
  const pollRef = useRef<number | null>(null);

  function reset() {
    setErr(null);
    setBusy(false);
    setTg({ kind: 'idle' });
    if (pollRef.current) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }

  useEffect(() => () => {
    if (pollRef.current) window.clearInterval(pollRef.current);
  }, []);

  useEffect(() => {
    if (!open) reset();
  }, [open]);

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

  const onTelegramClick = useCallback(async () => {
    setErr(null); setBusy(true);
    const anonDevice = getDeviceId();
    try {
      const { auth_token, deeplink } = await api.telegramInit();
      setTg({ kind: 'waiting', token: auth_token, deeplink });
      // open the bot — popup-friendly: try opening in a new tab right after user click
      window.open(deeplink, '_blank', 'noopener,noreferrer');

      pollRef.current = window.setInterval(async () => {
        try {
          const r = await api.telegramStatus(auth_token);
          if (r.status === 'completed' && r.access_token && r.refresh_token) {
            if (pollRef.current) {
              window.clearInterval(pollRef.current);
              pollRef.current = null;
            }
            setTokens(r.access_token, r.refresh_token);
            try { await api.mergeAnonymous(anonDevice); } catch {}
            await refreshUser();
            refreshBilling().catch(() => {});
            setTg({ kind: 'done' });
            onClose(); reset();
          } else if (r.status === 'expired') {
            if (pollRef.current) {
              window.clearInterval(pollRef.current);
              pollRef.current = null;
            }
            setTg({ kind: 'expired' });
          }
        } catch {
          /* silent: keep polling */
        }
      }, 2000);
    } catch (e) {
      const ae = e as ApiError;
      setErr(ae.detail || ae.message || 'telegram_init_failed');
    } finally {
      setBusy(false);
    }
  }, [onClose, refreshUser, refreshBilling]);

  const tgWaiting = tg.kind === 'waiting';
  const tgExpired = tg.kind === 'expired';

  return (
    <Modal open={open} onClose={() => { onClose(); reset(); }} title={t('profile.createAccount', lang)} size="sm" testId="auth-modal">
      <div className="space-y-4">
        <p className="text-sm muted-text text-center">
          {lang === 'ru'
            ? 'Войдите, чтобы сохранить сны и продолжить на любом устройстве.'
            : 'Sign in to keep your dreams safe and continue on any device.'}
        </p>

        {err && <div className="text-sm text-red-400 bg-red-500/10 rounded-xl px-3 py-2" data-testid="auth-error">{err}</div>}

        {tgWaiting && (
          <div className="text-sm accent-text bg-white/5 rounded-xl px-3 py-3 flex items-center gap-2" data-testid="tg-waiting">
            <Loader2 className="w-4 h-4 animate-spin shrink-0" />
            <span>
              {lang === 'ru'
                ? 'Открой Telegram и нажми «Start» — мы тебя сразу залогиним.'
                : 'Open Telegram and tap Start — we will sign you in.'}
            </span>
          </div>
        )}

        {tgExpired && (
          <div className="text-sm text-red-400 bg-red-500/10 rounded-xl px-3 py-2">
            {lang === 'ru'
              ? 'Время сессии истекло. Нажми «Войти через Telegram» ещё раз.'
              : 'Session expired. Tap "Sign in with Telegram" again.'}
          </div>
        )}

        <div className="flex flex-col items-center gap-3 pt-1">
          <GoogleSignInButton onCredential={onGoogleCredential} locale={lang} disabled={busy || tgWaiting} />

          <button
            type="button"
            onClick={onTelegramClick}
            disabled={busy || tgWaiting}
            className="btn-pill btn-soft !py-2 w-full max-w-[280px] justify-center"
            data-testid="auth-telegram-btn"
          >
            <Send className="w-4 h-4" />
            {tgWaiting
              ? (lang === 'ru' ? 'Ждём подтверждения…' : 'Waiting for confirmation…')
              : (lang === 'ru' ? 'Войти через Telegram' : 'Sign in with Telegram')}
          </button>

          {tgWaiting && tg.kind === 'waiting' && (
            <a
              href={tg.deeplink}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs muted-text underline-offset-2 hover:underline"
            >
              {lang === 'ru' ? 'Открыть Telegram ещё раз' : 'Reopen Telegram'}
            </a>
          )}
        </div>
      </div>
    </Modal>
  );
}
