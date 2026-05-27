import React, { useMemo } from "react";

/**
 * Animated SVG sphere — dream points orbiting on a wire-frame sphere.
 * Pure SVG, no canvas, no three.js. Lightweight, accessible.
 */
const Sphere = () => {
  // Deterministic dream points (lat/lng → 2D projection)
  const points = useMemo(() => {
    const pts = [];
    const PHI = Math.PI * (3 - Math.sqrt(5)); // golden angle
    const N = 64;
    for (let i = 0; i < N; i++) {
      const y = 1 - (i / (N - 1)) * 2;
      const radius = Math.sqrt(1 - y * y);
      const theta = PHI * i;
      const x = Math.cos(theta) * radius;
      const z = Math.sin(theta) * radius;
      // soft random tint
      const seed = (i * 9301 + 49297) % 233280 / 233280;
      pts.push({
        x, y, z,
        r: 1.4 + ((i * 17) % 7) * 0.18,
        tint: seed > 0.78 ? "cinnabar" : seed > 0.42 ? "copper" : "cream",
        delay: (i % 11) * 0.4,
      });
    }
    return pts;
  }, []);

  // project sphere of unit radius to viewBox 400x400, center 200,200, R=170
  const R = 170;
  const cx = 200;
  const cy = 200;

  const colorFor = (t) => {
    if (t === "cinnabar") return "#8B0000";
    if (t === "copper") return "#B87333";
    return "#E8E1D4";
  };

  // wire frame meridians
  const meridians = [];
  for (let m = 0; m < 8; m++) {
    const angle = (m / 8) * Math.PI;
    const path = [];
    for (let t = 0; t <= 60; t++) {
      const phi = (t / 60) * Math.PI - Math.PI / 2;
      const x = Math.cos(phi) * Math.cos(angle);
      const y = Math.sin(phi);
      // const z = Math.cos(phi) * Math.sin(angle);
      path.push(`${cx + x * R},${cy + y * R}`);
    }
    meridians.push(path.join(" "));
  }
  // parallels
  const parallels = [];
  for (let p = 1; p < 6; p++) {
    const phi = (p / 6) * Math.PI - Math.PI / 2;
    const ry = Math.cos(phi) * R;
    const yPos = cy + Math.sin(phi) * R;
    parallels.push({ ry, yPos });
  }

  return (
    <div className="relative w-full aspect-square max-w-[560px] mx-auto" aria-hidden="true">
      {/* outer faint ring */}
      <svg viewBox="0 0 400 400" className="absolute inset-0 w-full h-full">
        <defs>
          <radialGradient id="halo" cx="50%" cy="50%" r="50%">
            <stop offset="60%" stopColor="#B87333" stopOpacity="0" />
            <stop offset="92%" stopColor="#B87333" stopOpacity="0.06" />
            <stop offset="100%" stopColor="#B87333" stopOpacity="0" />
          </radialGradient>
          <filter id="soft" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="1.2" />
          </filter>
        </defs>

        <circle cx={cx} cy={cy} r={R + 24} fill="url(#halo)" />

        {/* outer hairline circle with tick marks */}
        <g opacity="0.32">
          <circle cx={cx} cy={cy} r={R + 14} fill="none" stroke="#E8E1D4" strokeWidth="0.4" />
          {Array.from({ length: 24 }).map((_, i) => {
            const a = (i / 24) * Math.PI * 2;
            const r1 = R + 12;
            const r2 = R + 18;
            const x1 = cx + Math.cos(a) * r1;
            const y1 = cy + Math.sin(a) * r1;
            const x2 = cx + Math.cos(a) * r2;
            const y2 = cy + Math.sin(a) * r2;
            return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#E8E1D4" strokeWidth="0.4" />;
          })}
        </g>

        {/* rotating wire-frame sphere */}
        <g className="rotate-slow" style={{ transformOrigin: "200px 200px" }}>
          {/* meridians */}
          {meridians.map((d, i) => (
            <polyline key={i} points={d} fill="none" stroke="#8B8578" strokeWidth="0.35" opacity="0.32" />
          ))}
          {/* parallels */}
          {parallels.map((p, i) => (
            <ellipse key={i} cx={cx} cy={p.yPos} rx={p.ry} ry={p.ry * 0.18} fill="none" stroke="#8B8578" strokeWidth="0.3" opacity="0.22" />
          ))}
        </g>

        {/* counter-rotating constellations layer with dream points */}
        <g className="rotate-slower" style={{ transformOrigin: "200px 200px" }}>
          {/* faint constellation lines connecting clusters */}
          {(() => {
            const lines = [];
            for (let i = 0; i < points.length; i++) {
              for (let j = i + 1; j < points.length; j++) {
                const dx = points[i].x - points[j].x;
                const dy = points[i].y - points[j].y;
                const dz = points[i].z - points[j].z;
                const d = Math.sqrt(dx * dx + dy * dy + dz * dz);
                if (d < 0.35 && Math.abs(points[i].z + points[j].z) > 0) {
                  if (points[i].z > -0.1 && points[j].z > -0.1) {
                    lines.push(
                      <line
                        key={`${i}-${j}`}
                        x1={cx + points[i].x * R}
                        y1={cy + points[i].y * R}
                        x2={cx + points[j].x * R}
                        y2={cy + points[j].y * R}
                        className="constellation-line"
                      />
                    );
                  }
                }
              }
            }
            return lines;
          })()}

          {/* dream points — z-sorted (back to front) */}
          {points
            .slice()
            .sort((a, b) => a.z - b.z)
            .map((p, idx) => {
              const x = cx + p.x * R;
              const y = cy + p.y * R;
              const depth = (p.z + 1) / 2; // 0..1, 1 = front
              const opacity = 0.25 + depth * 0.7;
              const size = 1 + p.r * (0.5 + depth * 0.9);
              return (
                <circle
                  key={idx}
                  cx={x}
                  cy={y}
                  r={size}
                  fill={colorFor(p.tint)}
                  opacity={opacity}
                  className={`dream-point ${idx % 3 === 0 ? "twinkle" : idx % 3 === 1 ? "twinkle-2" : "twinkle-3"}`}
                  style={{ animationDelay: `${p.delay}s` }}
                />
              );
            })}
        </g>

        {/* static center marker — alchemical self */}
        <g opacity="0.85">
          <circle cx={cx} cy={cy} r="2" fill="#B87333" />
          <circle cx={cx} cy={cy} r="6" fill="none" stroke="#B87333" strokeWidth="0.5" opacity="0.45" />
        </g>
      </svg>
    </div>
  );
};

export default Sphere;
