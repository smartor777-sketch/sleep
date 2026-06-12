import { useEffect, useRef } from 'react';
import { useApp } from '../lib/store';
import { api } from '../lib/api';
import { t } from '../lib/i18n';
import DreamCard from '../components/DreamCard';
import DreamComposer from '../components/DreamComposer';
import { Archive, Loader2 } from 'lucide-react';

export default function DreamsPage() {
  const lang = useApp((s) => s.lang);
  const dreams = useApp((s) => s.dreams);
  const dreamsLoaded = useApp((s) => s.dreamsLoaded);
  const loadDreams = useApp((s) => s.loadDreams);
  const updateDream = useApp((s) => s.updateDreamInCache);

  const pollersRef = useRef<Map<string, ReturnType<typeof setInterval>>>(new Map());

  useEffect(() => {
    loadDreams(true).catch(() => {});
  }, [loadDreams]);

  // Re-poll any dream that's currently 'analyzing' on mount
  useEffect(() => {
    dreams.filter((d) => d.analysis_status === 'analyzing').forEach((d) => startPollingDream(d.id));
    return () => {
      pollersRef.current.forEach((id) => clearInterval(id));
      pollersRef.current.clear();
    };
    // eslint-disable-next-line
  }, [dreamsLoaded]);

  function startPollingDream(dreamId: string) {
    if (pollersRef.current.has(dreamId)) return;
    let attempts = 0;
    const handle = setInterval(async () => {
      attempts += 1;
      try {
        const d = await api.getDream(dreamId);
        updateDream(d);
        if (d.analysis_status === 'analyzed' || d.analysis_status === 'analysis_failed' || attempts > 90) {
          clearInterval(handle);
          pollersRef.current.delete(dreamId);
        }
      } catch {
        if (attempts > 90) {
          clearInterval(handle);
          pollersRef.current.delete(dreamId);
        }
      }
    }, 2000);
    pollersRef.current.set(dreamId, handle);
  }

  const hasDreams = dreams.length > 0;

  return (
    <div className="space-y-7 max-w-6xl" data-testid="dreams-page">
      <section className="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <div className="inline-flex items-center gap-2 muted-text text-xs uppercase tracking-[0.18em] mb-3">
            <Archive className="w-4 h-4" />
            {lang === 'ru' ? 'Архив' : 'Archive'}
          </div>
          <h1 className="font-display text-3xl sm:text-4xl leading-tight">
            {lang === 'ru' ? 'Сны' : 'Dreams'}
          </h1>
          <p className="muted-text mt-2 max-w-xl">
            {lang === 'ru'
              ? 'Личный архив записей, образов и анализов.'
              : 'A personal archive of entries, images and analyses.'}
          </p>
        </div>
        {hasDreams && (
          <span className="muted-text text-sm">
            {dreams.length} {lang === 'ru' ? 'записей' : 'entries'}
          </span>
        )}
      </section>

      <DreamComposer variant="compact" />

      {/* Grid */}
      {!dreamsLoaded ? (
        <GridSkeleton />
      ) : !hasDreams ? (
        <EmptyState />
      ) : (
        <div
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4"
          data-testid="dreams-grid"
        >
          {dreams.map((d) => <DreamCard key={d.id} dream={d} />)}
        </div>
      )}
    </div>
  );
}

function GridSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="h-[220px] rounded-[22px] overflow-hidden"
             style={{ background: 'linear-gradient(110deg, rgba(255,255,255,0.04), rgba(255,255,255,0.10), rgba(255,255,255,0.04))',
                      backgroundSize: '200% 100%' }}>
          <div className="w-full h-full animate-shimmer" />
        </div>
      ))}
    </div>
  );
}

function EmptyState() {
  const lang = useApp((s) => s.lang);
  return (
    <div className="text-center py-16 px-6 animate-fade-up" data-testid="dreams-empty">
      <img
        src="/icon-background.png"
        alt=""
        aria-hidden="true"
        className="w-20 h-20 mx-auto rounded-full object-cover mb-5"
      />
      <h3 className="font-display text-2xl mb-2">{t('dreams.empty.title', lang)}</h3>
      <p className="muted-text max-w-md mx-auto">{t('dreams.empty.sub', lang)}</p>
    </div>
  );
}
