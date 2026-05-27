import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api, ApiError } from '../lib/api';
import { Analysis, Dream, Message } from '../lib/types';
import { useApp } from '../lib/store';
import { t } from '../lib/i18n';
import { Sparkles, Send, Loader2, Trash2, AlertCircle, Lock } from 'lucide-react';
import Markdown from '../components/Markdown';

export default function DreamPage() {
  const { id = '' } = useParams();
  const nav = useNavigate();
  const lang = useApp((s) => s.lang);
  const billing = useApp((s) => s.billing);
  const openPaywall = useApp((s) => s.openPaywall);
  const removeDream = useApp((s) => s.removeDreamFromCache);
  const updateDream = useApp((s) => s.updateDreamInCache);

  const [dream, setDream] = useState<Dream | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [chatText, setChatText] = useState('');
  const [chatSending, setChatSending] = useState(false);
  const [chatTaskId, setChatTaskId] = useState<string | null>(null);
  const [confirmDel, setConfirmDel] = useState(false);

  const pollDreamRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollChatRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const isPro = billing?.sub_type === 'pro' || billing?.sub_type === 'trial';

  useEffect(() => { load(); return () => { stopAllPolling(); }; /* eslint-disable-next-line */ }, [id]);

  function stopAllPolling() {
    if (pollDreamRef.current) clearInterval(pollDreamRef.current);
    if (pollChatRef.current) clearInterval(pollChatRef.current);
    pollDreamRef.current = null;
    pollChatRef.current = null;
  }

  async function load() {
    setLoading(true); setErr(null);
    try {
      const d = await api.getDream(id);
      setDream(d);
      if (d.has_analysis || d.analysis_status === 'analyzed') {
        try {
          const a = await api.analysisForDream(id);
          setAnalysis(a);
        } catch {}
        try {
          const h = await api.messageHistory(id, 200, 0);
          setMessages(h.messages);
        } catch {}
      }
      if (d.analysis_status === 'analyzing') startDreamPolling();
    } catch (e) {
      const ae = e as ApiError;
      setErr(ae.detail || 'Not found');
    } finally {
      setLoading(false);
    }
  }

  function startDreamPolling() {
    if (pollDreamRef.current) return;
    let n = 0;
    pollDreamRef.current = setInterval(async () => {
      n++;
      try {
        const d = await api.getDream(id);
        setDream(d);
        updateDream(d);
        if (d.analysis_status === 'analyzed') {
          try { const a = await api.analysisForDream(id); setAnalysis(a); } catch {}
          try { const h = await api.messageHistory(id, 200, 0); setMessages(h.messages); } catch {}
          stopAllPolling();
        } else if (d.analysis_status === 'analysis_failed' || n > 90) {
          stopAllPolling();
        }
      } catch { /* keep trying */ }
    }, 2000);
  }

  async function startAnalysis() {
    if (!dream) return;
    setErr(null);
    try {
      await api.startAnalysis(dream.id);
      const fresh = await api.getDream(dream.id);
      setDream(fresh);
      updateDream(fresh);
      startDreamPolling();
    } catch (e) {
      const ae = e as ApiError;
      if (ae.status === 402) {
        openPaywall(t('dream.limitReached', lang));
      } else {
        setErr(ae.detail || 'Error');
      }
    }
  }

  function startChatPolling(taskId: string) {
    if (pollChatRef.current) return;
    let n = 0;
    pollChatRef.current = setInterval(async () => {
      n++;
      try {
        const s = await api.messageTaskStatus(taskId);
        const status = (s.status || '').toUpperCase();
        if (status === 'SUCCESS' || status === 'COMPLETED' || status === 'FAILURE' || status === 'FAILED' || n > 90) {
          stopAllPolling();
          setChatTaskId(null);
          setChatSending(false);
          try {
            const h = await api.messageHistory(id, 200, 0);
            setMessages(h.messages);
            setTimeout(scrollChatToBottom, 50);
          } catch {}
        }
      } catch {}
    }, 2000);
  }

  function scrollChatToBottom() {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }

  async function sendChat() {
    const content = chatText.trim();
    if (!content || !dream) return;
    if (!isPro) {
      openPaywall(t('dream.gateChat', lang));
      return;
    }
    setChatSending(true);
    setChatText('');
    try {
      const r = await api.sendMessage(dream.id, content);
      setMessages((m) => [...m, r.user_message]);
      setChatTaskId(r.task_id);
      startChatPolling(r.task_id);
      setTimeout(scrollChatToBottom, 50);
    } catch (e) {
      setChatSending(false);
      setErr((e as ApiError).detail || 'Error');
    }
  }

  async function deleteDream() {
    if (!dream) return;
    try {
      await api.deleteDream(dream.id);
      removeDream(dream.id);
      nav('/', { replace: true });
    } catch (e) {
      setErr((e as ApiError).detail || 'Error');
    }
  }

  const g1 = dream?.gradient_color_1 || '#FA9042';
  const g2 = dream?.gradient_color_2 || '#8885FF';
  const date = useMemo(() => {
    if (!dream) return '';
    try { return new Date(dream.created_at).toLocaleString(lang === 'ru' ? 'ru-RU' : 'en-US', { dateStyle: 'medium', timeStyle: 'short' }); }
    catch { return dream.created_at; }
  }, [dream?.created_at, lang, dream]);

  if (loading || !dream) {
    return (
      <div className="py-16 flex items-center justify-center gap-2 muted-text" data-testid="dream-loading">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span>{t('common.loading', lang)}</span>
      </div>
    );
  }

  return (
    <div className="space-y-5 animate-fade-up max-w-4xl" data-testid="dream-page">
      {/* Delete button row (top-right of content) */}
      <div className="flex items-center justify-end">
        <button
          onClick={() => setConfirmDel(true)}
          className="btn-pill btn-ghost !px-3 text-red-300 hover:!bg-red-500/15"
          title={t('dream.delete', lang)}
          data-testid="dream-delete-btn"
        >
          <Trash2 className="w-5 h-5" />
        </button>
      </div>

      {/* Dream hero card */}
      <div
        className="rounded-[28px] p-4 sm:p-6 lg:p-7 relative overflow-hidden text-white"
        style={{ background: `linear-gradient(135deg, ${g1}, ${g2})` }}
      >
        <div className="absolute inset-0 opacity-50 mix-blend-overlay"
             style={{ background: 'linear-gradient(120deg, rgba(255,255,255,0.25), transparent 40%, rgba(0,0,0,0.35))' }} />
        <div className="relative">
          <div className="text-xs opacity-80 mb-2">{date}</div>
          <h1 className="font-display text-xl sm:text-2xl lg:text-3xl leading-tight mb-3 font-semibold">
            {dream.title || dream.content.trim().split(/\s+/).slice(0, 5).join(' ')}
          </h1>
          <p className="whitespace-pre-wrap text-[15px] sm:text-base lg:text-[17px] leading-relaxed opacity-95">
            {dream.content}
          </p>
        </div>
      </div>

      {/* Bottom action / analysis area */}
      {dream.analysis_status === 'saved' && (
        <div className="card-surface rounded-[24px] p-5 text-center">
          <p className="muted-text mb-4 max-w-md mx-auto">
            {lang === 'ru'
              ? 'Запустите глубинный анализ — Oneiros раскроет архетипы, символы и эмоциональный рисунок.'
              : 'Run the depth analysis — Oneiros will reveal archetypes, symbols and the emotional pattern.'}
          </p>
          <button onClick={startAnalysis} className="btn-pill btn-primary text-base px-6" data-testid="dream-analyze-btn">
            <Sparkles className="w-4 h-4" />
            {t('dream.analyze', lang)}
          </button>
          {err && <div className="text-red-400 text-sm mt-3">{err}</div>}
        </div>
      )}

      {dream.analysis_status === 'analyzing' && (
        <div className="card-surface rounded-[24px] p-6 text-center" data-testid="dream-analyzing">
          <div className="w-14 h-14 mx-auto rounded-full flex items-center justify-center mb-3 animate-pulse-soft"
               style={{ background: 'radial-gradient(circle at 30% 30%, #FA9042, #8885FF 80%)' }}>
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <p className="muted-text">{t('dream.analyzing', lang)}</p>
        </div>
      )}

      {dream.analysis_status === 'analysis_failed' && (
        <div className="card-surface rounded-[24px] p-5 text-center" data-testid="dream-failed">
          <AlertCircle className="w-6 h-6 mx-auto mb-2 text-red-400" />
          <p className="muted-text mb-3">{dream.analysis_error_message || t('dream.analysisFailed', lang)}</p>
          <button onClick={startAnalysis} className="btn-pill btn-soft" data-testid="dream-retry-btn">
            {t('dream.retry', lang)}
          </button>
        </div>
      )}

      {dream.analysis_status === 'analyzed' && analysis && (
        <>
          <section className="card-surface rounded-[24px] p-4 sm:p-6 lg:p-7" data-testid="dream-analysis-section">
            <div className="flex items-center gap-2 mb-3">
              <span className="w-2 h-2 rounded-full accent-bg" />
              <h2 className="font-display text-lg accent-text">
                {lang === 'ru' ? 'Разбор Oneiros' : 'Oneiros\' reading'}
              </h2>
            </div>
            <Markdown text={analysis.result || ''} />
          </section>

          {/* Chat */}
          <section className="card-surface rounded-[24px] p-4 sm:p-5" data-testid="chat-section">
            <h3 className="font-display text-lg mb-3 px-1">
              {lang === 'ru' ? 'Диалог о сне' : 'Conversation about the dream'}
            </h3>
            <div ref={scrollRef} className="space-y-3 max-h-[60vh] overflow-y-auto px-1 pb-2">
              {messages.length === 0 && (
                <div className="muted-text text-sm py-4 text-center">
                  {lang === 'ru' ? 'Спросите что-то — углубим понимание сна.' : 'Ask something to deepen the dream.'}
                </div>
              )}
              {messages.map((m) => (
                <div key={m.id} className={m.role === 'user' ? 'flex justify-end' : ''}>
                  <div className={
                    m.role === 'user'
                      ? 'max-w-[85%] rounded-2xl rounded-tr-md px-4 py-2.5 accent-bg text-white'
                      : 'max-w-[92%]'
                  }>
                    {m.role === 'user'
                      ? <div className="whitespace-pre-wrap leading-relaxed">{m.content}</div>
                      : <Markdown text={m.content} />}
                  </div>
                </div>
              ))}
              {chatSending && (
                <div className="muted-text text-sm flex items-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  {lang === 'ru' ? 'Oneiros размышляет…' : 'Oneiros is reflecting…'}
                </div>
              )}
            </div>

            <div className="mt-3 flex items-end gap-2">
              <textarea
                value={chatText}
                onChange={(e) => setChatText(e.target.value)}
                onKeyDown={(e) => { if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') sendChat(); }}
                rows={1}
                placeholder={isPro ? t('dream.askFollowUp', lang) : t('dream.gateChat', lang)}
                disabled={!isPro}
                className="input-base resize-none flex-1 !py-3"
                data-testid="chat-input"
              />
              {!isPro ? (
                <button onClick={() => openPaywall(t('dream.gateChat', lang))}
                        className="w-11 h-11 rounded-full accent-bg text-white flex items-center justify-center"
                        data-testid="chat-gate-btn">
                  <Lock className="w-5 h-5" />
                </button>
              ) : (
                <button onClick={sendChat} disabled={chatSending || !chatText.trim()}
                        className="w-11 h-11 rounded-full accent-bg text-white flex items-center justify-center disabled:opacity-50"
                        data-testid="chat-send-btn">
                  {chatSending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                </button>
              )}
            </div>
          </section>
        </>
      )}

      {/* Delete confirm modal-ish */}
      {confirmDel && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" data-testid="confirm-delete">
          <div className="absolute inset-0 bg-black/60" onClick={() => setConfirmDel(false)} />
          <div className="glass relative rounded-3xl p-6 max-w-sm w-full text-center">
            <p className="mb-5">{t('dream.deleteConfirm', lang)}</p>
            <div className="flex gap-3 justify-center">
              <button onClick={() => setConfirmDel(false)} className="btn-pill btn-ghost">{t('common.cancel', lang)}</button>
              <button onClick={deleteDream} className="btn-pill bg-red-500 hover:bg-red-600 text-white">{t('dream.delete', lang)}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
