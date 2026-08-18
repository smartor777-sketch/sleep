import { useEffect, useRef, useState } from 'react';
import { Bell, Check, CheckCheck, Loader2 } from 'lucide-react';
import { useApp } from '../lib/store';
import { t } from '../lib/i18n';
import { Lang } from '../lib/settings';
import { AppNotification } from '../lib/types';

function notificationText(n: AppNotification, lang: Lang): { title: string; body: string } {
  const dreamTitle = n.data?.dream_title
    ? String(n.data.dream_title)
    : lang === 'ru' ? 'сон' : 'dream';
  switch (n.type) {
    case 'analysis_started': {
      const pos = n.data?.queue_position;
      return {
        title: t('notif.started', lang),
        body: pos != null
          ? lang === 'ru'
            ? `Разбираем «${dreamTitle}» — в очереди №${pos}.`
            : `Analyzing “${dreamTitle}” — queue position ${pos}.`
          : lang === 'ru'
            ? `Разбираем «${dreamTitle}».`
            : `Analyzing “${dreamTitle}”.`,
      };
    }
    case 'analysis_completed':
      return {
        title: t('notif.completed', lang),
        body: lang === 'ru'
          ? `Разбор сна «${dreamTitle}» готов.`
          : `The reading of “${dreamTitle}” is ready.`,
      };
    case 'analysis_failed':
      return {
        title: t('notif.failed', lang),
        body: lang === 'ru'
          ? `Не получилось разобрать «${dreamTitle}».`
          : `Could not analyze “${dreamTitle}”.`,
      };
    case 'queue_alert':
      return {
        title: n.title,
        body: n.body || (lang === 'ru' ? 'Очередь анализов перегружена.' : 'Analysis queue is overloaded.'),
      };
    default:
      return { title: n.title, body: n.body || '' };
  }
}

function timeAgo(iso: string, lang: Lang): string {
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const min = Math.floor(diff / 60000);
    if (min < 1) return lang === 'ru' ? 'только что' : 'just now';
    if (min < 60) return lang === 'ru' ? `${min} мин назад` : `${min}m ago`;
    const hrs = Math.floor(min / 60);
    if (hrs < 24) return lang === 'ru' ? `${hrs} ч назад` : `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return lang === 'ru' ? `${days} дн назад` : `${days}d ago`;
  } catch {
    return '';
  }
}

export default function NotificationsBell() {
  const lang = useApp((s) => s.lang);
  const notifications = useApp((s) => s.notifications);
  const unread = useApp((s) => s.notificationsUnread);
  const loadNotifications = useApp((s) => s.loadNotifications);
  const markRead = useApp((s) => s.markNotificationRead);
  const markAllRead = useApp((s) => s.markAllNotificationsRead);

  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  // Periodic refresh (every 20s) + on mount
  useEffect(() => {
    setLoading(true);
    loadNotifications().finally(() => setLoading(false));
    const h = setInterval(() => {
      loadNotifications().catch(() => {});
    }, 20000);
    return () => clearInterval(h);
    // eslint-disable-next-line
  }, [loadNotifications]);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('mousedown', onClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onClick);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  async function openBell() {
    const next = !open;
    setOpen(next);
    if (next) {
      setLoading(true);
      await loadNotifications().finally(() => setLoading(false));
    }
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={openBell}
        className="w-10 h-10 rounded-full btn-ghost flex items-center justify-center relative"
        aria-label={t('notif.title', lang)}
        data-testid="notif-bell"
      >
        <Bell className="w-5 h-5" />
        {unread > 0 && (
          <span
            className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 rounded-full text-[10px] font-bold flex items-center justify-center"
            style={{ background: 'rgb(var(--accent))', color: '#fff' }}
            data-testid="notif-badge"
          >
            {unread > 99 ? '99+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div
          className="absolute right-0 top-12 w-[320px] sm:w-[360px] max-h-[70vh] flex flex-col glass rounded-3xl overflow-hidden z-40 shadow-xl"
          data-testid="notif-dropdown"
        >
          <div className="flex items-center justify-between px-4 py-3 border-b divider">
            <span className="font-display text-sm">{t('notif.title', lang)}</span>
            <div className="flex items-center gap-1">
              {loading && <Loader2 className="w-3.5 h-3.5 animate-spin muted-text" />}
              {unread > 0 && (
                <button
                  onClick={() => markAllRead()}
                  className="flex items-center gap-1 text-xs btn-ghost rounded-full px-2.5 py-1"
                  data-testid="notif-mark-all"
                >
                  <CheckCheck className="w-3.5 h-3.5" />
                  {t('notif.markAll', lang)}
                </button>
              )}
            </div>
          </div>

          <div className="overflow-y-auto divide-y divide-[var(--line)]">
            {notifications.length === 0 ? (
              <div className="p-6 text-center muted-text text-sm" data-testid="notif-empty">
                {t('notif.empty', lang)}
              </div>
            ) : (
              notifications.map((n) => {
                const txt = notificationText(n, lang);
                return (
                  <button
                    key={n.id}
                    onClick={() => { if (!n.is_read) markRead(n.id); }}
                    className={`w-full text-left px-4 py-3 hover:bg-white/5 transition-colors ${n.is_read ? 'opacity-60' : ''}`}
                    data-testid={`notif-item-${n.id}`}
                  >
                    <div className="flex items-start gap-2">
                      <span className="mt-1.5 w-1.5 h-1.5 rounded-full shrink-0"
                            style={{ background: n.is_read ? 'transparent' : 'rgb(var(--accent))' }} />
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-medium leading-snug">{txt.title}</div>
                        {txt.body && <div className="text-xs muted-text mt-0.5 leading-snug">{txt.body}</div>}
                        <div className="text-[10px] muted-text mt-1">{timeAgo(n.created_at, lang)}</div>
                      </div>
                      {n.is_read ? (
                        <Check className="w-3.5 h-3.5 muted-text shrink-0 mt-1" />
                      ) : null}
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}