import { useEffect, useState } from 'react';
import { useApp } from '../lib/store';
import { api } from '../lib/api';
import { Dream } from '../lib/types';
import { t } from '../lib/i18n';
import DreamCard from '../components/DreamCard';
import { Loader2, Search as SearchIcon } from 'lucide-react';

export default function SearchPage() {
  const lang = useApp((s) => s.lang);
  const [q, setQ] = useState('');
  const [mode, setMode] = useState<'semantic' | 'lexical'>('semantic');
  const [results, setResults] = useState<Dream[] | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const handle = setTimeout(async () => {
      if (q.trim().length < 1) { setResults(null); return; }
      setLoading(true);
      try {
        const r = await api.searchDreams(q.trim(), mode);
        setResults(r.dreams);
      } catch { setResults([]); }
      finally { setLoading(false); }
    }, 350);
    return () => clearTimeout(handle);
  }, [q, mode]);

  return (
    <div className="space-y-5 max-w-5xl" data-testid="search-page">
      <div className="glass rounded-[24px] p-3 flex items-center gap-3">
        <SearchIcon className="w-5 h-5 muted-text ml-2" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t('search.placeholder', lang)}
          autoFocus
          data-testid="search-input"
          className="bg-transparent border-0 outline-none flex-1 py-2 text-base"
        />
        {loading && <Loader2 className="w-4 h-4 animate-spin muted-text" />}
      </div>

      <div className="flex gap-2 text-sm">
        <button
          onClick={() => setMode('semantic')}
          data-testid="search-mode-semantic"
          className={'btn-pill !py-1.5 ' + (mode === 'semantic' ? 'btn-soft accent-text' : 'btn-ghost')}>
          {t('search.modeSemantic', lang)}
        </button>
        <button
          onClick={() => setMode('lexical')}
          data-testid="search-mode-lexical"
          className={'btn-pill !py-1.5 ' + (mode === 'lexical' ? 'btn-soft accent-text' : 'btn-ghost')}>
          {t('search.modeLexical', lang)}
        </button>
      </div>

      {results === null && (
        <div className="text-center muted-text py-12">
          {lang === 'ru'
            ? 'Введите запрос — слово, образ или ощущение.'
            : 'Type a query — a word, an image, a feeling.'}
        </div>
      )}
      {results !== null && results.length === 0 && !loading && (
        <div className="text-center muted-text py-12">{t('search.nothing', lang)}</div>
      )}
      {results && results.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-3 sm:gap-4">
          {results.map((d) => <DreamCard key={d.id} dream={d} />)}
        </div>
      )}
    </div>
  );
}
