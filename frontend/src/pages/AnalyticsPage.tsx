import { useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useApp } from '../lib/store';
import { DreamsBarChart, ArchetypesDonut } from '../components/Charts';
import { ArrowRight, BarChart3, CircleDot, Map as MapIcon } from 'lucide-react';

export default function AnalyticsPage() {
  const lang = useApp((s) => s.lang);
  const stats = useApp((s) => s.stats);
  const dreams = useApp((s) => s.dreams);
  const dreamsLoaded = useApp((s) => s.dreamsLoaded);
  const refreshStats = useApp((s) => s.refreshStats);
  const loadDreams = useApp((s) => s.loadDreams);

  useEffect(() => {
    refreshStats().catch(() => {});
    if (!dreamsLoaded) loadDreams(true).catch(() => {});
  }, [dreamsLoaded, loadDreams, refreshStats]);

  // Recurring symbols from the backend (LLM-extracted, normalized, 2+ dreams),
  // kept as [label, dreamCount] tuples — see docs/SYMBOLS_RAG_CORE.md §3.1.
  const motifs = useMemo<[string, number][]>(
    () => (stats?.recurring_symbols ?? []).map((s) => [s.display_label, s.dream_count]),
    [stats],
  );
  const analyzedCount = dreams.filter((d) => d.analysis_status === 'analyzed').length;
  const recurringCount = motifs.length;

  return (
    <div className="space-y-6 max-w-6xl" data-testid="analytics-page">
      <section>
        <div className="inline-flex items-center gap-2 muted-text text-xs uppercase tracking-[0.18em] mb-3">
          <BarChart3 className="w-4 h-4" />
          {lang === 'ru' ? 'Аналитика' : 'Analytics'}
        </div>
        <h1 className="font-display text-3xl sm:text-4xl leading-tight">
          {lang === 'ru' ? 'Мягкая аналитика снов' : 'Soft dream analytics'}
        </h1>
        <p className="muted-text text-base mt-3 max-w-2xl">
          {lang === 'ru'
            ? 'Здесь собираются статистика, архетипы и повторяющиеся мотивы вашего архива.'
            : 'Statistics, archetypes and recurring motifs from your archive collect here.'}
        </p>
      </section>

      <section className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard label={lang === 'ru' ? 'Всего снов' : 'Total dreams'} value={stats?.total_dreams ?? dreams.length} accent />
        <StatCard label={lang === 'ru' ? 'Серия дней' : 'Day streak'} value={stats?.streak_days ?? 0} />
        <StatCard label={lang === 'ru' ? 'Проанализировано' : 'Analyzed'} value={analyzedCount} />
        <StatCard label={lang === 'ru' ? 'Повторяющихся мотивов' : 'Recurring motifs'} value={recurringCount} />
      </section>

      <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px] items-stretch">
        <div className="card-surface dream-card rounded-[22px] p-5 h-full">
          <div className="flex items-baseline justify-between mb-4 gap-3">
            <div>
              <h2 className="font-display text-xl">{lang === 'ru' ? 'Динамика' : 'Dynamics'}</h2>
              <p className="muted-text text-sm mt-1">{lang === 'ru' ? 'Сны за последние 14 дней' : 'Dreams over the last 14 days'}</p>
            </div>
          </div>
          {stats?.dreams_last_14_days?.length ? (
            <DreamsBarChart data={stats.dreams_last_14_days} lang={lang} />
          ) : (
            <EmptyText text={lang === 'ru' ? 'Динамика появится после нескольких записей.' : 'Dynamics will appear after a few entries.'} />
          )}
        </div>

        <div className="card-surface dream-card rounded-[22px] p-5 h-full">
          <div className="flex items-center gap-2 mb-4">
            <CircleDot className="w-5 h-5 accent-text" />
            <h2 className="font-display text-xl">{lang === 'ru' ? 'Символы и мотивы' : 'Symbols and motifs'}</h2>
          </div>
          {motifs.length > 0 ? (
            <div className="space-y-3">
              {motifs.slice(0, 8).map(([name, count], i) => (
                <div key={name} className="space-y-1.5">
                  <div className="flex items-center justify-between gap-3 text-sm">
                    <span className="truncate">{name.charAt(0).toUpperCase() + name.slice(1)}</span>
                    <span className="muted-text tabular-nums">{count}</span>
                  </div>
                  <div className="h-2 rounded-full overflow-hidden motif-track">
                    <div className="h-full rounded-full accent-bg" style={{ width: `${Math.max(12, (count / motifs[0][1]) * 100)}%`, opacity: 0.95 - i * 0.055 }} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyText text={lang === 'ru' ? 'Мотивы появятся после первых записей.' : 'Motifs will appear after your first entries.'} />
          )}
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px] items-stretch">
        <div className="card-surface dream-card rounded-[22px] p-5 h-full">
          <div className="mb-4">
            <h2 className="font-display text-xl">{lang === 'ru' ? 'Фокус архетипов' : 'Archetype focus'}</h2>
            <p className="muted-text text-sm mt-1">
              {lang === 'ru'
                ? 'Какие архетипические темы чаще проявлялись в ваших снах.'
                : 'Which archetypal themes appeared most often in your dreams.'}
            </p>
          </div>
          {stats?.archetypes_top?.length ? (
            <ArchetypesDonut data={stats.archetypes_top} lang={lang} />
          ) : (
            <EmptyText text={lang === 'ru' ? 'Архетипы появятся после анализов снов.' : 'Archetypes will appear after dream analyses.'} />
          )}
        </div>

        <Link to="/map" className="card-surface dream-card rounded-[22px] p-5 no-tap h-full flex flex-col justify-between">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-11 h-11 rounded-2xl accent-bg text-white flex items-center justify-center">
              <MapIcon className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-display text-xl">{lang === 'ru' ? 'Связь с картой' : 'Map connection'}</h2>
              <p className="muted-text text-sm">{lang === 'ru' ? 'Откройте визуальные связи' : 'Open visual links'}</p>
            </div>
          </div>
          <div className="text-link mt-5">
            {lang === 'ru' ? 'Открыть карту снов' : 'Open dream map'} <ArrowRight className="w-4 h-4" />
          </div>
        </Link>
      </section>
    </div>
  );
}

function StatCard({ label, value, accent }: { label: string; value: number | string; accent?: boolean }) {
  return (
    <div className="card-surface dream-card rounded-[20px] p-4 sm:p-5">
      <div className={'font-display text-2xl sm:text-3xl mb-1 tabular-nums ' + (accent ? 'accent-text' : '')}>{value}</div>
      <div className="muted-text text-xs sm:text-sm">{label}</div>
    </div>
  );
}

function EmptyText({ text }: { text: string }) {
  return <div className="muted-text text-sm py-8 text-center">{text}</div>;
}
