import React, { useEffect, useRef } from "react";

/**
 * FractalDots — canvas background of slowly drifting dots,
 * connected with hairlines when close. A subtle alchemical lattice.
 *
 * Props:
 *   variant: "copper" | "cinnabar" — accent tint
 *   density: number of dots (~30-80)
 *   opacity: overall multiplier 0..1
 */
const FractalDots = ({ variant = "copper", density = 56, opacity = 1 }) => {
  const canvasRef = useRef(null);
  const rafRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const parent = canvas.parentElement;
    let W = 0, H = 0, dpr = Math.min(window.devicePixelRatio || 1, 2);

    const accent =
      variant === "cinnabar"
        ? { r: 139, g: 0, b: 0, line: "rgba(184, 115, 51, 0.10)", dot: "rgba(232, 225, 212, " }
        : { r: 184, g: 115, b: 51, line: "rgba(184, 115, 51, 0.12)", dot: "rgba(232, 225, 212, " };

    const resize = () => {
      const rect = parent.getBoundingClientRect();
      W = Math.max(320, rect.width);
      H = Math.max(320, rect.height);
      canvas.width = W * dpr;
      canvas.height = H * dpr;
      canvas.style.width = `${W}px`;
      canvas.style.height = `${H}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();

    const ro = new ResizeObserver(resize);
    ro.observe(parent);

    // particle field
    const pts = Array.from({ length: density }).map((_, i) => {
      const seed = (i * 9301 + 49297) % 233280 / 233280;
      const seed2 = (i * 1597 + 51749) % 233280 / 233280;
      return {
        x: seed * W,
        y: seed2 * H,
        vx: (Math.sin(i * 1.7) * 0.18),
        vy: (Math.cos(i * 2.3) * 0.18),
        r: 0.7 + ((i * 7) % 5) * 0.35,
        phase: seed * Math.PI * 2,
        accent: i % 13 === 0, // few accent-colored dots
      };
    });

    // pause when offscreen
    let running = true;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => (running = e.isIntersecting));
      },
      { threshold: 0 }
    );
    io.observe(parent);

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const CONNECT = 150; // px

    let t0 = performance.now();
    const tick = (t) => {
      const dt = Math.min(40, t - t0) / 16.6;
      t0 = t;
      if (!running) {
        rafRef.current = requestAnimationFrame(tick);
        return;
      }
      ctx.clearRect(0, 0, W, H);

      // fractal warp via sine field — gives drifting feel
      const tw = t / 4200;
      for (let i = 0; i < pts.length; i++) {
        const p = pts[i];
        if (!reducedMotion) {
          // base drift
          p.x += p.vx * dt;
          p.y += p.vy * dt;
          // fractal-ish micro-perturbation
          p.x += Math.sin(tw + p.phase + p.y * 0.012) * 0.18;
          p.y += Math.cos(tw * 0.8 + p.phase + p.x * 0.011) * 0.18;
        }
        // wrap
        if (p.x < -20) p.x = W + 20;
        else if (p.x > W + 20) p.x = -20;
        if (p.y < -20) p.y = H + 20;
        else if (p.y > H + 20) p.y = -20;
      }

      // lines
      ctx.lineWidth = 0.7;
      for (let i = 0; i < pts.length; i++) {
        for (let j = i + 1; j < pts.length; j++) {
          const a = pts[i], b = pts[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const d2 = dx * dx + dy * dy;
          if (d2 < CONNECT * CONNECT) {
            const alpha = (1 - Math.sqrt(d2) / CONNECT) * 0.42 * opacity;
            ctx.strokeStyle = `rgba(${accent.r}, ${accent.g}, ${accent.b}, ${alpha})`;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      // dots
      for (let i = 0; i < pts.length; i++) {
        const p = pts[i];
        const breathe = reducedMotion ? 1 : 0.85 + 0.15 * Math.sin(t / 900 + p.phase);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r * breathe, 0, Math.PI * 2);
        if (p.accent) {
          ctx.fillStyle = `rgba(${accent.r}, ${accent.g}, ${accent.b}, ${0.85 * opacity})`;
        } else {
          ctx.fillStyle = `${accent.dot}${0.55 * opacity})`;
        }
        ctx.fill();
      }

      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(rafRef.current);
      ro.disconnect();
      io.disconnect();
    };
  }, [variant, density, opacity]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="absolute inset-0 w-full h-full pointer-events-none"
      style={{ opacity: 0.85 }}
    />
  );
};

export default FractalDots;
