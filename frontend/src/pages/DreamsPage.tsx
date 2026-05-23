import { useEffect, useRef, useState } from 'react';
import { useApp } from '../lib/store';
import { api, ApiError } from '../lib/api';
import { t } from '../lib/i18n';
import DreamCard from '../components/DreamCard';
import AudioButton from '../components/AudioButton';
import { Send, Loader2, Sparkles } from 'lucide-react';

export default function DreamsPage() {
  const lang = useApp((s) => s.lang);
  const dreams = useApp((s) => s.dreams);
  const dreamsLoaded = useApp((s) => s.dreamsLoaded);
  const loadDreams = useApp((s) => s.loadDreams);
  const addDream = useApp((s) => s.addDreamToCache);
  const updateDream = useApp((s) => s.updateDreamInCache);

  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const composeRef = useRef<HTMLTextAreaElement | null>(null);
  const pollersRef = useRef<Map<string, ReturnType<typeof setInterval>>>(new Map());

  useEffect(() => {
    loadDreams(true).catch(() => {});
  }, [loadDreams]);

  // Auto-grow textarea
  function adjust() {
    const el = composeRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 220) + 'px';
  }
  useEffect(() => { adjust(); }, [text]);

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

  async function submit() {
    const content = text.trim();
    if (content.length < 10) {
      setErr(lang === 'ru' ? 'Хотя бы 10 символов' : 'At least 10 characters');
      return;
    }
    setSending(true); setErr(null);
    try {
      const dream = await api.createDream({ content });
      addDream(dream);
      setText('');
      // start analysis automatically? No — spec says manual. But create only.
    } catch (e) {
      const ae = e as ApiError;
      if (ae.status === 429) setErr(t('compose.dailyLimitReached', lang));
      else setErr(ae.detail || (lang === 'ru' ? 'Не удалось сохранить' : 'Could not save'));
    } finally {
      setSending(false);
    }
  }

  const hasDreams = dreams.length > 0;

  return (
    <div className="space-y-6" data-testid="dreams-page">
      {/* Header */}
      <div className="flex items-end justify-between gap-4 pt-2">
        <div>
          <h1 className="font-display text-3xl sm:text-4xl tracking-tight">
            {lang === 'ru' ? 'Дневник снов' : 'Dream journal'}
          </h1>
          <p className="muted-text mt-1 text-sm">{t('app.tagline', lang)}</p>
        </div>
        {dreamsLoaded && (
          <div className="hidden sm:block muted-text text-sm">
            {dreams.length} {lang === 'ru' ? 'снов' : 'dreams'}
          </div>
        )}
      </div>

      {/* Compose */}
      <div className="glass rounded-[28px] p-3 sm:p-4">
        <div className="flex items-end gap-3">
          <AudioButton onText={(s) => setText((prev) => (prev ? prev + ' ' + s : s))} />
          <textarea
            ref={composeRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') submit();
            }}
            placeholder={t('compose.placeholder', lang)}
            rows={1}
            maxLength={10000}
            data-testid="dream-compose-input"
            className="input-base resize-none flex-1 !rounded-2xl !py-3"
          />
          <button
            onClick={submit}
            disabled={sending || text.trim().length < 10}
            className="w-11 h-11 rounded-full accent-bg text-white flex items-center justify-center disabled:opacity-50"
            title={t('compose.send', lang)}
            data-testid="dream-compose-send-btn"
          >
            {sending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          </button>
        </div>
        {err && <div className="mt-2 text-sm text-red-400 px-2">{err}</div>}
      </div>

      {/* Grid */}
      {!dreamsLoaded ? (
        <GridSkeleton />
      ) : !hasDreams ? (
        <EmptyState />
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4" data-testid="dreams-grid">
          {dreams.map((d) => <DreamCard key={d.id} dream={d} />)}
        </div>
      )}
    </div>
  );
}

function GridSkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="aspect-[4/5] rounded-[28px] overflow-hidden"
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
    <div className="text-center py-12 px-6 animate-fade-up" data-testid="dreams-empty">
      <div className="w-20 h-20 mx-auto rounded-full flex items-center justify-center mb-5"
           style={{ background: 'radial-gradient(circle at 30% 30%, #FA9042, #8885FF 80%)' }}>
        <Sparkles className="w-8 h-8 text-white" />
      </div>
      <h3 className="font-display text-xl mb-2">{t('dreams.empty.title', lang)}</h3>
      <p className="muted-text max-w-md mx-auto">{t('dreams.empty.sub', lang)}</p>
    </div>
  );
}
