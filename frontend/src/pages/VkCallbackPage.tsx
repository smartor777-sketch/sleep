import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, setTokens } from '../lib/api';
import { useApp } from '../lib/store';

const VK_STATE_KEY = 'vk_auth_state';

export function saveVkState(state: string) {
  sessionStorage.setItem(VK_STATE_KEY, state);
}

export function loadVkState(): string | null {
  return sessionStorage.getItem(VK_STATE_KEY);
}

export default function VkCallbackPage() {
  const navigate = useNavigate();
  const refreshUser = useApp((s) => s.refreshUser);
  const refreshBilling = useApp((s) => s.refreshBilling);
  const [status, setStatus] = useState<'loading' | 'done' | 'error'>('loading');
  const [errorMsg, setErrorMsg] = useState('');
  const called = useRef(false);

  useEffect(() => {
    if (called.current) return;
    called.current = true;

    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');

    if (!code || !state) {
      setStatus('error');
      setErrorMsg('Нет параметров от VK. Попробуй ещё раз.');
      return;
    }

    const isWebFlow = loadVkState() === state;

    api.vkExchange(code, state)
      .then((r) => {
        sessionStorage.removeItem(VK_STATE_KEY);
        if (isWebFlow) {
          setTokens(r.access_token, r.refresh_token);
          Promise.all([refreshUser(), refreshBilling().catch(() => {})]).finally(() => {
            navigate('/', { replace: true });
          });
        } else {
          setStatus('done');
        }
      })
      .catch((e) => {
        setStatus('error');
        setErrorMsg(e?.detail || e?.message || 'Ошибка авторизации. Попробуй ещё раз.');
      });
  }, [navigate, refreshUser, refreshBilling]);

  if (status === 'done') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ink">
        <div className="text-center px-6">
          <div className="text-4xl mb-4">✓</div>
          <p className="text-cream text-lg font-serif">Авторизация через VK прошла успешно</p>
          <p className="text-stone text-sm mt-2">Вернись в приложение — ты уже вошёл.</p>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ink">
        <div className="text-center px-6">
          <p className="text-red-400 text-sm">{errorMsg}</p>
          <button onClick={() => navigate('/')} className="mt-4 text-stone text-sm underline">
            На главную
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-ink">
      <div className="text-center px-6">
        <div className="w-6 h-6 border-2 border-copper border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-stone text-sm">Входим через VK…</p>
      </div>
    </div>
  );
}
