import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useApp } from '../lib/store';
import DreamComposer from '../components/DreamComposer';
import { api } from '../lib/api';
import { Dream, DreamMap } from '../lib/types';
import { ArrowRight, CalendarDays, Map as MapIcon, Sparkles } from 'lucide-react';
import { createMapFit, nodeImportance, previewLinks } from '../lib/mapLayout';

function formatDate(iso: string, lang: string) {
  try {
    return new Date(iso).toLocaleDateString(lang === 'ru' ? 'ru-RU' : 'en-US', {
      day: '2-digit',
      month: 'long',
    });
  } catch {
    return iso;
  }
}

function titleOf(dream: Dream) {
  return dream.title?.trim() || dream.content.trim().split(/\s+/).slice(0, 6).join(' ') || '...';
}

export default function TodayPage() {
  const lang = useApp((s) => s.lang);
  const user = useApp((s) => s.user);
  const dreams = useApp((s) => s.dreams);
  const stats = useApp((s) => s.stats);
  const dreamsLoaded = useApp((s) => s.dreamsLoaded);
  const loadDreams = useApp((s) => s.loadDreams);
  const refreshStats = useApp((s) => s.refreshStats);

  useEffect(() => {
    if (!dreamsLoaded) loadDreams(true).catch(() => {});
    refreshStats().catch(() => {});
  }, [dreamsLoaded, loadDreams, refreshStats]);

  // Recurring symbols come from the backend (LLM-extracted, normalized, 2+ dreams),
  // not a client-side word count — see docs/SYMBOLS_RAG_CORE.md §3.1.
  const motifs = useMemo(
    () =>
      (stats?.recurring_symbols ?? []).slice(0, 6).map((s) => ({
        name: s.display_label.charAt(0).toUpperCase() + s.display_label.slice(1),
        count: s.dream_count,
      })),
    [stats],
  );
  const latest = dreams.slice(0, 3);
  const name = user?.first_name || user?.email?.split('@')[0] || (lang === 'ru' ? 'Гость' : 'Guest');

  return (
    <div className="space-y-7" data-testid="today-page">
      <section className="pt-1">
        <div className="inline-flex items-center gap-2 muted-text text-xs uppercase tracking-[0.18em] mb-3">
          <CalendarDays className="w-4 h-4" />
          {lang === 'ru' ? 'Сегодня' : 'Today'}
        </div>
        <h1 className="font-display text-3xl sm:text-5xl leading-tight tracking-tight max-w-3xl">
          {lang === 'ru' ? `Доброе утро, ${name}` : `Good morning, ${name}`}
        </h1>
        <p className="muted-text text-base sm:text-lg mt-3 max-w-2xl">
          {lang === 'ru'
            ? 'Запишите сон и посмотрите, какие мотивы возвращаются.'
            : 'Write a dream and see which motifs return.'}
        </p>
      </section>

      <section className="grid gap-5 lg:grid-cols-[minmax(320px,0.78fr)_minmax(0,1.22fr)] lg:grid-rows-[minmax(260px,auto)_minmax(360px,auto)] items-stretch">
        <DreamComposer variant="hero" className="min-h-[280px] lg:min-h-[260px]" />
        <MotifsCard motifs={motifs} lang={lang} />
        <LatestDreams dreams={latest} lang={lang} loaded={dreamsLoaded} />
        <MapPreview lang={lang} hasDreams={dreams.length >= 3} />
      </section>
    </div>
  );
}

function MotifsCard({ motifs, lang }: { motifs: { name: string; count: number }[]; lang: 'ru' | 'en' }) {
  return (
    <section className="card-surface dream-card rounded-[22px] p-5 min-h-[280px] lg:min-h-[260px] h-full flex flex-col">
      <div className="flex items-center justify-between gap-3 mb-4">
        <div>
          <h2 className="font-display text-xl">{lang === 'ru' ? 'Что возвращается' : 'What returns'}</h2>
          <p className="muted-text text-sm mt-1">{lang === 'ru' ? 'Повторяющиеся слова и образы' : 'Recurring words and images'}</p>
        </div>
        <Sparkles className="w-5 h-5 accent-text" />
      </div>
      {motifs.length > 0 ? (
        <div className="flex flex-wrap gap-2 content-start">
          {motifs.map((m, i) => (
            <span key={m.name} className={`chip chip-${(i % 4) + 1}`}>
              {m.name}
              <span className="opacity-60">{m.count}</span>
            </span>
          ))}
        </div>
      ) : (
        <p className="muted-text text-sm leading-relaxed">
          {lang === 'ru'
            ? 'Когда появятся первые сны, здесь отобразятся повторяющиеся мотивы.'
            : 'Recurring motifs will appear here after the first dreams.'}
        </p>
      )}
    </section>
  );
}

function LatestDreams({ dreams, lang, loaded }: { dreams: Dream[]; lang: 'ru' | 'en'; loaded: boolean }) {
  return (
    <section className="card-surface dream-card rounded-[22px] p-5 min-h-[360px] h-full flex flex-col">
      <div className="flex items-center justify-between gap-3 mb-4">
        <div>
          <h2 className="font-display text-xl">{lang === 'ru' ? 'Последние сны' : 'Recent dreams'}</h2>
          <p className="muted-text text-sm mt-1">{lang === 'ru' ? 'Три последние записи' : 'Your latest three entries'}</p>
        </div>
        <Link to="/dreams" className="text-link">
          {lang === 'ru' ? 'Все сны' : 'All dreams'} <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
      {!loaded ? (
        <div className="space-y-3 flex-1">
          {Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-20 rounded-2xl skeleton-soft" />)}
        </div>
      ) : dreams.length > 0 ? (
        <div className="space-y-3 flex-1">
          {dreams.map((d) => (
            <Link key={d.id} to={`/dream/${d.id}`} className="block rounded-2xl p-4 quiet-row no-tap">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="font-semibold truncate">{titleOf(d)}</div>
                  <p className="muted-text text-sm mt-1 line-clamp-2">{d.content}</p>
                </div>
                <span className="muted-text text-xs shrink-0">{formatDate(d.created_at, lang)}</span>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <p className="muted-text text-sm leading-relaxed">
          {lang === 'ru' ? 'Здесь появятся ваши последние записи.' : 'Your recent entries will appear here.'}
        </p>
      )}
    </section>
  );
}

function MapPreview({ lang, hasDreams }: { lang: 'ru' | 'en'; hasDreams: boolean }) {
  const user = useApp((s) => s.user);
  const billing = useApp((s) => s.billing);
  const isPro = billing?.sub_type === 'pro' || billing?.sub_type === 'trial';
  const [previewMap, setPreviewMap] = useState<DreamMap | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (!user || !isPro) {
      setPreviewMap(null);
      return () => { cancelled = true; };
    }

    setLoading(true);
    api.getMap(user.id)
      .then((m) => { if (!cancelled) setPreviewMap(m); })
      .catch(() => { if (!cancelled) setPreviewMap(null); })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, [user?.id, isPro]);

  const fittedNodes = useMemo(() => createMapFit(previewMap?.nodes ?? [], 0.1).nodes, [previewMap]);
  const nodes = useMemo(
    () => [...fittedNodes].sort((a, b) => nodeImportance(b) - nodeImportance(a)).slice(0, 28),
    [fittedNodes],
  );
  const links = useMemo(() => previewLinks(nodes, 18), [nodes]);
  const labels = nodes.slice(0, 5);
  const hasRealMap = nodes.length > 0;

  return (
    <section className="card-surface dream-card rounded-[22px] p-5 min-h-[360px] h-full flex flex-col">
      <div className="flex items-center justify-between gap-3 mb-4">
        <div>
          <h2 className="font-display text-xl">{lang === 'ru' ? 'Карта снов' : 'Dream map'}</h2>
          <p className="muted-text text-sm mt-1">
            {hasRealMap
              ? (lang === 'ru' ? 'Миниатюра вашей карты' : 'A miniature of your map')
              : hasDreams
              ? (lang === 'ru' ? 'Компактный вид связей' : 'A compact view of links')
              : (lang === 'ru' ? 'Начнёт проявляться после нескольких записей' : 'It starts appearing after a few entries')}
          </p>
        </div>
        <MapIcon className="w-5 h-5 accent-text" />
      </div>
      <Link to="/map" className="block map-preview rounded-2xl min-h-[220px] flex-1 relative overflow-hidden no-tap">
        {hasRealMap ? (
          <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100" aria-hidden="true">
            {links.map(({ a, b }) => (
              <line
                key={`${a.id}:${b.id}`}
                x1={a.viewX * 100}
                y1={a.viewY * 100}
                x2={b.viewX * 100}
                y2={b.viewY * 100}
                stroke="rgba(250,247,242,0.26)"
                strokeWidth="0.35"
              />
            ))}
            {nodes.map((n) => (
              <circle
                key={n.id}
                cx={n.viewX * 100}
                cy={n.viewY * 100}
                r={1.4 + n.size_weight * 3.2}
                fill={n.archetype_color}
                opacity="0.94"
              />
            ))}
            {labels.map((n) => (
              <text
                key={`${n.id}-label`}
                x={n.viewX * 100}
                y={n.viewY * 100 + 6}
                textAnchor="middle"
                fill="rgba(255,255,255,0.72)"
                fontSize="3"
                fontWeight="600"
              >
                {n.display_label.slice(0, 14)}
              </text>
            ))}
          </svg>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center px-6 text-center">
            <div className="text-sm text-white/62 leading-relaxed">
              {loading
                ? (lang === 'ru' ? 'Собираем миниатюру карты...' : 'Preparing the map miniature...')
                : (lang === 'ru' ? 'Карта начнёт проявляться после нескольких записей.' : 'The map starts appearing after a few entries.')}
            </div>
          </div>
        )}
        <span className="absolute left-4 bottom-4 text-sm text-white/86 inline-flex items-center gap-1.5">
          {lang === 'ru' ? 'Открыть карту' : 'Open map'} <ArrowRight className="w-4 h-4" />
        </span>
      </Link>
    </section>
  );
}
