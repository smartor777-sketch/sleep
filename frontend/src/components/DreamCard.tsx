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
      className="relative group aspect-[4/5] rounded-[28px] overflow-hidden no-tap animate-fade-up"
      style={{
        // @ts-ignore custom props
        ['--g1' as any]: g1,
        ['--g2' as any]: g2,
      }}
    >
      <div className="absolute inset-0 dream-grad" />
      {/* shine sheen */}
      <div className="absolute inset-0 opacity-60 mix-blend-overlay pointer-events-none"
           style={{ background: 'linear-gradient(120deg, rgba(255,255,255,0.25) 0%, rgba(255,255,255,0) 35%, rgba(0,0,0,0.25) 100%)' }} />
      {/* darken bottom for legibility */}
      <div className="absolute inset-0 pointer-events-none"
           style={{ background: 'linear-gradient(180deg, rgba(0,0,0,0) 30%, rgba(0,0,0,0.45) 100%)' }} />

      <div className="relative h-full p-3 sm:p-4 flex flex-col justify-between text-white">
        <div className="text-xs sm:text-sm opacity-90 font-medium tracking-wide">{date}</div>
        <div>
          <div className="text-base sm:text-lg leading-tight line-clamp-3 font-semibold drop-shadow">
            {title}
          </div>
          {dream.emoji && <div className="mt-1 text-lg">{dream.emoji}</div>}
        </div>
      </div>

      {isAnalyzing && (
        <div className="absolute top-3 right-3 flex items-center gap-1 bg-black/40 backdrop-blur px-2 py-1 rounded-full text-[11px] text-white">
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
