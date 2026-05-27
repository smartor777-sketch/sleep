import React, { useMemo } from "react";

/**
 * DreamMap demo — flat 2D vector projection of dream points with clusters.
 * Cluster labels mimic the actual app screenshot.
 */
const CLUSTERS = [
  { cx: 280, cy: 130, label: "образ матери", color: "#B87333", count: 11 },
  { cx: 165, cy: 195, label: "вода и пустота", color: "#D38A45", count: 8 },
  { cx: 360, cy: 230, label: "тень / преследование", color: "#8B0000", count: 9 },
  { cx: 220, cy: 320, label: "архетип героя", color: "#E8E1D4", count: 6 },
  { cx: 420, cy: 360, label: "проводник", color: "#B87333", count: 5 },
  { cx: 110, cy: 360, label: "дом без стен", color: "#C9C2B5", count: 4 },
];

const DreamMap = () => {
  const points = useMemo(() => {
    const pts = [];
    CLUSTERS.forEach((c, ci) => {
      for (let i = 0; i < c.count; i++) {
        // seed pseudo-random
        const s1 = Math.sin(ci * 13.37 + i * 7.91) * 43758.5453;
        const s2 = Math.sin(ci * 19.19 + i * 11.13) * 12543.123;
        const a = (s1 - Math.floor(s1)) * Math.PI * 2;
        const r = (s2 - Math.floor(s2)) * 28 + 4;
        pts.push({
          x: c.cx + Math.cos(a) * r,
          y: c.cy + Math.sin(a) * r,
          color: c.color,
          size: 1.5 + ((s1 - Math.floor(s1)) * 2.2),
          op: 0.45 + ((s2 - Math.floor(s2)) * 0.55),
          cluster: ci,
        });
      }
    });
    // scattered ambient points
    for (let i = 0; i < 30; i++) {
      const sx = (Math.sin(i * 17.31) * 43758.5453);
      const sy = (Math.sin(i * 29.19) * 12543.123);
      pts.push({
        x: 60 + (sx - Math.floor(sx)) * 460,
        y: 80 + (sy - Math.floor(sy)) * 320,
        color: "#8B8578",
        size: 0.9,
        op: 0.25,
        cluster: -1,
      });
    }
    return pts;
  }, []);

  return (
    <div className="relative w-full">
      <div className="relative aspect-[16/10] w-full overflow-hidden border hairline" style={{ background: "var(--ink-2)" }}>
        {/* parchment grid */}
        <svg viewBox="0 0 600 440" preserveAspectRatio="xMidYMid slice" className="absolute inset-0 w-full h-full">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#E8E1D4" strokeWidth="0.3" opacity="0.06" />
            </pattern>
            <radialGradient id="cluster-glow-copper" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#B87333" stopOpacity="0.22" />
              <stop offset="100%" stopColor="#B87333" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="cluster-glow-cinnabar" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#8B0000" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#8B0000" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="cluster-glow-cream" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#E8E1D4" stopOpacity="0.12" />
              <stop offset="100%" stopColor="#E8E1D4" stopOpacity="0" />
            </radialGradient>
          </defs>

          <rect width="600" height="440" fill="url(#grid)" />

          {/* cluster halos */}
          {CLUSTERS.map((c, i) => {
            const glow = c.color === "#8B0000" ? "cluster-glow-cinnabar"
              : c.color === "#B87333" || c.color === "#D38A45" ? "cluster-glow-copper"
              : "cluster-glow-cream";
            return (
              <circle key={i} cx={c.cx} cy={c.cy} r="55" fill={`url(#${glow})`} />
            );
          })}

          {/* faint inter-cluster lines */}
          {CLUSTERS.map((c, i) =>
            CLUSTERS.slice(i + 1).map((c2, j) => {
              const dx = c.cx - c2.cx;
              const dy = c.cy - c2.cy;
              const d = Math.sqrt(dx * dx + dy * dy);
              if (d < 180) {
                return (
                  <line
                    key={`l-${i}-${j}`}
                    x1={c.cx}
                    y1={c.cy}
                    x2={c2.cx}
                    y2={c2.cy}
                    stroke="#B87333"
                    strokeWidth="0.4"
                    opacity="0.14"
                    strokeDasharray="2 4"
                  />
                );
              }
              return null;
            })
          )}

          {/* points */}
          {points.map((p, i) => (
            <circle
              key={i}
              cx={p.x}
              cy={p.y}
              r={p.size}
              fill={p.color}
              opacity={p.op}
              className={i % 4 === 0 ? "twinkle-2" : ""}
            />
          ))}

          {/* cluster labels */}
          {CLUSTERS.map((c, i) => (
            <g key={`label-${i}`}>
              <text
                x={c.cx}
                y={c.cy - 38}
                textAnchor="middle"
                fontFamily="EB Garamond, Georgia, serif"
                fontSize="13"
                fill="#E8E1D4"
                opacity="0.78"
                fontStyle="italic"
              >
                {c.label}
              </text>
            </g>
          ))}
        </svg>

        {/* HUD overlay */}
        <div className="absolute top-3 left-4 flex gap-3 items-center text-[11px] uppercase tracking-[0.18em]" style={{ color: "var(--stone)" }}>
          <span className="font-serif italic text-[14px] normal-case tracking-normal" style={{ color: "var(--cream)" }}>Dream Map</span>
          <span>·</span>
          <span>43 nodes</span>
          <span>·</span>
          <span>6 clusters</span>
        </div>
        <div className="absolute bottom-3 right-4 text-[10px] tracking-[0.18em] uppercase" style={{ color: "var(--stone)" }}>
          v · близость = смысл
        </div>
      </div>
    </div>
  );
};

export default DreamMap;
