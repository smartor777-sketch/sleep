import { useEffect, useRef, useState } from 'react';
import { api, ApiError } from '../lib/api';
import { t } from '../lib/i18n';
import { useApp } from '../lib/store';
import { onNewDreamRequest } from './Layout';
import AudioButton from './AudioButton';
import { BookOpen, Loader2, Send } from 'lucide-react';

interface Props {
  variant?: 'hero' | 'compact';
  onCreated?: () => void;
  className?: string;
}

export default function DreamComposer({ variant = 'hero', onCreated, className = '' }: Props) {
  const lang = useApp((s) => s.lang);
  const addDream = useApp((s) => s.addDreamToCache);
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const composeRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => onNewDreamRequest(() => {
    composeRef.current?.focus();
    composeRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }), []);

  useEffect(() => {
    const el = composeRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, variant === 'hero' ? 300 : 220) + 'px';
  }, [text, variant]);

  async function submit() {
    const content = text.trim();
    if (content.length < 10) {
      setErr(lang === 'ru' ? 'Хотя бы 10 символов' : 'At least 10 characters');
      return;
    }
    setSending(true);
    setErr(null);
    try {
      const dream = await api.createDream({ content });
      addDream(dream);
      setText('');
      onCreated?.();
    } catch (e) {
      const ae = e as ApiError;
      if (ae.status === 429) setErr(t('compose.dailyLimitReached', lang));
      else setErr(ae.detail || (lang === 'ru' ? 'Не удалось сохранить' : 'Could not save'));
    } finally {
      setSending(false);
    }
  }

  const charCount = text.length;
  const isHero = variant === 'hero';

  return (
    <section className={(isHero ? 'relative animate-fade-up' : 'animate-fade-up') + (className ? ` ${className}` : '')}>
      {isHero && (
        <div
          className="absolute -top-8 inset-x-0 h-44 pointer-events-none opacity-60 blur-3xl"
          style={{ background: 'radial-gradient(ellipse at center, rgba(214,138,58,0.24), rgba(207,226,255,0.18) 44%, transparent 72%)' }}
        />
      )}
      <div className={'relative card-surface dream-card p-4 sm:p-6 h-full flex flex-col ' + (isHero ? 'rounded-[24px]' : 'rounded-[22px]')}>
        <label className="flex items-center gap-2 muted-text text-[10px] sm:text-xs uppercase tracking-[0.18em] mb-3">
          <BookOpen className="w-3.5 h-3.5" />
          {lang === 'ru' ? 'Быстрая запись' : 'Quick note'}
        </label>
        <textarea
          ref={composeRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') submit();
          }}
          placeholder={lang === 'ru'
            ? 'Я шёл по тёмному лесу, между деревьями мерцал свет...'
            : 'I was walking through a dark forest, light flickering between the trees...'}
          rows={1}
          maxLength={10000}
          data-testid="dream-compose-input"
          className={'w-full bg-transparent border-0 outline-none resize-none leading-relaxed placeholder:muted-text flex-1 ' + (isHero ? 'text-lg sm:text-xl' : 'text-base')}
          style={{ minHeight: isHero ? 112 : 64 }}
        />
        <p className="muted-text text-xs mt-3">
          {lang === 'ru'
            ? 'Можно записать даже несколько фраз — этого достаточно для анализа.'
            : 'A few phrases are enough to start the analysis.'}
        </p>
        <div className="flex items-center justify-between mt-4 pt-4 border-t divider gap-3">
          <div className="flex items-center gap-2 muted-text text-xs min-w-0">
            <AudioButton onText={(s) => setText((p) => (p ? p + ' ' + s : s))} />
            <span className="hidden sm:inline truncate">
              {lang === 'ru' ? 'Текст или голос. Cmd+Enter — сохранить' : 'Type or speak. Cmd+Enter to save'}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className={'text-xs tabular-nums ' + (charCount > 9000 ? 'text-amber-300' : 'muted-text')}>
              {charCount}/10000
            </span>
            <button
              onClick={submit}
              disabled={sending || text.trim().length < 10}
              data-testid="dream-compose-send-btn"
              className="btn-pill btn-primary !px-5"
            >
              {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              <span>{lang === 'ru' ? 'Записать сон' : 'Save dream'}</span>
            </button>
          </div>
        </div>
        {err && <div className="mt-3 text-sm text-red-400">{err}</div>}
      </div>
    </section>
  );
}
