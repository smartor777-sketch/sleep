import { NavLink, useLocation, Link, useNavigate } from 'react-router-dom';
import { BarChart3, BookOpen, CalendarDays, Map as MapIcon, User as UserIcon, Sparkles, Plus, X } from 'lucide-react';
import { useApp } from '../lib/store';
import { t } from '../lib/i18n';
import clsx from 'clsx';

interface Props {
  open: boolean;             // controls mobile drawer visibility
  onClose: () => void;
  onNewDream?: () => void;
}

export default function Sidebar({ open, onClose, onNewDream }: Props) {
  const lang = useApp((s) => s.lang);
  const user = useApp((s) => s.user);
  const billing = useApp((s) => s.billing);
  const openPaywall = useApp((s) => s.openPaywall);
  const dreamsTotal = useApp((s) => s.dreams.length);
  const nav = useNavigate();
  const loc = useLocation();

  const items = [
    { to: '/',          icon: CalendarDays, label: t('nav.today', lang),    id: 'nav-today' },
    { to: '/dreams',    icon: BookOpen,     label: t('nav.dreams', lang),   id: 'nav-dreams' },
    { to: '/map',       icon: MapIcon,      label: t('nav.map', lang),      id: 'nav-map' },
    { to: '/analytics', icon: BarChart3,    label: t('nav.analytics', lang), id: 'nav-analytics' },
    { to: '/profile',   icon: UserIcon,     label: t('nav.profile', lang),  id: 'nav-profile' },
  ];

  const tier = billing?.sub_type || 'free';
  const tierLabel = tier === 'pro' ? t('profile.pro', lang)
                   : tier === 'trial' ? t('profile.trial', lang)
                   : t('profile.free', lang);

  function handleNewDream() {
    if (loc.pathname !== '/') nav('/');
    onClose();
    setTimeout(() => onNewDream?.(), 60);
  }

  return (
    <>
      {/* Mobile overlay */}
      <div
        className={clsx(
          'fixed inset-0 z-40 bg-black/55 backdrop-blur-sm transition-opacity lg:hidden',
          open ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        )}
        onClick={onClose}
      />

      <aside
        data-testid="sidebar"
        className={clsx(
          'fixed lg:sticky top-0 left-0 z-50 h-screen w-[272px] flex flex-col',
          'transition-transform duration-300 ease-out',
          'glass border-r divider',
          open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        {/* Brand */}
        <div className="flex items-center justify-between px-5 pt-5 pb-4">
          <Link to="/" onClick={onClose} className="flex items-center gap-2.5 no-tap" data-testid="brand-link">
            <img src="/icon.png" alt="InnerCore" className="w-9 h-9 object-contain shrink-0" />
            <span className="font-display text-xl tracking-tight">InnerCore</span>
          </Link>
          <button
            onClick={onClose}
            className="lg:hidden w-9 h-9 rounded-full btn-ghost flex items-center justify-center"
            aria-label="close"
            data-testid="sidebar-close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* New dream CTA */}
        <div className="px-4">
          <button
            onClick={handleNewDream}
            className="w-full btn-pill btn-primary !rounded-2xl !py-3 justify-start gap-3 group"
            data-testid="new-dream-btn"
          >
            <span className="w-7 h-7 rounded-xl flex items-center justify-center"
                  style={{ background: 'rgba(255,255,255,0.18)' }}>
              <Plus className="w-4 h-4" />
            </span>
            <span className="font-medium">
              {lang === 'ru' ? 'Новый сон' : 'New dream'}
            </span>
            <span className="ml-auto text-[11px] opacity-70 hidden xl:inline">⌘N</span>
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 mt-5 px-3 space-y-0.5 overflow-y-auto">
          <div className="muted-text text-[10px] uppercase tracking-[0.18em] px-3 mb-2">
            {lang === 'ru' ? 'Пространство' : 'Workspace'}
          </div>
          {items.map((it) => (
            <NavLink
              key={it.to}
              to={it.to}
              end={it.to === '/'}
              data-testid={it.id}
              onClick={onClose}
              className={({ isActive }) =>
                clsx(
                  'group flex items-center gap-3 px-3 py-2.5 rounded-2xl text-sm no-tap relative',
                  isActive ? 'accent-text' : 'nav-link-hover'
                )
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span
                      className="absolute left-0 top-2 bottom-2 w-[3px] rounded-r-full accent-bg"
                      aria-hidden
                    />
                  )}
                  <span
                    className={clsx(
                      'w-8 h-8 rounded-xl flex items-center justify-center',
                      isActive ? 'accent-bg text-white' : 'icon-pill'
                    )}
                  >
                    <it.icon className="w-4 h-4" strokeWidth={2.2} />
                  </span>
                  <span className="font-medium">{it.label}</span>
                  {it.to === '/dreams' && dreamsTotal > 0 && (
                    <span className="ml-auto text-xs muted-text">{dreamsTotal}</span>
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Plan widget at bottom */}
        <div className="px-4 pb-5 mt-2">
          <div className="card-surface rounded-2xl p-4" data-testid="sidebar-plan-widget">
            <div className="flex items-center gap-3 mb-1">
              <img
                src="/icon-background.png"
                alt=""
                aria-hidden="true"
                className="w-9 h-9 rounded-xl object-cover shrink-0"
              />
              <div className="min-w-0">
                <div className="text-sm font-semibold leading-tight truncate">
                  {user?.email || (lang === 'ru' ? 'Гость' : 'Guest')}
                </div>
                <div className="text-xs muted-text leading-tight">
                  {tierLabel}
                  {tier === 'free' && billing && (
                    <> · {billing.analyses_left_this_week ?? 0}/2</>
                  )}
                </div>
              </div>
            </div>
            {tier !== 'pro' && (
              <button
                onClick={() => openPaywall(t('profile.upgradeCta', lang))}
                className="w-full mt-3 btn-pill btn-soft !py-2 text-sm"
                data-testid="sidebar-upgrade-btn"
              >
                <Sparkles className="w-3.5 h-3.5" />
                {t('profile.upgradeCta', lang)}
              </button>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}
