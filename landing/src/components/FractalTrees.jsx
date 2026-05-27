import React, { useEffect, useRef } from "react";

/**
 * FractalTrees — recursive L-system trees growing from left and right edges.
 * Branches sprout in waves, fade slowly, regrow. Subtle copper alchemical lattice.
 */
const FractalTrees = () => {
  const canvasRef = useRef(null);
  const rafRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const parent = canvas.parentElement;
    let W = 0, H = 0, dpr = Math.min(window.devicePixelRatio || 1, 2);

    const resize = () => {
      const rect = parent.getBoundingClientRect();
      W = Math.max(360, rect.width);
      H = Math.max(360, rect.height);
      canvas.width = W * dpr;
      canvas.height = H * dpr;
      canvas.style.width = `${W}px`;
      canvas.style.height = `${H}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(parent);

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // pause when offscreen
    let running = true;
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => (running = e.isIntersecting)),
      { threshold: 0 }
    );
    io.observe(parent);

    /** Build a static branch skeleton (so growth animation is just revealing segments) */
    const buildTree = (originX, originY, baseAngle, scale) => {
      const segs = []; // {x1,y1,x2,y2,depth,index,len}
      let counter = 0;
      const recurse = (x, y, angle, length, depth) => {
        if (depth < 0 || length < 4) return;
        // random fork seed
        const seed = Math.sin(counter * 12.9898 + originX * 0.31) * 43758.5453;
        const jitter = (seed - Math.floor(seed) - 0.5) * 0.18;
        const x2 = x + Math.cos(angle) * length;
        const y2 = y + Math.sin(angle) * length;
        counter++;
        segs.push({ x1: x, y1: y, x2, y2, depth, idx: counter, len: length });
        if (depth === 0) return;
        // branching: 2 branches with slight asymmetry
        const spread = 0.42 + jitter;
        recurse(x2, y2, angle - spread, length * 0.72, depth - 1);
        recurse(x2, y2, angle + spread + jitter * 0.5, length * 0.7, depth - 1);
        // occasional third branch
        const seed2 = Math.sin(counter * 7.13 + 91.7) * 43758.5453;
        if ((seed2 - Math.floor(seed2)) > 0.66) {
          recurse(x2, y2, angle + jitter * 0.8, length * 0.55, depth - 2);
        }
      };
      recurse(originX, originY, baseAngle, 80 * scale, 7);
      // sort by depth-distance for cleaner sequential growth
      return segs;
    };

    /** Trees per side; we'll regenerate every ~14s for variety */
    let trees = [];
    let cycleStart = 0;
    const CYCLE_MS = 16000; // full grow + fade cycle

    const generateTrees = () => {
      const s = Math.min(1.2, Math.max(0.7, H / 720));
      const lefts = [
        { x: 0, y: H * 0.78, angle: -Math.PI / 2 - 0.35, scale: s * 1.1 },
        { x: 0, y: H * 0.45, angle: 0 + 0.08, scale: s * 0.9 },
      ];
      const rights = [
        { x: W, y: H * 0.82, angle: -Math.PI / 2 + 0.35, scale: s * 1.05 },
        { x: W, y: H * 0.42, angle: Math.PI - 0.05, scale: s * 0.85 },
      ];
      trees = [...lefts, ...rights].map((t) => ({
        ...t,
        segs: buildTree(t.x, t.y, t.angle, t.scale),
      }));
    };

    generateTrees();
    cycleStart = performance.now();

    const draw = (now) => {
      if (!running) {
        rafRef.current = requestAnimationFrame(draw);
        return;
      }

      ctx.clearRect(0, 0, W, H);

      let cycleT = ((now - cycleStart) % CYCLE_MS) / CYCLE_MS; // 0..1
      // if regenerate point reached
      if (reducedMotion) cycleT = 1;

      // growth phase: 0..0.55 grow, 0.55..0.85 hold, 0.85..1 fade
      const growthEnd = 0.55;
      const fadeStart = 0.85;
      const growth = Math.min(1, cycleT / growthEnd); // 0..1
      const fade = cycleT > fadeStart ? 1 - (cycleT - fadeStart) / (1 - fadeStart) : 1;

      // regenerate after cycle
      if (!reducedMotion && now - cycleStart > CYCLE_MS) {
        generateTrees();
        cycleStart = now;
      }

      ctx.lineCap = "round";

      for (const tree of trees) {
        const segs = tree.segs;
        const maxIdx = segs.length;
        // reveal up to growth*maxIdx
        const revealCount = Math.floor(growth * maxIdx);
        for (let i = 0; i < revealCount; i++) {
          const s = segs[i];
          // branch thickness based on depth
          const thickness = 0.4 + s.depth * 0.32;
          // alpha based on depth and fade
          const baseAlpha = (0.12 + s.depth * 0.06) * fade;
          // copper tint
          ctx.strokeStyle = `rgba(184, 115, 51, ${baseAlpha})`;
          ctx.lineWidth = thickness;
          ctx.beginPath();
          ctx.moveTo(s.x1, s.y1);
          ctx.lineTo(s.x2, s.y2);
          ctx.stroke();
        }
        // edge tip currently growing — last segment partial
        if (revealCount < maxIdx && revealCount > 0) {
          const s = segs[revealCount];
          const localT = (growth * maxIdx) - revealCount;
          const tx = s.x1 + (s.x2 - s.x1) * localT;
          const ty = s.y1 + (s.y2 - s.y1) * localT;
          ctx.strokeStyle = `rgba(211, 138, 69, ${0.6 * fade})`;
          ctx.lineWidth = 0.6;
          ctx.beginPath();
          ctx.moveTo(s.x1, s.y1);
          ctx.lineTo(tx, ty);
          ctx.stroke();
          // glowing tip
          ctx.fillStyle = `rgba(232, 225, 212, ${0.7 * fade})`;
          ctx.beginPath();
          ctx.arc(tx, ty, 1.5, 0, Math.PI * 2);
          ctx.fill();
        }

        // little "leaves" — small dots at terminal points (depth 0)
        if (growth > 0.3) {
          for (let i = 0; i < revealCount; i++) {
            const s = segs[i];
            if (s.depth === 0) {
              const a = 0.55 * fade * Math.min(1, (growth - 0.3) * 2);
              ctx.fillStyle = `rgba(232, 225, 212, ${a})`;
              ctx.beginPath();
              ctx.arc(s.x2, s.y2, 1.3, 0, Math.PI * 2);
              ctx.fill();
            }
          }
        }
      }

      rafRef.current = requestAnimationFrame(draw);
    };

    rafRef.current = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(rafRef.current);
      ro.disconnect();
      io.disconnect();
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="absolute inset-0 w-full h-full pointer-events-none"
      style={{ opacity: 1 }}
    />
  );
};

export default FractalTrees;
