// Reusable chart components for Profile page.
import { useMemo, useState } from 'react';

/* =====================================================
 * Dreams bar chart (last N days)
 * X-axis: day-of-month numbers
 * Y-axis: count labels (0 / mid / max)
 * Bars use accent-bg via CSS class
 * ===================================================== */
export function DreamsBarChart({ data, lang = 'ru' }: {
  data: { date: string; count: number }[];
  lang?: 'ru' | 'en';
}) {
  const [hover, setHover] = useState<number | null>(null);
  const max = Math.max(1, ...data.map(d => d.count));
  const mid = Math.max(1, Math.round(max / 2));
  const months = lang === 'ru'
    ? ['янв', 'фев', 'мар', 'апр', 'мая', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
    : ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  function fmtDate(d: string) {
    try {
      const dt = new Date(d);
      return `${dt.getDate()} ${months[dt.getMonth()]}`;
    } catch { return d; }
  }

  return (
    <div className="flex gap-3" data-testid="dreams-barchart">
      {/* Y-axis labels */}
      <div className="flex flex-col justify-between text-[10px] muted-text py-1 pr-1 select-none min-w-[14px] text-right">
        <span>{max}</span>
        <span>{mid}</span>
        <span>0</span>
      </div>

      {/* Plot area */}
      <div className="flex-1 relative">
        {/* horizontal guides */}
        <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
          <div className="border-t divider opacity-60" />
          <div className="border-t divider opacity-30" />
          <div className="border-t divider opacity-60" />
        </div>

        {/* bars */}
        <div className="relative flex items-stretch gap-1.5 h-36">
          {data.map((d, i) => {
            const h = (d.count / max) * 100;
            const isHover = hover === i;
            return (
              <div
                key={i}
                className="flex-1 flex flex-col items-center justify-end relative no-tap h-full"
                onMouseEnter={() => setHover(i)}
                onMouseLeave={() => setHover(null)}
                data-testid={`bar-${i}`}
              >
                {/* hover tooltip */}
                {isHover && d.count > 0 && (
                  <div className="absolute -top-7 px-2 py-0.5 rounded-md text-[11px] glass whitespace-nowrap z-10">
                    {fmtDate(d.date)}: <b>{d.count}</b>
                  </div>
                )}
                {/* count label above bar */}
                {d.count > 0 && (
                  <span className="text-[10px] muted-text mb-1 leading-none">{d.count}</span>
                )}
                <div
                  className="w-full rounded-t-md accent-bg transition-all"
                  style={{
                    height: `${Math.max(h, d.count > 0 ? 6 : 2)}%`,
                    opacity: d.count === 0 ? 0.18 : (isHover ? 1 : 0.9),
                    minHeight: d.count > 0 ? 6 : 2,
                  }}
                />
              </div>
            );
          })}
        </div>

        {/* X-axis day labels (alternate to prevent crowding) */}
        <div className="flex gap-1.5 mt-2">
          {data.map((d, i) => {
            let label = '';
            try { label = String(new Date(d.date).getDate()); } catch { label = d.date.slice(8, 10); }
            return (
              <span key={i} className="flex-1 text-center text-[10px] muted-text">
                {label}
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* =====================================================
 * Archetypes donut chart with legend
 * ===================================================== */

// Palette from spec — archetype node colors
const ARCH_PALETTE = [
  '#7E57C2', // 1 — most-frequent (Shadow / Тень)
  '#26A69A', // 2 — Self / Самость
  '#EF5350', // 3 — Anima
  '#FF7043', // 4 — Hero
  '#42A5F5', // 5 — Wise Old Man
  '#AB47BC', // 6
  '#66BB6A', // 7
  '#FFA726', // 8
  '#8D6E63', // 9
  '#78909C', // 10
];

function archetypeColor(index: number): string {
  return ARCH_PALETTE[index % ARCH_PALETTE.length];
}

export function ArchetypesDonut({ data, lang = 'ru' }: {
  data: { name: string; count: number }[];
  lang?: 'ru' | 'en';
}) {
  const [active, setActive] = useState<number | null>(null);

  const items = useMemo(() => {
    const sorted = [...data].sort((a, b) => b.count - a.count);
    const total = sorted.reduce((s, x) => s + x.count, 0) || 1;
    return sorted.map((x, i) => ({
      ...x,
      pct: x.count / total,
      color: archetypeColor(i),
    }));
  }, [data]);

  const total = items.reduce((s, x) => s + x.count, 0);
  if (total === 0) {
    return (
      <div className="muted-text text-sm py-6 text-center">
        {lang === 'ru' ? 'Архетипы появятся после анализов снов.' : 'Archetypes will appear after dream analyses.'}
      </div>
    );
  }

  // Donut geometry: SVG 200×200, stroke-based segments
  const size = 220;
  const cx = size / 2;
  const cy = size / 2;
  const r = 78;             // radius of the stroke center
  const stroke = 32;        // donut thickness
  const C = 2 * Math.PI * r;

  // Pre-compute dash offsets
  let acc = 0;
  const slices = items.map((s, i) => {
    const len = s.pct * C;
    const offset = -acc;
    acc += len;
    return { ...s, len, offset, idx: i };
  });

  const activeItem = active !== null ? slices[active] : null;
  // Center text shows either total or active slice
  const centerTop = activeItem
    ? `${Math.round(activeItem.pct * 100)}%`
    : `${total}`;
  const centerBottom = activeItem
    ? activeItem.name
    : (lang === 'ru' ? 'всего' : 'total');

  return (
    <div className="flex flex-col lg:flex-row gap-6 items-center lg:items-start" data-testid="archetypes-donut">
      {/* Donut */}
      <div className="relative shrink-0" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          role="img"
          aria-label="Archetypes distribution"
        >
          {/* background ring */}
          <circle
            cx={cx} cy={cy} r={r}
            fill="none"
            stroke="rgba(255,255,255,0.04)"
            strokeWidth={stroke}
          />
          {/* segments */}
          <g transform={`rotate(-90 ${cx} ${cy})`}>
            {slices.map((s) => {
              const isActive = active === s.idx;
              return (
                <circle
                  key={s.idx}
                  cx={cx}
                  cy={cy}
                  r={r}
                  fill="none"
                  stroke={s.color}
                  strokeWidth={isActive ? stroke + 6 : stroke}
                  strokeDasharray={`${s.len} ${C - s.len}`}
                  strokeDashoffset={s.offset}
                  style={{ cursor: 'pointer', transition: 'stroke-width 180ms ease, opacity 180ms ease', opacity: active === null || isActive ? 1 : 0.45 }}
                  onMouseEnter={() => setActive(s.idx)}
                  onMouseLeave={() => setActive(null)}
                  data-testid={`donut-slice-${s.idx}`}
                />
              );
            })}
          </g>
          {/* percent labels (only for slices >= 6%) */}
          <g>
            {slices.filter(s => s.pct >= 0.06).map((s) => {
              // Mid-angle of this slice in radians, with -90 rotation
              const startAngle = (s.offset / C) * 360; // negative
              const sliceMidDeg = -startAngle + (s.pct * 360) / 2 - 90;
              const rad = (sliceMidDeg * Math.PI) / 180;
              const lr = r;
              const tx = cx + Math.cos(rad) * lr;
              const ty = cy + Math.sin(rad) * lr;
              return (
                <text
                  key={`l-${s.idx}`}
                  x={tx}
                  y={ty}
                  fontSize={11}
                  fontWeight={700}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fill="#fff"
                  style={{ pointerEvents: 'none', textShadow: '0 1px 2px rgba(0,0,0,0.5)' }}
                >
                  {Math.round(s.pct * 100)}%
                </text>
              );
            })}
          </g>
        </svg>
        {/* center label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <div className="font-display text-2xl leading-none" data-testid="donut-center-top">{centerTop}</div>
          <div className="muted-text text-xs mt-1 leading-tight max-w-[120px] text-center truncate" data-testid="donut-center-bottom">
            {centerBottom}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex-1 w-full grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-2 self-center" data-testid="donut-legend">
        {slices.map((s) => (
          <button
            key={s.idx}
            type="button"
            onMouseEnter={() => setActive(s.idx)}
            onMouseLeave={() => setActive(null)}
            data-testid={`legend-${s.idx}`}
            className="flex items-center gap-2.5 text-left py-1.5 rounded-lg no-tap transition-opacity"
            style={{ opacity: active === null || active === s.idx ? 1 : 0.55 }}
          >
            <span
              className="w-3 h-3 rounded-full shrink-0"
              style={{ background: s.color, boxShadow: `0 0 0 2px ${s.color}28` }}
            />
            <span className="truncate text-sm">{s.name}</span>
            <span className="muted-text text-sm ml-auto tabular-nums">{s.count}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
