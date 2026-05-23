import { useEffect, useMemo, useRef, useState } from 'react';
import { useApp } from '../lib/store';
import { api, ApiError } from '../lib/api';
import { DreamMap, MapNode, SymbolDetail } from '../lib/types';
import { t } from '../lib/i18n';
import { Loader2, RefreshCw, Map as MapIcon, Lock, X, ZoomIn, ZoomOut } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function MapPage() {
  const lang = useApp((s) => s.lang);
  const user = useApp((s) => s.user);
  const billing = useApp((s) => s.billing);
  const openPaywall = useApp((s) => s.openPaywall);
  const isPro = billing?.sub_type === 'pro' || billing?.sub_type === 'trial';

  const [map, setMap] = useState<DreamMap | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('__all__');
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [selected, setSelected] = useState<SymbolDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const dragging = useRef<{ x: number; y: number } | null>(null);

  useEffect(() => {
    if (!user || !isPro) return;
    load(false);
    // eslint-disable-next-line
  }, [user?.id, isPro]);

  async function load(force: boolean) {
    if (!user) return;
    setLoading(true); setErr(null);
    try {
      const m = await api.getMap(user.id, force ? { force_refresh: true } : {});
      setMap(m);
    } catch (e) {
      const ae = e as ApiError;
      if (ae.status === 402 || ae.status === 403) openPaywall(t('map.gate', lang));
      else setErr(ae.detail || 'Error');
    } finally { setLoading(false); }
  }

  async function openSymbol(n: MapNode) {
    if (!user) return;
    setSelected({ ...n, related_symbols: [], occurrences: [] } as SymbolDetail);
    setLoadingDetail(true);
    try {
      const d = await api.getSymbol(user.id, n.id);
      setSelected(d);
    } catch {} finally { setLoadingDetail(false); }
  }

  const filteredNodes = useMemo(() => {
    if (!map) return [] as MapNode[];
    if (filter === '__all__') return map.nodes;
    return map.nodes.filter(n => n.cluster_label === filter || n.related_archetypes.includes(filter));
  }, [map, filter]);

  // Gate for FREE
  if (!isPro) {
    return (
      <div className="text-center py-20 px-4 animate-fade-up" data-testid="map-gate">
        <div className="mx-auto w-20 h-20 rounded-full flex items-center justify-center mb-5"
             style={{ background: 'radial-gradient(circle at 30% 30%, #FA9042, #8885FF 80%)' }}>
          <MapIcon className="w-9 h-9 text-white" />
        </div>
        <h2 className="font-display text-2xl mb-2">{t('map.gate', lang)}</h2>
        <p className="muted-text max-w-md mx-auto mb-6">{t('map.gateDesc', lang)}</p>
        <button onClick={() => openPaywall(t('map.gate', lang))} className="btn-pill btn-primary" data-testid="map-upgrade-btn">
          <Lock className="w-4 h-4" />
          {t('profile.upgradeCta', lang)}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="map-page">
      <div className="flex items-center justify-between gap-4">
        <p className="muted-text text-sm">
          {map ? `${map.nodes.length} ${t('map.nodes', lang)} · zoom ${zoom.toFixed(2)}x${map.meta.cached ? ' · cached' : ''}` : ''}
        </p>
        <div className="flex items-center gap-2">
          <button
            onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); setFilter('__all__'); }}
            className="btn-pill btn-ghost text-sm" data-testid="map-reset-btn">
            {t('map.reset', lang)}
          </button>
          <button onClick={() => load(true)} disabled={loading}
                  className="btn-pill btn-soft text-sm" data-testid="map-refresh-btn">
            <RefreshCw className={'w-4 h-4 ' + (loading ? 'animate-spin' : '')} />
            {t('map.refresh', lang)}
          </button>
        </div>
      </div>

      {/* Archetype filters */}
      {map && map.archetype_filters?.length > 0 && (
        <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1" data-testid="map-filters">
          <FilterPill active={filter === '__all__'} onClick={() => setFilter('__all__')}>{t('map.all', lang)}</FilterPill>
          {map.archetype_filters.map((a) => (
            <FilterPill key={a} active={filter === a} onClick={() => setFilter(a)}>{a}</FilterPill>
          ))}
        </div>
      )}

      {/* Canvas */}
      <div
        className="relative rounded-[28px] overflow-hidden card-surface"
        style={{ height: 'min(72vh, 720px)' }}
        onWheel={(e) => {
          e.preventDefault();
          setZoom((z) => Math.max(0.5, Math.min(5, z + (e.deltaY < 0 ? 0.15 : -0.15))));
        }}
        onMouseDown={(e) => { dragging.current = { x: e.clientX - pan.x, y: e.clientY - pan.y }; }}
        onMouseMove={(e) => {
          if (!dragging.current) return;
          setPan({ x: e.clientX - dragging.current.x, y: e.clientY - dragging.current.y });
        }}
        onMouseUp={() => { dragging.current = null; }}
        onMouseLeave={() => { dragging.current = null; }}
      >
        {/* Grid background */}
        <div className="absolute inset-0 pointer-events-none opacity-25"
             style={{
               backgroundImage:
                 'linear-gradient(rgba(255,255,255,0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.15) 1px, transparent 1px)',
               backgroundSize: '60px 60px',
             }} />

        {/* Soft cluster glows */}
        {map?.clusters?.map((c) => (
          <div key={c.id}
               className="absolute rounded-full pointer-events-none"
               style={{
                 left: `calc(${c.center.x * 100}% + ${pan.x}px)`,
                 top: `calc(${c.center.y * 100}% + ${pan.y}px)`,
                 transform: `translate(-50%, -50%) scale(${zoom})`,
                 width: 220, height: 220,
                 background: `radial-gradient(circle, ${c.color}55 0%, ${c.color}00 70%)`,
                 filter: 'blur(8px)',
               }} />
        ))}

        {/* Nodes */}
        {filteredNodes.map((n) => {
          const size = 14 + Math.round(n.size_weight * 26);
          return (
            <button
              key={n.id}
              data-testid={`map-node-${n.id}`}
              onClick={() => openSymbol(n)}
              className="absolute rounded-full no-tap"
              style={{
                left: `calc(${n.x * 100}% + ${pan.x}px)`,
                top: `calc(${n.y * 100}% + ${pan.y}px)`,
                width: size * zoom,
                height: size * zoom,
                transform: 'translate(-50%, -50%)',
                background: n.archetype_color,
                boxShadow: `0 0 ${18 * zoom}px ${n.archetype_color}AA, inset 0 0 ${8 * zoom}px rgba(255,255,255,0.35)`,
              }}
              title={n.display_label}
            />
          );
        })}

        {/* Node labels */}
        {filteredNodes.slice(0, 14).map((n) => (
          <div
            key={n.id + '-l'}
            className="absolute text-[11px] sm:text-xs px-2 py-1 rounded-full pointer-events-none"
            style={{
              left: `calc(${n.x * 100}% + ${pan.x}px)`,
              top: `calc(${n.y * 100}% + ${pan.y + 24}px)`,
              transform: 'translate(-50%, 0)',
              background: 'rgba(0,0,0,0.55)',
              border: '1px solid rgba(255,255,255,0.10)',
              color: '#fff',
              whiteSpace: 'nowrap',
              maxWidth: 220,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {n.display_label}
          </div>
        ))}

        {/* Zoom buttons */}
        <div className="absolute bottom-3 right-3 flex flex-col gap-2">
          <button onClick={() => setZoom((z) => Math.min(5, z + 0.25))} className="w-10 h-10 rounded-full glass flex items-center justify-center">
            <ZoomIn className="w-4 h-4" />
          </button>
          <button onClick={() => setZoom((z) => Math.max(0.5, z - 0.25))} className="w-10 h-10 rounded-full glass flex items-center justify-center">
            <ZoomOut className="w-4 h-4" />
          </button>
        </div>

        {/* Loading state */}
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/30">
            <Loader2 className="w-6 h-6 animate-spin accent-text" />
          </div>
        )}
        {!loading && map && map.nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center px-6 text-center">
            <div className="muted-text">{t('map.empty', lang)}</div>
          </div>
        )}
        {err && (
          <div className="absolute inset-0 flex items-center justify-center text-red-300">{err}</div>
        )}
      </div>

      {/* Symbol detail sheet */}
      {selected && (
        <SymbolSheet
          detail={selected}
          loading={loadingDetail}
          onClose={() => setSelected(null)}
          lang={lang}
        />
      )}
    </div>
  );
}

function FilterPill({ active, children, onClick }: { active: boolean; children: React.ReactNode; onClick: () => void }) {
  return (
    <button onClick={onClick}
            className={'btn-pill text-sm whitespace-nowrap !py-1.5 ' + (active ? 'btn-soft accent-text' : 'btn-ghost')}>
      {active && <span>✓</span>}
      {children}
    </button>
  );
}

function SymbolSheet({ detail, loading, onClose, lang }:
  { detail: SymbolDetail; loading: boolean; onClose: () => void; lang: 'ru' | 'en' }) {
  const lastOcc = detail.occurrences?.[0];
  return (
    <div className="fixed inset-0 z-40 flex items-end sm:items-center justify-center" data-testid="symbol-sheet">
      <div className="absolute inset-0 bg-black/55 backdrop-blur-sm" onClick={onClose} />
      <div className="relative glass w-full sm:max-w-lg rounded-t-[28px] sm:rounded-[28px] p-5 animate-fade-up" style={{ maxHeight: '85vh' }}>
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <h3 className="font-display text-xl accent-text">{detail.display_label}</h3>
            <p className="muted-text text-sm">
              {lang === 'ru' ? 'Символ' : 'Symbol'}: {detail.symbol_name}
            </p>
          </div>
          <button onClick={onClose} className="w-9 h-9 rounded-full btn-ghost flex items-center justify-center">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="text-sm mb-3">
          {detail.occurrence_count} {t('symbol.occurrences', lang)} {detail.dream_count} {t('symbol.dreams', lang)}
        </div>

        {detail.related_archetypes.length > 0 && (
          <div className="mb-4">
            <div className="muted-text text-xs uppercase tracking-wider mb-2">{t('symbol.archetypes', lang)}</div>
            <div className="flex flex-wrap gap-2">
              {detail.related_archetypes.map((a) => (
                <span key={a} className="px-3 py-1 rounded-full text-sm"
                      style={{ background: 'rgba(var(--accent), 0.15)', color: 'rgb(var(--accent-soft))' }}>
                  {a}
                </span>
              ))}
            </div>
          </div>
        )}

        {loading ? (
          <div className="muted-text text-sm flex items-center gap-2">
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> {t('common.loading', lang)}
          </div>
        ) : (
          <>
            {detail.related_symbols?.length > 0 && (
              <div className="mb-4">
                <div className="muted-text text-xs uppercase tracking-wider mb-2">{t('symbol.related', lang)}</div>
                <ul className="space-y-1 text-sm">
                  {detail.related_symbols.map((s) => (
                    <li key={s.id}>• {s.display_label || s.symbol_name}</li>
                  ))}
                </ul>
              </div>
            )}

            {lastOcc && (
              <div className="mb-4">
                <div className="muted-text text-xs uppercase tracking-wider mb-2">{t('symbol.where', lang)}</div>
                <div className="text-sm">
                  <div className="accent-text mb-1">{lastOcc.date.slice(0, 10)}</div>
                  <div className="muted-text">{lastOcc.text_preview}</div>
                </div>
              </div>
            )}

            {lastOcc && (
              <Link
                to={`/dream/${lastOcc.dream_id}`}
                onClick={onClose}
                className="btn-pill btn-primary w-full justify-center mt-2"
                data-testid="symbol-open-dream-btn"
              >
                {t('symbol.openDream', lang)}
              </Link>
            )}
          </>
        )}
      </div>
    </div>
  );
}
