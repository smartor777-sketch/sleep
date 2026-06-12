import { Dream } from '../lib/types';
import { Link } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useApp } from '../lib/store';
import { t } from '../lib/i18n';

interface Props { dream: Dream; }

function formatDate(iso: string, lang: string) {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(lang === 'ru' ? 'ru-RU' : 'en-US', {
      day: '2-digit', month: '2-digit', year: 'numeric',
    });
  } catch {
    return iso;
  }
}

export default function DreamCard({ dream }: Props) {
  const lang = useApp((s) => s.lang);
  const g1 = dream.gradient_color_1 || '#FA9042';
  const g2 = dream.gradient_color_2 || '#8885FF';
  const title = dream.title?.trim() ||
    dream.content.trim().split(/\s+/).slice(0, 3).join(' ') || '—';
  const date = formatDate(dream.created_at, lang);
  const isAnalyzing = dream.analysis_status === 'analyzing';
  const isFailed = dream.analysis_status === 'analysis_failed';

  return (
    <Link
      to={`/dream/${dream.id}`}
      data-testid={`dream-card-${dream.id}`}
      className="relative group min-h-[220px] rounded-[22px] overflow-hidden no-tap animate-fade-up card-surface dream-card"
      style={{
        // @ts-ignore custom props
        ['--g1' as any]: g1,
        ['--g2' as any]: g2,
      }}
    >
      <div className="absolute inset-x-0 top-0 h-1 dream-grad" />
      <div className="absolute -right-10 -top-10 w-28 h-28 rounded-full blur-2xl opacity-20 dream-grad pointer-events-none" />

      <div className="relative h-full p-4 flex flex-col justify-between">
        <div className="flex items-start justify-between gap-3">
          <div className="text-[11px] sm:text-xs muted-text font-medium tracking-wide">{date}</div>
          {dream.emoji && <div className="text-base sm:text-lg">{dream.emoji}</div>}
        </div>
        <div className="py-5">
          <div className="text-base lg:text-lg leading-snug line-clamp-3 font-semibold">
            {title}
          </div>
          <p className="muted-text text-sm mt-3 line-clamp-4 leading-relaxed">
            {dream.content}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="chip chip-1">
            {dream.analysis_status === 'analyzed'
              ? (lang === 'ru' ? 'анализ' : 'analysis')
              : dream.analysis_status === 'analyzing'
                ? (lang === 'ru' ? 'анализируется' : 'analyzing')
                : (lang === 'ru' ? 'запись' : 'entry')}
          </span>
        </div>
      </div>

      {isAnalyzing && (
        <div className="absolute top-3 right-3 flex items-center gap-1 glass px-2 py-1 rounded-full text-[11px]">
          <Loader2 className="w-3 h-3 animate-spin" />
          {t('dream.analyzing', lang).split('…')[0]}…
        </div>
      )}
      {isFailed && (
        <div className="absolute top-3 right-3 bg-red-500/80 backdrop-blur px-2 py-1 rounded-full text-[11px] text-white">
          !
        </div>
      )}
    </Link>
  );
}
