import { useEffect, useRef, useState } from 'react';

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (resp: { credential: string }) => void;
            auto_select?: boolean;
            cancel_on_tap_outside?: boolean;
          }) => void;
          renderButton: (
            parent: HTMLElement,
            options: {
              type?: 'standard' | 'icon';
              theme?: 'outline' | 'filled_blue' | 'filled_black';
              size?: 'small' | 'medium' | 'large';
              text?: 'signin_with' | 'signup_with' | 'continue_with';
              shape?: 'rectangular' | 'pill' | 'circle' | 'square';
              width?: number;
              locale?: string;
            }
          ) => void;
        };
      };
    };
  }
}

interface Props {
  onCredential: (idToken: string) => void;
  locale?: 'ru' | 'en';
  disabled?: boolean;
}

const CLIENT_ID = (import.meta as any).env.VITE_GOOGLE_CLIENT_ID as string | undefined;

export default function GoogleSignInButton({ onCredential, locale = 'ru', disabled }: Props) {
  // Two refs: outer (React-owned, holds skeleton) + inner (GIS-owned, never touched by React after first paint)
  const gisHostRef = useRef<HTMLDivElement | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!CLIENT_ID) return;
    let cancelled = false;

    const init = () => {
      if (cancelled) return;
      if (!window.google?.accounts?.id) {
        setTimeout(init, 150);
        return;
      }
      const host = gisHostRef.current;
      if (!host) return;
      window.google.accounts.id.initialize({
        client_id: CLIENT_ID,
        callback: (resp) => {
          if (resp?.credential) onCredential(resp.credential);
        },
        auto_select: false,
        cancel_on_tap_outside: true,
      });
      window.google.accounts.id.renderButton(host, {
        type: 'standard',
        theme: 'filled_black',
        size: 'large',
        text: 'continue_with',
        shape: 'pill',
        width: 280,
        locale,
      });
      setReady(true);
    };

    init();
    return () => {
      cancelled = true;
    };
  }, [onCredential, locale]);

  if (!CLIENT_ID) return null;

  return (
    <div
      className="flex justify-center"
      style={{ opacity: disabled ? 0.5 : 1, pointerEvents: disabled ? 'none' : 'auto' }}
      data-testid="google-signin-button"
    >
      {/* GIS owns this node — React doesn't render any children into it */}
      <div ref={gisHostRef} className="min-h-10" />
      {!ready && (
        <div className="absolute h-10 w-[280px] rounded-full bg-white/5 animate-pulse" aria-hidden="true" />
      )}
    </div>
  );
}
