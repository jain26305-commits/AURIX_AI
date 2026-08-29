import { ApiError, ApiErrorDetails, ApiMode } from '@/types/api.types';

const BASE_URL = process.env.NEXT_PUBLIC_AURIX_API_URL || 'http://localhost:8000/api/v1';

export class ApiClient {
  public static getBaseUrl(): string {
    return BASE_URL;
  }

  public static getMode(): ApiMode {
    const envMode = process.env.NEXT_PUBLIC_AURIX_API_MODE;
    if (envMode === 'MOCK' || envMode === 'PRODUCTION') {
      return envMode;
    }
    return 'PRODUCTION';
  }

  public static getTenantId(): string {
    if (typeof window !== 'undefined') {
      return (
        localStorage.getItem('aurix_active_tenant') ||
        localStorage.getItem('aurix_tenant_id') ||
        'Aurix_Ai'
      );
    }
    return 'Aurix_Ai';
  }

  public static setTenantId(tenantId: string | null): void {
    if (typeof window !== 'undefined') {
      if (tenantId) {
        localStorage.setItem('aurix_active_tenant', tenantId);
        localStorage.setItem('aurix_tenant_id', tenantId);
      } else {
        localStorage.removeItem('aurix_active_tenant');
        localStorage.removeItem('aurix_tenant_id');
      }
    }
  }

  public static getActiveScenarioId(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('aurix_active_scenario_id');
    }
    return null;
  }

  public static setActiveScenarioId(scenarioId: string | null): void {
    if (typeof window !== 'undefined') {
      if (scenarioId) {
        localStorage.setItem('aurix_active_scenario_id', scenarioId);
      } else {
        localStorage.removeItem('aurix_active_scenario_id');
      }
    }
  }

  public static getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return (
        localStorage.getItem('aurix_session_token') ||
        localStorage.getItem('aurix_auth_token')
      );
    }
    return null;
  }

  public static setAuthToken(token: string | null): void {
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('aurix_session_token', token);
        localStorage.setItem('aurix_auth_token', token);
      } else {
        localStorage.removeItem('aurix_session_token');
        localStorage.removeItem('aurix_auth_token');
      }
    }
  }

  public static clearAuth(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('aurix_session_token');
      localStorage.removeItem('aurix_auth_token');
    }
  }

  private static getHeaders(isFormData: boolean = false): HeadersInit {
    const headers: Record<string, string> = {};
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }

    if (typeof window !== 'undefined') {
      const token = this.getAuthToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      headers['X-Tenant-ID'] = this.getTenantId();

      const activeScenarioId = this.getActiveScenarioId();
      if (activeScenarioId) {
        headers['X-Scenario-ID'] = activeScenarioId;
      }
    }
    return headers;
  }

  private static async handleResponse<T>(res: Response): Promise<T> {
    if (!res.ok) {
      let errorDetails: ApiErrorDetails;

      try {
        const errorJson = await res.json();

        errorDetails = {
          code: errorJson.code || `HTTP_${res.status}`,
          message:
            errorJson.detail ||
            errorJson.message ||
            errorJson.error?.message ||
            res.statusText,
          statusCode: res.status,
          details: errorJson,
          timestamp: new Date().toISOString(),
        };
      } catch {
        errorDetails = {
          code: `HTTP_${res.status}`,
          message: res.statusText || 'An unexpected error occurred',
          statusCode: res.status,
          timestamp: new Date().toISOString(),
        };
      }

      throw new ApiError(errorDetails);
    }

    const payload = await res.json();

    if (
      payload &&
      typeof payload === 'object' &&
      'data' in payload &&
      payload.data !== undefined
    ) {
      return payload.data as T;
    }

    return payload as T;
  }

  public static async get<T>(endpoint: string, fallback?: () => T): Promise<T> {
    try {
      const url = `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
      const res = await fetch(url, {
        method: 'GET',
        headers: this.getHeaders(),
      });
      return await this.handleResponse<T>(res);
    } catch (err) {
      if (this.getMode() === 'MOCK' && fallback) {
        console.warn(`[ApiClient] Operating in MOCK mode. Serving fallback for GET ${endpoint}`);
        return fallback();
      }
      throw err;
    }
  }

  public static async post<TReq, TRes>(
    endpoint: string,
    data: TReq,
    fallback?: (data: TReq) => TRes
  ): Promise<TRes> {
    try {
      const url = `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
      const res = await fetch(url, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(data),
      });
      return await this.handleResponse<TRes>(res);
    } catch (err) {
      if (this.getMode() === 'MOCK' && fallback) {
        console.warn(`[ApiClient] Operating in MOCK mode. Serving fallback for POST ${endpoint}`);
        return fallback(data);
      }
      throw err;
    }
  }

  public static async upload<TRes>(
    endpoint: string,
    formData: FormData,
    fallback?: (formData: FormData) => TRes
  ): Promise<TRes> {
    try {
      const url = `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
      const res = await fetch(url, {
        method: 'POST',
        headers: this.getHeaders(true),
        body: formData,
      });
      return await this.handleResponse<TRes>(res);
    } catch (err) {
      if (this.getMode() === 'MOCK' && fallback) {
        console.warn(`[ApiClient] Operating in MOCK mode. Serving fallback for UPLOAD ${endpoint}`);
        return fallback(formData);
      }
      throw err;
    }
  }

  public static async put<TReq, TRes>(
    endpoint: string,
    data: TReq,
    fallback?: (data: TReq) => TRes
  ): Promise<TRes> {
    try {
      const url = `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
      const res = await fetch(url, {
        method: 'PUT',
        headers: this.getHeaders(),
        body: JSON.stringify(data),
      });
      return await this.handleResponse<TRes>(res);
    } catch (err) {
      if (this.getMode() === 'MOCK' && fallback) {
        console.warn(`[ApiClient] Operating in MOCK mode. Serving fallback for PUT ${endpoint}`);
        return fallback(data);
      }
      throw err;
    }
  }

  public static async delete<TRes>(endpoint: string, fallback?: () => TRes): Promise<TRes> {
    try {
      const url = `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
      const res = await fetch(url, {
        method: 'DELETE',
        headers: this.getHeaders(),
      });
      return await this.handleResponse<TRes>(res);
    } catch (err) {
      if (this.getMode() === 'MOCK' && fallback) {
        console.warn(`[ApiClient] Operating in MOCK mode. Serving fallback for DELETE ${endpoint}`);
        return fallback();
      }
      throw err;
    }
  }
}

