import { useEffect, useRef, useState } from 'react';
import { useApp } from '../lib/store';
import { api, ApiError } from '../lib/api';
import { t } from '../lib/i18n';
import DreamCard from '../components/DreamCard';
import AudioButton from '../components/AudioButton';
import { Send, Loader2, Sparkles, BookOpen } from 'lucide-react';
import { onNewDreamRequest } from '../components/Layout';

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

  // External focus trigger (sidebar "New dream" / cmd+N)
  useEffect(() => onNewDreamRequest(() => {
    composeRef.current?.focus();
    composeRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }), []);

  // Auto-grow textarea
  function adjust() {
    const el = composeRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 260) + 'px';
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
    } catch (e) {
      const ae = e as ApiError;
      if (ae.status === 429) setErr(t('compose.dailyLimitReached', lang));
      else setErr(ae.detail || (lang === 'ru' ? 'Не удалось сохранить' : 'Could not save'));
    } finally {
      setSending(false);
    }
  }

  const hasDreams = dreams.length > 0;
  const charCount = text.length;

  return (
    <div className="space-y-8" data-testid="dreams-page">
      {/* Hero compose */}
      <section className="relative animate-fade-up">
        <div
          className="absolute -top-6 -left-10 -right-10 h-44 pointer-events-none opacity-50 blur-3xl"
          style={{ background: 'radial-gradient(ellipse at center, rgba(250,144,66,0.35), rgba(136,133,255,0.30) 40%, transparent 70%)' }}
        />
        <div className="relative card-surface rounded-[28px] p-4 sm:p-6">
          <label className="flex items-center gap-2 muted-text text-[10px] sm:text-xs uppercase tracking-[0.18em] mb-2 sm:mb-3">
            <BookOpen className="w-3.5 h-3.5" />
            {lang === 'ru' ? 'Запишите сон' : 'Write a dream'}
          </label>
          <textarea
            ref={composeRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') submit();
            }}
            placeholder={lang === 'ru'
              ? 'Я шёл по тёмному лесу, между деревьями мерцал свет…'
              : 'I was walking through a dark forest, light flickering between the trees…'}
            rows={1}
            maxLength={10000}
            data-testid="dream-compose-input"
            className="w-full bg-transparent border-0 outline-none resize-none text-base sm:text-lg leading-relaxed placeholder:muted-text"
            style={{ minHeight: 56 }}
          />
          <div className="flex items-center justify-between mt-3 pt-3 border-t divider gap-3">
            <div className="flex items-center gap-2 muted-text text-xs">
              <AudioButton onText={(s) => setText((p) => (p ? p + ' ' + s : s))} />
              <span className="hidden sm:inline">
                {lang === 'ru' ? 'Текст или голос. ⌘↵ — сохранить' : 'Type or speak. ⌘↵ to save'}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <span className={'text-xs ' + (charCount > 9000 ? 'text-amber-300' : 'muted-text')}>
                {charCount}/10000
              </span>
              <button
                onClick={submit}
                disabled={sending || text.trim().length < 10}
                data-testid="dream-compose-send-btn"
                className="btn-pill btn-primary !px-5"
              >
                {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                <span>{lang === 'ru' ? 'Сохранить' : 'Save'}</span>
              </button>
            </div>
          </div>
          {err && <div className="mt-3 text-sm text-red-400">{err}</div>}
        </div>
      </section>

      {/* Section header */}
      {hasDreams && (
        <div className="flex items-center justify-between">
          <h2 className="font-display text-xl sm:text-2xl">
            {lang === 'ru' ? 'Ваши сны' : 'Your dreams'}
          </h2>
          <span className="muted-text text-sm">
            {dreams.length} {lang === 'ru' ? 'записей' : 'entries'}
          </span>
        </div>
      )}

      {/* Grid */}
      {!dreamsLoaded ? (
        <GridSkeleton />
      ) : !hasDreams ? (
        <EmptyState />
      ) : (
        <div
          className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-3 sm:gap-4"
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
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-3 sm:gap-4">
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
