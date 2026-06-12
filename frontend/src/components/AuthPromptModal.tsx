import { useState } from 'react';
import { LogIn, UserRound } from 'lucide-react';
import Modal from './Modal';
import AuthModal from './AuthModal';
import { useApp } from '../lib/store';

export default function AuthPromptModal() {
  const open = useApp((s) => s.authPromptOpen);
  const closeAuthPrompt = useApp((s) => s.closeAuthPrompt);
  const openOnboarding = useApp((s) => s.openOnboarding);
  const lang = useApp((s) => s.lang);
  const [authOpen, setAuthOpen] = useState(false);

  function continueAsGuest() {
    closeAuthPrompt();
    openOnboarding();
  }

  return (
    <>
      <Modal open={open} closable={false} size="sm" testId="auth-prompt-modal">
        <div className="space-y-5 text-center">
          <div className="mx-auto w-14 h-14 rounded-2xl accent-bg text-white flex items-center justify-center">
            <UserRound className="w-6 h-6" />
          </div>
          <div>
            <h2 className="font-display text-2xl leading-tight">
              {lang === 'ru' ? 'Войдите в аккаунт' : 'Sign in to your account'}
            </h2>
            <p className="muted-text text-sm leading-relaxed mt-2">
              {lang === 'ru'
                ? 'Если у вас уже есть аккаунт, войдите, чтобы открыть свои сны и настройки. Или продолжите как гость.'
                : 'If you already have an account, sign in to open your dreams and settings. Or continue as a guest.'}
            </p>
          </div>

          <div className="space-y-2">
            <button
              type="button"
              onClick={() => setAuthOpen(true)}
              className="btn-pill btn-primary w-full"
              data-testid="auth-prompt-signin-btn"
            >
              <LogIn className="w-4 h-4" />
              {lang === 'ru' ? 'Войти' : 'Sign in'}
            </button>
            <button
              type="button"
              onClick={continueAsGuest}
              className="btn-pill btn-ghost w-full"
              data-testid="auth-prompt-guest-btn"
            >
              {lang === 'ru' ? 'Продолжить как гость' : 'Continue as guest'}
            </button>
          </div>
        </div>
      </Modal>

      <AuthModal open={authOpen} onClose={() => setAuthOpen(false)} />
    </>
  );
}
