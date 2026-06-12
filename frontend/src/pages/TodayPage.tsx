import { useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useApp } from '../lib/store';
import DreamComposer from '../components/DreamComposer';
import { Dream } from '../lib/types';
import { ArrowRight, CalendarDays, Map as MapIcon, Sparkles } from 'lucide-react';

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

function extractMotifs(dreams: Dream[]) {
  const stop = new Set([
    'и', 'в', 'во', 'на', 'не', 'я', 'мы', 'он', 'она', 'оно', 'это', 'как', 'но', 'за', 'из', 'по', 'под', 'там', 'мне', 'меня',
    'the', 'and', 'was', 'were', 'with', 'from', 'into', 'that', 'this', 'you', 'had', 'for', 'not', 'but', 'then', 'there',
  ]);
  const counts = new Map<string, number>();
  dreams.forEach((d) => {
    const words = d.content
      .toLowerCase()
      .replace(/[^\p{L}\p{N}\s-]/gu, ' ')
      .split(/\s+/)
      .filter((w) => w.length > 3 && !stop.has(w));
    Array.from(new Set(words)).forEach((w) => counts.set(w, (counts.get(w) || 0) + 1));
  });
  return Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([name, count]) => ({ name: name.charAt(0).toUpperCase() + name.slice(1), count }));
}

export default function TodayPage() {
  const lang = useApp((s) => s.lang);
  const user = useApp((s) => s.user);
  const dreams = useApp((s) => s.dreams);
  const dreamsLoaded = useApp((s) => s.dreamsLoaded);
  const loadDreams = useApp((s) => s.loadDreams);
  const refreshStats = useApp((s) => s.refreshStats);

  useEffect(() => {
    if (!dreamsLoaded) loadDreams(true).catch(() => {});
    refreshStats().catch(() => {});
  }, [dreamsLoaded, loadDreams, refreshStats]);

  const motifs = useMemo(() => extractMotifs(dreams), [dreams]);
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
  const nodes = [
    { x: 22, y: 35, s: 18, c: '#D68A3A' },
    { x: 48, y: 58, s: 26, c: '#CFE2FF' },
    { x: 74, y: 34, s: 20, c: '#DCCBFF' },
    { x: 66, y: 74, s: 14, c: '#DCE8E1' },
  ];
  return (
    <section className="card-surface dream-card rounded-[22px] p-5 min-h-[360px] h-full flex flex-col">
      <div className="flex items-center justify-between gap-3 mb-4">
        <div>
          <h2 className="font-display text-xl">{lang === 'ru' ? 'Карта снов' : 'Dream map'}</h2>
          <p className="muted-text text-sm mt-1">
            {hasDreams
              ? (lang === 'ru' ? 'Компактный вид связей' : 'A compact view of links')
              : (lang === 'ru' ? 'Начнёт проявляться после нескольких записей' : 'It starts appearing after a few entries')}
          </p>
        </div>
        <MapIcon className="w-5 h-5 accent-text" />
      </div>
      <Link to="/map" className="block map-preview rounded-2xl min-h-[220px] flex-1 relative overflow-hidden no-tap">
        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100" aria-hidden="true">
          <line x1="22" y1="35" x2="48" y2="58" stroke="rgba(250,247,242,0.28)" strokeWidth="0.6" />
          <line x1="48" y1="58" x2="74" y2="34" stroke="rgba(250,247,242,0.24)" strokeWidth="0.6" />
          <line x1="48" y1="58" x2="66" y2="74" stroke="rgba(250,247,242,0.22)" strokeWidth="0.6" />
          {nodes.map((n, i) => (
            <circle key={i} cx={n.x} cy={n.y} r={n.s / 4} fill={n.c} opacity="0.92" />
          ))}
        </svg>
        <span className="absolute left-4 bottom-4 text-sm text-white/86 inline-flex items-center gap-1.5">
          {lang === 'ru' ? 'Открыть карту' : 'Open map'} <ArrowRight className="w-4 h-4" />
        </span>
      </Link>
    </section>
  );
}
