import { useLocation, useNavigate, Link } from 'react-router-dom';
import { Menu, ArrowLeft, Sun, Moon, AlertTriangle } from 'lucide-react';
import { useApp } from '../lib/store';
import { t } from '../lib/i18n';
import { ReactNode } from 'react';

interface Props {
  onOpenSidebar: () => void;
  rightSlot?: ReactNode;
}

export default function Topbar({ onOpenSidebar, rightSlot }: Props) {
  const lang = useApp((s) => s.lang);
  const theme = useApp((s) => s.theme);
  const setTheme = useApp((s) => s.setTheme);
  const upgrade = useApp((s) => s.upgradeBanner);
  const loc = useLocation();
  const nav = useNavigate();

  const pageTitle = (() => {
    if (loc.pathname === '/') return lang === 'ru' ? 'Дневник снов' : 'Dream journal';
    if (loc.pathname.startsWith('/dream/')) return lang === 'ru' ? 'Сон' : 'Dream';
    if (loc.pathname === '/map') return t('map.title', lang);
    if (loc.pathname === '/search') return t('search.title', lang);
    if (loc.pathname === '/profile') return t('profile.title', lang);
    return '';
  })();

  const subtitle = (() => {
    if (loc.pathname === '/') return t('app.tagline', lang);
    if (loc.pathname === '/profile') return lang === 'ru' ? 'Настройки и подписка' : 'Settings & subscription';
    return null;
  })();

  const isDreamRoute = loc.pathname.startsWith('/dream/');

  return (
    <div className="sticky top-0 z-30">
      {upgrade && (
        <div
          className="px-4 py-2 text-sm flex items-center gap-2 justify-center"
          style={{ background: 'rgb(var(--accent))', color: '#fff' }}
          data-testid="upgrade-banner"
        >
          <AlertTriangle className="w-4 h-4" />
          <span>{t('common.upgradeRequired', lang)}</span>
        </div>
      )}

      <header className="glass border-b divider">
        <div className="px-3 sm:px-6 lg:px-8 h-14 sm:h-16 flex items-center gap-2 sm:gap-3">
          {/* Mobile menu OR back-arrow for dream route */}
          {isDreamRoute ? (
            <button
              onClick={() => nav(-1)}
              className="w-10 h-10 rounded-full btn-ghost flex items-center justify-center"
              aria-label="back"
              data-testid="topbar-back-btn"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
          ) : (
            <button
              onClick={onOpenSidebar}
              className="lg:hidden w-10 h-10 rounded-full btn-ghost flex items-center justify-center"
              aria-label="menu"
              data-testid="topbar-menu-btn"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}

          <div className="min-w-0 flex-1">
            <h1 className="font-display text-lg sm:text-xl tracking-tight truncate leading-tight">
              {pageTitle}
            </h1>
            {subtitle && (
              <p className="muted-text text-xs hidden sm:block leading-tight">{subtitle}</p>
            )}
          </div>

          <div className="flex items-center gap-2">
            {rightSlot}
            <button
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="w-10 h-10 rounded-full btn-ghost flex items-center justify-center"
              aria-label="theme"
              data-testid="topbar-theme-btn"
              title={theme === 'dark' ? 'Light theme' : 'Dark theme'}
            >
              {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
            <Link
              to="/profile"
              className="hidden sm:flex items-center gap-2 pl-2 pr-3 py-1.5 rounded-full btn-ghost"
              data-testid="topbar-profile-link"
            >
              <img
                src="/icon-background.png"
                alt={lang === 'ru' ? 'Профиль' : 'Profile'}
                className="w-7 h-7 rounded-full object-cover"
              />
            </Link>
          </div>
        </div>
      </header>
    </div>
  );
}
