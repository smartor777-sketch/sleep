import { useEffect, useRef } from 'react';
import { useApp } from '../lib/store';
import { api } from '../lib/api';

// Global poller for any dream currently in "analyzing" state. It covers pages
// that don't run their own polling (Today, Dreams, Map, ...) so the auto-analysis
// that starts on POST /dreams keeps the cache fresh and flips status to
// analyzed/analysis_failed as soon as the backend finishes.
export default function GlobalAnalysisPoller() {
  const dreams = useApp((s) => s.dreams);
  const updateDream = useApp((s) => s.updateDreamInCache);

  const analyzingIdsRef = useRef<string[]>([]);
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const analyzingIds = dreams
    .filter((d) => d.analysis_status === 'analyzing')
    .map((d) => d.id);

  useEffect(() => {
    // Stop polling dreams that left the analyzing state
    const active = new Set(analyzingIds);
    for (const [id, t] of timersRef.current) {
      if (!active.has(id)) {
        clearTimeout(t);
        timersRef.current.delete(id);
      }
    }

    // Start polling newly added analyzing dreams
    for (const id of analyzingIds) {
      if (analyzingIdsRef.current.includes(id)) continue;
      if (timersRef.current.has(id)) continue;
      analyzingIdsRef.current.push(id);
      poll(id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [analyzingIds.join(',')]);

  function poll(id: string) {
    const tick = async () => {
      try {
        const d = await api.getDream(id);
        updateDream(d);
        if (d.analysis_status !== 'analyzing') {
          const t = timersRef.current.get(id);
          if (t) clearTimeout(t);
          timersRef.current.delete(id);
          analyzingIdsRef.current = analyzingIdsRef.current.filter((x) => x !== id);
          return;
        }
      } catch {
        // keep trying
      }
      timersRef.current.set(id, setTimeout(tick, 3000));
    };
    timersRef.current.set(id, setTimeout(tick, 500));
  }

  useEffect(() => {
    return () => {
      for (const t of timersRef.current.values()) clearTimeout(t);
      timersRef.current.clear();
      analyzingIdsRef.current = [];
    };
  }, []);

  return null;
}