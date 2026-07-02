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
            className="btn-pill btn-soft !py-2 w-full max-w-[280px] justify-center"
            data-testid="auth-yandex-button"
          >
            {yandexBusy
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <span className="font-bold text-[13px] tracking-wide" style={{ color: '#FC3F1D' }}>Я</span>
            }
            {lang === 'ru' ? 'Войти через Яндекс' : 'Sign in with Yandex'}
          </button>

          <button
            type="button"
            onClick={signInVk}
            disabled={busy || yandexBusy || vkBusy || waitingConfirm}
            className="btn-pill btn-soft !py-2 w-full max-w-[280px] justify-center"
            data-testid="auth-vk-button"
          >
            {vkBusy
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <span className="font-bold text-[12px]" style={{ color: '#0077FF' }}>VK</span>
            }
            {lang === 'ru' ? 'Войти через VK' : 'Sign in with VK'}
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
