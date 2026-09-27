export type Category = 'water' | 'electricity' | 'sanitation' | 'roads' | 'streetlights' | 'other';
export type Priority = 'high' | 'normal' | 'low';
export type Status = 'open' | 'in_progress' | 'resolved' | 'rejected';

export interface Complaint {
  id: string;
  text: string;
  location: string;
  reporter_contact?: string | null;
  category: Category;
  priority: Priority;
  status: Status;
  ai_summary?: string | null;
  triaged_by: string;
  triage_latency_ms: number;
  created_at: string;
  updated_at: string;
}

export interface ComplaintCreate {
  text: string;
  location: string;
  reporter_contact?: string | null;
}

export interface ComplaintListResponse {
  items: Complaint[];
  total: number;
  page: number;
  page_size: number;
}

export interface StatusPatch {
  status: Status;
}

export interface StatsResponse {
  by_category: Record<string, number>;
  by_priority: Record<string, number>;
  by_status: Record<string, number>;
  total: {
    total: number;
  };
}

export interface ProviderOutcome {
  provider: string;
  latency_ms: number;
  fallback: boolean;
  created_at?: string | null;
}

export interface ProviderMetaResponse {
  active_provider: string;
  outcomes: ProviderOutcome[];
}

export interface ApiErrorDetail {
  field?: string;
  msg?: string;
}

export class ApiError extends Error {
  public status: number;
  public details?: ApiErrorDetail[];
  public retryAfter?: number;

  constructor(status: number, message: string, details?: ApiErrorDetail[], retryAfter?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
    this.retryAfter = retryAfter;
  }
}
