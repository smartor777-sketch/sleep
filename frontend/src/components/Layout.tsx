import { ReactNode } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { LayoutGrid, MessageCircle, Search, MapPin, User as UserIcon, AlertTriangle } from 'lucide-react';
import { useApp } from '../lib/store';
import { t } from '../lib/i18n';
import clsx from 'clsx';

export default function Layout({ children }: { children: ReactNode }) {
  const lang = useApp((s) => s.lang);
  const upgrade = useApp((s) => s.upgradeBanner);
  const loc = useLocation();
  const isDreamRoute = loc.pathname.startsWith('/dream/');

  return (
    <div className="grain min-h-screen flex flex-col relative">
      {upgrade && (
        <div className="sticky top-0 z-40 px-4 py-2 text-sm flex items-center gap-2 justify-center"
             style={{ background: 'rgb(var(--accent))', color: '#fff' }}>
          <AlertTriangle className="w-4 h-4" />
          <span>{t('common.upgradeRequired', lang)}</span>
        </div>
      )}

      <main className={clsx(
        'flex-1 max-w-6xl mx-auto w-full px-4 sm:px-6 pt-6 relative z-10',
        isDreamRoute ? 'pb-6' : 'pb-28'
      )}>
        {children}
      </main>

      {!isDreamRoute && <BottomNav />}
    </div>
  );
}

function BottomNav() {
  const lang = useApp((s) => s.lang);
  const items = [
    { to: '/', icon: LayoutGrid, label: t('nav.grid', lang), id: 'nav-grid' },
    { to: '/search', icon: Search, label: t('nav.search', lang), id: 'nav-search' },
    { to: '/map', icon: MapPin, label: t('nav.map', lang), id: 'nav-map' },
    { to: '/profile', icon: UserIcon, label: t('nav.profile', lang), id: 'nav-profile' },
  ];
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-30 glass border-t divider"
      data-testid="bottom-nav"
    >
      <div className="max-w-6xl mx-auto flex items-stretch justify-around px-4 py-2 safe-bottom">
        {items.map((it) => (
          <NavLink
            key={it.to}
            to={it.to}
            end={it.to === '/'}
            data-testid={it.id}
            className={({ isActive }) =>
              clsx(
                'flex-1 max-w-[120px] flex flex-col items-center justify-center gap-1 py-2 rounded-2xl no-tap',
                isActive ? 'accent-text' : 'muted-text'
              )
            }
          >
            <it.icon className="w-6 h-6" strokeWidth={2.1} />
            <span className="text-[11px]">{it.label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
