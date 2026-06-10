// Visual settings: theme (dark/light), accent color, font size, language
// Persisted in localStorage and applied as CSS variables / data attributes.

export type ThemeMode = 'dark' | 'light';
export type FontSize = 'small' | 'medium' | 'large';
export type Lang = 'ru' | 'en';

export interface AccentSwatch {
  id: string;
  hex: string;          // base accent
  softHex: string;      // softer/derived for emphasis text
}

export const ACCENTS: AccentSwatch[] = [
  { id: 'purple', hex: '#673AB7', softHex: '#9F7AEA' },
  { id: 'teal',   hex: '#26A69A', softHex: '#4DD0C4' },
  { id: 'amber',  hex: '#FA9042', softHex: '#FFB976' },
  { id: 'pink',   hex: '#E91E63', softHex: '#F48FB1' },
  { id: 'blue',   hex: '#42A5F5', softHex: '#82C4FF' },
];

const FONT_SCALE: Record<FontSize, number> = {
  small: 0.92,
  medium: 1,
  large: 1.12,
};

const KEY = 'innercore.settings.v1';

interface Settings {
  theme: ThemeMode;
  accentId: string;
  fontSize: FontSize;
  lang: Lang;
}

const DEFAULT: Settings = {
  theme: 'light',
  accentId: 'amber',
  fontSize: 'medium',
  lang: 'ru',
};

export function loadSettings(): Settings {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return { ...DEFAULT };
    const parsed = JSON.parse(raw);
    return { ...DEFAULT, ...parsed };
  } catch {
    return { ...DEFAULT };
  }
}

export function saveSettings(s: Settings) {
  localStorage.setItem(KEY, JSON.stringify(s));
}

function hexToRgb(hex: string): string {
  const clean = hex.replace('#', '');
  const r = parseInt(clean.slice(0, 2), 16);
  const g = parseInt(clean.slice(2, 4), 16);
  const b = parseInt(clean.slice(4, 6), 16);
  return `${r} ${g} ${b}`;
}

export function applySettings(s: Settings) {
  const root = document.documentElement;
  root.setAttribute('data-theme', s.theme);
  root.style.setProperty('--font-scale', String(FONT_SCALE[s.fontSize]));

  const accent = ACCENTS.find(a => a.id === s.accentId) ?? ACCENTS[0];
  root.style.setProperty('--accent', hexToRgb(accent.hex));
  root.style.setProperty('--accent-soft', hexToRgb(accent.softHex));
  root.setAttribute('lang', s.lang);
}

export function initSettingsFromStorage() {
  applySettings(loadSettings());
}
