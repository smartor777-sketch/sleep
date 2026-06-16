import { MapNode } from './types';

export interface FittedMapNode extends MapNode {
  viewX: number;
  viewY: number;
}

export interface MapFit {
  nodes: FittedMapNode[];
  point: (p: { x: number; y: number }) => { viewX: number; viewY: number };
}

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

export function nodeImportance(n: MapNode) {
  return (n.dream_count || 0) * 4 + (n.occurrence_count || 0) + (n.size_weight || 0) * 10;
}

export function createMapFit(nodes: MapNode[], padding = 0.08): MapFit {
  if (nodes.length === 0) {
    return { nodes: [], point: () => ({ viewX: 0.5, viewY: 0.5 }) };
  }

  const xs = nodes.map((n) => n.x);
  const ys = nodes.map((n) => n.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const spreadX = maxX - minX;
  const spreadY = maxY - minY;
  const rangeX = Math.max(0.001, spreadX);
  const rangeY = Math.max(0.001, spreadY);
  const usable = 1 - padding * 2;

  function point(p: { x: number; y: number }) {
    const viewX = spreadX < 0.001 ? 0.5 : padding + ((p.x - minX) / rangeX) * usable;
    const viewY = spreadY < 0.001 ? 0.5 : padding + ((p.y - minY) / rangeY) * usable;
    return {
      viewX: clamp(viewX, padding, 1 - padding),
      viewY: clamp(viewY, padding, 1 - padding),
    };
  }

  return {
    nodes: nodes.map((n) => ({ ...n, ...point(n) })),
    point,
  };
}

export function previewLinks(nodes: FittedMapNode[], maxLinks = 14) {
  const links: { a: FittedMapNode; b: FittedMapNode }[] = [];
  const seen = new Set<string>();

  nodes.forEach((a) => {
    const nearest = nodes
      .filter((b) => b.id !== a.id)
      .map((b) => ({
        b,
        d: Math.hypot(a.viewX - b.viewX, a.viewY - b.viewY),
      }))
      .sort((x, y) => x.d - y.d)
      .slice(0, 2);

    nearest.forEach(({ b }) => {
      const key = [a.id, b.id].sort().join(':');
      if (!seen.has(key)) {
        seen.add(key);
        links.push({ a, b });
      }
    });
  });

  return links
    .sort((x, y) => {
      const ix = nodeImportance(x.a) + nodeImportance(x.b);
      const iy = nodeImportance(y.a) + nodeImportance(y.b);
      return iy - ix;
    })
    .slice(0, maxLinks);
}
