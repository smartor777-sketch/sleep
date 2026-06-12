import { create } from 'zustand';
import { api, clearTokens, getDeviceId, getAccessToken } from './api';
import { applySettings, AccentSwatch, ACCENTS, FontSize, Lang, loadSettings, saveSettings, ThemeMode } from './settings';
import { BillingStatus, Dream, User, UserStats } from './types';

function needsOnboarding(user: User): boolean {
  return !user.profile?.onboarding_completed || !user.profile?.about_me;
}

interface AppState {
  // Auth
  user: User | null;
  bootstrapping: boolean;
  ready: boolean;

  // Settings
  theme: ThemeMode;
  accentId: string;
  fontSize: FontSize;
  lang: Lang;

  // Data caches
  billing: BillingStatus | null;
  stats: UserStats | null;
  dreams: Dream[];
  dreamsTotal: number;
  dreamsLoaded: boolean;

  // UI
  paywallOpen: boolean;
  paywallReason: string;
  upgradeBanner: { min_version?: string; download_url?: string } | null;
  onboardingOpen: boolean;
  authPromptOpen: boolean;

  // Actions
  bootstrap: () => Promise<void>;
  refreshUser: () => Promise<void>;
  refreshBilling: () => Promise<void>;
  refreshStats: () => Promise<void>;
  loadDreams: (reset?: boolean) => Promise<void>;
  addDreamToCache: (d: Dream) => void;
  updateDreamInCache: (d: Dream) => void;
  removeDreamFromCache: (id: string) => void;

  setTheme: (t: ThemeMode) => void;
  setAccent: (id: string) => void;
  setFontSize: (s: FontSize) => void;
  setLang: (l: Lang) => void;

  openPaywall: (reason?: string) => void;
  closePaywall: () => void;
  setUpgradeBanner: (info: { min_version?: string; download_url?: string } | null) => void;
  openOnboarding: () => void;
  closeOnboarding: () => void;
  openAuthPrompt: () => void;
  closeAuthPrompt: () => void;

  signOut: () => Promise<void>;
}

export const useApp = create<AppState>((set, get) => ({
  user: null,
  bootstrapping: true,
  ready: false,

  ...(() => {
    const s = loadSettings();
    return { theme: s.theme, accentId: s.accentId, fontSize: s.fontSize, lang: s.lang };
  })(),

  billing: null,
  stats: null,
  dreams: [],
  dreamsTotal: 0,
  dreamsLoaded: false,

  paywallOpen: false,
  paywallReason: '',
  upgradeBanner: null,
  onboardingOpen: false,
  authPromptOpen: false,

  bootstrap: async () => {
    set({ bootstrapping: true });
    getDeviceId(); // ensure exists
    try {
      if (getAccessToken()) {
        try {
          const u = await api.me();
          set({ user: u });
        } catch {
          await api.anonymous();
          const u = await api.me();
          set({ user: u });
        }
      } else {
        await api.anonymous();
        const u = await api.me();
        set({ user: u });
      }

      // billing in background (non-blocking)
      api.billingStatus().then((b) => set({ billing: b })).catch(() => {});

      const u = get().user;
      if (u) {
        if (needsOnboarding(u)) {
          set(u.is_anonymous
            ? { authPromptOpen: true, onboardingOpen: false }
            : { onboardingOpen: true, authPromptOpen: false });
        } else {
          set({ onboardingOpen: false, authPromptOpen: false });
        }
      }
    } catch (e) {
      // network or backend down — fail soft, UI still shows
      console.warn('Bootstrap failed:', e);
    } finally {
      set({ bootstrapping: false, ready: true });
    }
  },

  refreshUser: async () => {
    const u = await api.me();
    set({ user: u });
    if (needsOnboarding(u)) {
      set(u.is_anonymous
        ? { authPromptOpen: true, onboardingOpen: false }
        : { onboardingOpen: true, authPromptOpen: false });
    } else {
      set({ onboardingOpen: false, authPromptOpen: false });
    }
  },
  refreshBilling: async () => {
    const b = await api.billingStatus();
    set({ billing: b });
  },
  refreshStats: async () => {
    const s = await api.stats();
    set({ stats: s });
  },

  loadDreams: async (reset = false) => {
    if (reset) set({ dreamsLoaded: false });
    try {
      const data = await api.listDreams({ page: 1, page_size: 100 });
      set({ dreams: data.dreams, dreamsTotal: data.total, dreamsLoaded: true });
    } catch {
      set({ dreams: [], dreamsTotal: 0, dreamsLoaded: true });
    }
  },

  addDreamToCache: (d) => set((s) => ({ dreams: [d, ...s.dreams], dreamsTotal: s.dreamsTotal + 1 })),
  updateDreamInCache: (d) =>
    set((s) => ({ dreams: s.dreams.map((x) => (x.id === d.id ? { ...x, ...d } : x)) })),
  removeDreamFromCache: (id) =>
    set((s) => ({
      dreams: s.dreams.filter((x) => x.id !== id),
      dreamsTotal: Math.max(0, s.dreamsTotal - 1),
    })),

  setTheme: (t) => {
    set({ theme: t });
    const s = { theme: t, accentId: get().accentId, fontSize: get().fontSize, lang: get().lang };
    saveSettings(s); applySettings(s);
  },
  setAccent: (id) => {
    if (!ACCENTS.find((a) => a.id === id)) return;
    set({ accentId: id });
    const s = { theme: get().theme, accentId: id, fontSize: get().fontSize, lang: get().lang };
    saveSettings(s); applySettings(s);
  },
  setFontSize: (size) => {
    set({ fontSize: size });
    const s = { theme: get().theme, accentId: get().accentId, fontSize: size, lang: get().lang };
    saveSettings(s); applySettings(s);
  },
  setLang: (l) => {
    set({ lang: l });
    const s = { theme: get().theme, accentId: get().accentId, fontSize: get().fontSize, lang: l };
    saveSettings(s); applySettings(s);
  },

  openPaywall: (reason = '') => set({ paywallOpen: true, paywallReason: reason }),
  closePaywall: () => set({ paywallOpen: false, paywallReason: '' }),
  setUpgradeBanner: (info) => set({ upgradeBanner: info }),
  openOnboarding: () => set({ onboardingOpen: true }),
  closeOnboarding: () => set({ onboardingOpen: false }),
  openAuthPrompt: () => set({ authPromptOpen: true }),
  closeAuthPrompt: () => set({ authPromptOpen: false }),

  signOut: async () => {
    try { await api.logout(); } catch {}
    clearTokens();
    set({ user: null, dreams: [], dreamsTotal: 0, billing: null, stats: null, onboardingOpen: false, authPromptOpen: false });
    // re-bootstrap to anonymous
    await get().bootstrap();
  },
}));

export function currentAccent(): AccentSwatch {
  return ACCENTS.find((a) => a.id === useApp.getState().accentId) ?? ACCENTS[0];
}

// Expose the store on window for E2E/preview demos (dev only).
if (typeof window !== 'undefined' && (import.meta as any).env?.DEV) {
  (window as any).__innercore = { useApp };
}
