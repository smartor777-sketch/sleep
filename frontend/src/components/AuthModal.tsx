import { useCallback, useEffect, useRef, useState } from 'react';
import Modal from './Modal';
import { api, ApiError, getDeviceId, setTokens } from '../lib/api';
import { useApp } from '../lib/store';
import { t } from '../lib/i18n';
import { Loader2, Send } from 'lucide-react';
import GoogleSignInButton from './GoogleSignInButton';
import { saveYandexState } from '../pages/YandexCallbackPage';
import { saveVkState } from '../pages/VkCallbackPage';

interface Props {
  open: boolean;
  onClose: () => void;
}

type TgPrep =
  | { kind: 'preparing' }
  | { kind: 'ready'; token: string; deeplink: string; botUsername: string }
  | { kind: 'error'; message: string };

export default function AuthModal({ open, onClose }: Props) {
  const lang = useApp((s) => s.lang);
  const refreshUser = useApp((s) => s.refreshUser);
  const refreshBilling = useApp((s) => s.refreshBilling);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [tg, setTg] = useState<TgPrep>({ kind: 'preparing' });
  const [waitingConfirm, setWaitingConfirm] = useState(false);
  const [yandexBusy, setYandexBusy] = useState(false);
  const [vkBusy, setVkBusy] = useState(false);
  const pollRef = useRef<number | null>(null);

  function stopPolling() {
    if (pollRef.current) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }

  function reset() {
    setErr(null);
    setBusy(false);
    setYandexBusy(false);
    setVkBusy(false);
    setTg({ kind: 'preparing' });
    setWaitingConfirm(false);
    stopPolling();
  }

  const signInYandex = useCallback(async () => {
    setYandexBusy(true);
    setErr(null);
    try {
      const { state, auth_url } = await api.yandexInit();
      saveYandexState(state);
      window.location.assign(auth_url);
    } catch (e) {
      const ae = e as ApiError;
      setErr(ae.detail || ae.message || 'yandex_init_failed');
      setYandexBusy(false);
    }
  }, []);

  const signInVk = useCallback(async () => {
    setVkBusy(true);
    setErr(null);
    try {
      const { state, auth_url } = await api.vkInit();
      saveVkState(state);
      window.location.assign(auth_url);
    } catch (e) {
      const ae = e as ApiError;
      setErr(ae.detail || ae.message || 'vk_init_failed');
      setVkBusy(false);
    }
  }, []);

  useEffect(() => () => stopPolling(), []);

  useEffect(() => {
    if (!open) {
      reset();
      return;
    }
    let cancelled = false;
    setTg({ kind: 'preparing' });
    api.telegramInit()
      .then((r) => {
        if (cancelled) return;
        setTg({
          kind: 'ready',
          token: r.auth_token,
          deeplink: r.deeplink,
          botUsername: r.bot_username,
        });
      })
      .catch((e) => {
        if (cancelled) return;
        const ae = e as ApiError;
        setTg({ kind: 'error', message: ae.detail || ae.message || 'telegram_unavailable' });
      });
    return () => { cancelled = true; };
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

  const startPolling = useCallback((token: string) => {
    if (waitingConfirm) return;
    setWaitingConfirm(true);
    const anonDevice = getDeviceId();
    pollRef.current = window.setInterval(async () => {
      try {
        const r = await api.telegramStatus(token);
        if (r.status === 'completed' && r.access_token && r.refresh_token) {
          stopPolling();
          setTokens(r.access_token, r.refresh_token);
          try { await api.mergeAnonymous(anonDevice); } catch {}
          await refreshUser();
          refreshBilling().catch(() => {});
          onClose(); reset();
        } else if (r.status === 'expired') {
          stopPolling();
          setWaitingConfirm(false);
          setTg({ kind: 'error', message: 'session_expired' });
        }
      } catch {
        /* keep polling */
      }
    }, 2000);
  }, [waitingConfirm, onClose, refreshUser, refreshBilling]);

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

        {waitingConfirm && (
          <div className="text-sm accent-text bg-white/5 rounded-xl px-3 py-3 flex items-center gap-2" data-testid="tg-waiting">
            <Loader2 className="w-4 h-4 animate-spin shrink-0" />
            <span>
              {lang === 'ru'
                ? 'Ждём подтверждения от Telegram…'
                : 'Waiting for confirmation from Telegram…'}
            </span>
          </div>
        )}

        {tg.kind === 'error' && !waitingConfirm && (
          <div className="text-sm text-red-400 bg-red-500/10 rounded-xl px-3 py-2">
            {tg.message === 'session_expired'
              ? (lang === 'ru' ? 'Время сессии истекло. Закрой и открой окно ещё раз.' : 'Session expired. Close and reopen this dialog.')
              : tg.message}
          </div>
        )}

        <div className="flex flex-col items-center gap-3 pt-1">
          <GoogleSignInButton onCredential={onGoogleCredential} locale={lang} disabled={busy || yandexBusy} />

          <button
            type="button"
            onClick={signInYandex}
            disabled={busy || yandexBusy || vkBusy || waitingConfirm}
            className="flex items-center gap-3 w-full max-w-[280px] rounded-full px-4 py-2 text-sm font-medium text-white transition-opacity disabled:opacity-50"
            style={{ background: '#FC3F1D' }}
            data-testid="auth-yandex-button"
          >
            {yandexBusy ? (
              <Loader2 className="w-5 h-5 animate-spin shrink-0" />
            ) : (
              <svg width="20" height="20" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg" className="shrink-0">
                <circle cx="14" cy="14" r="14" fill="white"/>
                <path d="M15.763 7H13.43C11.11 7 9.5 8.27 9.5 10.55c0 1.98.93 3.08 2.68 4.26L9.3 21h2.54l2.73-5.84h.01L16.9 21H19.5l-3.3-6.56c1.52-.97 2.5-2.12 2.5-4.03C18.7 8.3 17.42 7 15.763 7zm-.72 7.02h-.95V8.82h.86c1.38 0 2.1.75 2.1 2.5 0 1.57-.75 2.7-2.01 2.7z" fill="#FC3F1D"/>
              </svg>
            )}
            <span className="flex-1 text-center">{lang === 'ru' ? 'Войти с Яндекс ID' : 'Sign in with Yandex ID'}</span>
          </button>

          <button
            type="button"
            onClick={signInVk}
            disabled={busy || yandexBusy || vkBusy || waitingConfirm}
            className="flex items-center gap-3 w-full max-w-[280px] rounded-full px-4 py-2 text-sm font-medium text-white transition-opacity disabled:opacity-50"
            style={{ background: '#0077FF' }}
            data-testid="auth-vk-button"
          >
            {vkBusy ? (
              <Loader2 className="w-5 h-5 animate-spin shrink-0" />
            ) : (
              <svg width="20" height="20" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg" className="shrink-0">
                <circle cx="14" cy="14" r="14" fill="white"/>
                <path d="M14.93 19.5c-5.53 0-8.68-3.79-8.8-10.09H8.9c.08 4.63 2.14 6.59 3.76 7V9.41h2.78v4.27c1.6-.17 3.28-2 3.85-4.27h2.74c-.44 2.74-2.28 4.57-3.59 5.31 1.31.61 3.4 2.23 4.19 4.78h-3.02c-.62-1.94-2.17-3.44-4.17-3.64v3.64H14.93z" fill="#0077FF"/>
              </svg>
            )}
            <span className="flex-1 text-center">{lang === 'ru' ? 'Войти с VK ID' : 'Sign in with VK ID'}</span>
          </button>

          {tg.kind === 'ready' ? (
            <a
              href={tg.deeplink}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => startPolling(tg.token)}
              className="btn-pill btn-soft !py-2 w-full max-w-[280px] justify-center"
              data-testid="auth-telegram-link"
            >
              <Send className="w-4 h-4" />
              {lang === 'ru' ? 'Войти через Telegram' : 'Sign in with Telegram'}
            </a>
          ) : (
            <button
              type="button"
              disabled
              className="btn-pill btn-soft !py-2 w-full max-w-[280px] justify-center opacity-60 cursor-not-allowed"
              data-testid="auth-telegram-loading"
            >
              <Loader2 className="w-4 h-4 animate-spin" />
              {lang === 'ru' ? 'Готовлю ссылку…' : 'Preparing link…'}
            </button>
          )}
        </div>

        {tg.kind === 'ready' && (
          <p className="text-xs muted-text text-center pt-1">
            {lang === 'ru'
              ? 'Нужен установленный Telegram (десктоп или мобильное приложение).'
              : 'Requires Telegram app (desktop or mobile).'}
          </p>
        )}
      </div>
    </Modal>
  );
}
