// Centralised API client.
// - Always sends X-App-Version on every request.
// - JWT Bearer, auto-refresh on 401 with single-flight queue.
// - Throws ApiError with status code & data for callers to inspect.

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';

const BASE_URL: string =
  (import.meta as any).env.VITE_API_BASE_URL || 'http://89.125.77.243:8080';
const APP_VERSION: string = (import.meta as any).env.VITE_APP_VERSION || '0.4.2';

const STORAGE = {
  device: 'innercore.device_id',
  access: 'innercore.access_token',
  refresh: 'innercore.refresh_token',
};

export function getDeviceId(): string {
  const existing = localStorage.getItem(STORAGE.device);
  if (existing) return existing;
  const uuid: string =
    (crypto as any).randomUUID?.() ??
    `${Date.now().toString(16)}-${Math.random().toString(16).slice(2, 10)}-${Math.random()
      .toString(16)
      .slice(2, 10)}`;
  localStorage.setItem(STORAGE.device, uuid);
  return uuid;
}

export function getAccessToken(): string | null {
  return localStorage.getItem(STORAGE.access);
}
export function getRefreshToken(): string | null {
  return localStorage.getItem(STORAGE.refresh);
}
export function setTokens(access: string, refresh: string) {
  localStorage.setItem(STORAGE.access, access);
  localStorage.setItem(STORAGE.refresh, refresh);
}
export function clearTokens() {
  localStorage.removeItem(STORAGE.access);
  localStorage.removeItem(STORAGE.refresh);
}

export class ApiError extends Error {
  status: number;
  data: any;
  detail?: string;
  constructor(message: string, status: number, data: any) {
    super(message);
    this.status = status;
    this.data = data;
    this.detail = (data && (data.detail || data.message)) || message;
  }
}

const http: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
});

let refreshing: Promise<string | null> | null = null;
let onUpgradeRequired: ((info: { min_version?: string; download_url?: string }) => void) | null =
  null;
let onForceLogout: (() => void) | null = null;

export function setApiHandlers(handlers: {
  onUpgradeRequired?: (info: any) => void;
  onForceLogout?: () => void;
}) {
  onUpgradeRequired = handlers.onUpgradeRequired ?? null;
  onForceLogout = handlers.onForceLogout ?? null;
}

http.interceptors.request.use((config) => {
  config.headers = config.headers ?? {};
  (config.headers as any)['X-App-Version'] = APP_VERSION;
  const token = getAccessToken();
  if (token && !(config as any).__skipAuth) {
    (config.headers as any)['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

async function tryRefresh(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;
  if (!refreshing) {
    refreshing = (async () => {
      try {
        const resp = await axios.post(
          `${BASE_URL}/api/v1/auth/refresh`,
          { refresh_token: refresh },
          { headers: { 'X-App-Version': APP_VERSION, 'Content-Type': 'application/json' } }
        );
        const { access_token, refresh_token } = resp.data;
        setTokens(access_token, refresh_token);
        return access_token as string;
      } catch (e) {
        clearTokens();
        onForceLogout?.();
        return null;
      } finally {
        refreshing = null;
      }
    })();
  }
  return refreshing;
}

http.interceptors.response.use(
  (r) => r,
  async (err: AxiosError<any>) => {
    const status = err.response?.status;
    const original: AxiosRequestConfig & { __retry?: boolean } = err.config ?? {};

    if (status === 426) {
      onUpgradeRequired?.(err.response?.data || {});
    }

    if (status === 401 && !original.__retry && !(original as any).__skipAuth) {
      original.__retry = true;
      const newToken = await tryRefresh();
      if (newToken) {
        original.headers = original.headers ?? {};
        (original.headers as any)['Authorization'] = `Bearer ${newToken}`;
        return http.request(original);
      }
    }

    const data = err.response?.data;
    throw new ApiError(err.message, status ?? 0, data);
  }
);

// Helpers
async function get<T>(url: string, params?: any) {
  const { data } = await http.get<T>(url, { params });
  return data;
}
async function post<T>(url: string, body?: any, opts?: AxiosRequestConfig) {
  const { data } = await http.post<T>(url, body, opts);
  return data;
}
async function put<T>(url: string, body?: any) {
  const { data } = await http.put<T>(url, body);
  return data;
}
async function patch<T>(url: string, body?: any) {
  const { data } = await http.patch<T>(url, body);
  return data;
}
async function del<T>(url: string) {
  const { data } = await http.delete<T>(url);
  return data;
}

// ===== Endpoints =====
import {
  User, Dream, DreamListResponse, Analysis, Message,
  DreamMap, SymbolDetail, BillingStatus, UserStats,
} from './types';

export const api = {
  // ---- Auth ----
  appVersion: () => get<{ version: string; download_url: string }>('/api/v1/app/version'),

  anonymous: async () => {
    const data = await post<{ access_token: string; refresh_token: string; user: User }>(
      '/api/v1/auth/anonymous',
      { device_id: getDeviceId(), platform: 'web', app_version: APP_VERSION },
      { __skipAuth: true } as any
    );
    setTokens(data.access_token, data.refresh_token);
    return data;
  },

  register: async (payload: {
    email: string; password: string; first_name?: string; last_name?: string; timezone?: string;
  }) => {
    const data = await post<{ access_token: string; refresh_token: string; token_type: string }>(
      '/api/v1/auth/register',
      payload,
      { __skipAuth: true } as any
    );
    return data;
  },

  login: async (email: string, password: string) => {
    const data = await post<{ access_token: string; refresh_token: string; token_type: string }>(
      '/api/v1/auth/login',
      { email, password },
      { __skipAuth: true } as any
    );
    return data;
  },

  verifyEmailCode: (email: string, code: string) =>
    post<{ message: string }>('/api/v1/auth/verify-email-code', { email, code }, { __skipAuth: true } as any),

  resendCode: (email: string) =>
    post<{ message: string }>('/api/v1/auth/resend-code', { email }, { __skipAuth: true } as any),

  forgotPassword: (email: string) =>
    post<{ message: string }>('/api/v1/auth/forgot-password', { email }, { __skipAuth: true } as any),

  mergeAnonymous: (anonymous_device_id: string) =>
    post<{ message: string }>('/api/v1/auth/merge-anonymous', { anonymous_device_id }),

  deleteAccount: () => del<{ message: string }>('/api/v1/auth/account'),
  logout: () => post<{ message: string }>('/api/v1/auth/logout', {}),

  // ---- User ----
  me: () => get<User>('/api/v1/users/me'),
  updateMe: (body: { self_description?: string; timezone?: string; onboarding_completed?: boolean }) =>
    put<User>('/api/v1/users/me', body),

  // ---- Dreams ----
  createDream: (body: { content: string; title?: string; emoji?: string; comment?: string }) =>
    post<Dream>('/api/v1/dreams', body),
  listDreams: (params?: { page?: number; page_size?: number; date?: string }) =>
    get<DreamListResponse>('/api/v1/dreams', params),
  searchDreams: (q: string, mode: 'semantic' | 'lexical' = 'semantic') =>
    get<{ dreams: Dream[]; total: number; query: string; mode: string }>(
      '/api/v1/dreams/search', { q, mode }
    ),
  getDream: (id: string) => get<Dream>(`/api/v1/dreams/${id}`),
  updateDream: (id: string, body: Partial<Pick<Dream, 'title' | 'content' | 'emoji' | 'comment' | 'created_at'>>) =>
    patch<Dream>(`/api/v1/dreams/${id}`, body),
  deleteDream: (id: string) => del<{ message: string }>(`/api/v1/dreams/${id}`),

  // ---- Analysis ----
  startAnalysis: (dream_id: string) =>
    post<{ analysis_id: string; task_id: string; status: string; message: string }>(
      '/api/v1/analyses', { dream_id }
    ),
  taskStatus: (task_id: string) =>
    get<{ task_id: string; status: string; result?: any; error?: string; progress?: number }>(
      `/api/v1/analyses/task/${task_id}`
    ),
  analysisForDream: (dream_id: string) =>
    get<Analysis>(`/api/v1/analyses/dream/${dream_id}`),

  // ---- Messages (chat) ----
  sendMessage: (dream_id: string, content: string) =>
    post<{ task_id: string; status: string; user_message: Message }>(
      '/api/v1/messages', { dream_id, content }
    ),
  messageHistory: (dream_id: string, limit = 100, offset = 0) =>
    get<{ messages: Message[]; total: number }>(
      `/api/v1/messages/dream/${dream_id}`, { limit, offset }
    ),
  messageTaskStatus: (task_id: string) =>
    get<{ task_id: string; status: string; result?: any; error?: string }>(
      `/api/v1/messages/task/${task_id}`
    ),

  // ---- Map ----
  getMap: (user_id: string, params?: Record<string, any>) =>
    get<DreamMap>(`/api/v1/map/${user_id}`, params),
  getSymbol: (user_id: string, symbol_id: string) =>
    get<SymbolDetail>(`/api/v1/map/${user_id}/symbol/${symbol_id}`),

  // ---- Stats / Billing ----
  stats: () => get<UserStats>('/api/v1/stats/me'),
  billingStatus: () => get<BillingStatus>('/api/v1/billing/status'),

  // ---- Audio ----
  transcribe: async (file: Blob, language?: string) => {
    const fd = new FormData();
    fd.append('file', file, 'audio.webm');
    if (language) fd.append('language', language);
    const { data } = await http.post<{
      text: string; partial: boolean; segments_total: number; segments_ok: number; segments_failed: number;
    }>('/api/v1/audio/transcriptions', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },
};
