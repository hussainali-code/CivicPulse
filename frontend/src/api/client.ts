import {
  ApiError,
  ApiErrorDetail,
  Complaint,
  ComplaintCreate,
  ComplaintListResponse,
  ProviderMetaResponse,
  StatsResponse,
  Status,
} from './types';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
    let errorDetails: ApiErrorDetail[] | undefined = undefined;
    let retryAfter: number | undefined = undefined;

    if (response.status === 429) {
      const retryHeader = response.headers.get('Retry-After');
      if (retryHeader) {
        retryAfter = parseInt(retryHeader, 10);
      }
    }

    try {
      const errorJson = await response.json();
      if (typeof errorJson.detail === 'string') {
        errorMessage = errorJson.detail;
      } else if (Array.isArray(errorJson.detail)) {
        // FastAPI / Pydantic validation error array
        errorDetails = errorJson.detail.map((d: any) => ({
          field: Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : undefined,
          msg: d.msg,
        }));
        errorMessage = errorDetails?.map((e) => (e.field ? `${e.field}: ${e.msg}` : e.msg)).join('; ') || errorMessage;
      }
    } catch {
      // Body not JSON
    }

    throw new ApiError(response.status, errorMessage, errorDetails, retryAfter);
  }

  return response.json() as Promise<T>;
}

export const api = {
  async createComplaint(payload: ComplaintCreate): Promise<Complaint> {
    const res = await fetch('/api/complaints', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<Complaint>(res);
  },

  async getComplaints(params?: {
    category?: string;
    priority?: string;
    status?: string;
    page?: number;
    page_size?: number;
  }): Promise<ComplaintListResponse> {
    const url = new URL('/api/complaints', window.location.origin);
    if (params?.category) url.searchParams.set('category', params.category);
    if (params?.priority) url.searchParams.set('priority', params.priority);
    if (params?.status) url.searchParams.set('status', params.status);
    if (params?.page) url.searchParams.set('page', params.page.toString());
    if (params?.page_size) url.searchParams.set('page_size', params.page_size.toString());

    const res = await fetch(url.pathname + url.search);
    return handleResponse<ComplaintListResponse>(res);
  },

  async getComplaintById(id: string): Promise<Complaint> {
    const res = await fetch(`/api/complaints/${id}`);
    return handleResponse<Complaint>(res);
  },

  async updateComplaintStatus(id: string, status: Status): Promise<Complaint> {
    const res = await fetch(`/api/complaints/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    });
    return handleResponse<Complaint>(res);
  },

  async getStats(): Promise<{ data: StatsResponse; xCache: string }> {
    const res = await fetch('/api/stats');
    const xCache = res.headers.get('X-Cache') || 'MISS';
    const data = await handleResponse<StatsResponse>(res);
    return { data, xCache };
  },

  async getProviderMeta(): Promise<ProviderMetaResponse> {
    const res = await fetch('/api/meta/providers');
    return handleResponse<ProviderMetaResponse>(res);
  },
};
