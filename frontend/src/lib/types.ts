// Domain types matching backend contracts.

export interface AuthUser {
  id: string;
  is_anonymous: boolean;
  email: string | null;
}

export interface ProviderIdentity {
  provider: string;
  provider_subject: string;
  email: string | null;
}

export interface LinkResponse {
  linked: boolean;
  user: AuthUser;
  provider_identity: ProviderIdentity;
}

export interface User {
  id: string;
  email: string | null;
  is_anonymous: boolean;
  email_verified?: boolean;
  sub_type?: 'free' | 'trial' | 'pro';
  linked_providers?: string[];
  profile?: { about_me?: string; onboarding_completed?: boolean };
}

export type AnalysisStatus = 'saved' | 'analyzing' | 'analyzed' | 'analysis_failed';

export interface Dream {
  id: string;
  user_id: string;
  title: string | null;
  content: string;
  emoji?: string;
  comment?: string;
  recorded_at?: string;
  created_at: string;
  updated_at?: string;
  has_analysis: boolean;
  analysis_status: AnalysisStatus;
  analysis_error_message?: string | null;
  gradient_color_1?: string | null;
  gradient_color_2?: string | null;
}

export interface PageMeta {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DreamListResponse extends PageMeta {
  dreams: Dream[];
}

export interface Analysis {
  id: string;
  dream_id: string;
  user_id: string;
  result: string | null;
  status: string;
  error_message?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface Message {
  id: string;
  user_id: string;
  dream_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface MapNode {
  id: string;
  symbol_name: string;
  display_label: string;
  x: number;
  y: number;
  z: number;
  cluster_id: number;
  cluster_label: string;
  archetype_color: string;
  cosine_sim_to_center: number;
  size_weight: number;
  occurrence_count: number;
  dream_count: number;
  last_seen_at: string;
  preview_text: string;
  related_archetypes: string[];
}

export interface MapCluster {
  id: number;
  label: string;
  color: string;
  count: number;
  center: { x: number; y: number };
}

export interface DreamMap {
  nodes: MapNode[];
  clusters: MapCluster[];
  archetype_filters: string[];
  meta: {
    total_nodes: number;
    total_clusters: number;
    cached: boolean;
    computed_with: string;
    cluster_method: string;
    min_nodes_required: number;
  };
}

export interface SymbolDetail extends MapNode {
  related_symbols: { id: string; symbol_name: string; display_label?: string }[];
  occurrences: { dream_id: string; date: string; text_preview: string }[];
}

export interface BillingStatus {
  sub_type: 'free' | 'trial' | 'pro';
  sub_expires_at: string | null;
  trial_days_left: number;
  analyses_left_this_week: number | null;
  active_subscription: { product_id: string; expires_at: string } | null;
}

export interface UserStats {
  total_dreams: number;
  streak_days: number;
  dreams_by_weekday: Record<string, number>;
  dreams_last_14_days: { date: string; count: number }[];
  archetypes_top: { name: string; count: number }[];
  avg_time_of_day: string | null;
}
