import { ApiClient } from '@/services/api/apiClient';
import { LoginRequest, LoginResponseData, UserSession } from '@/types/auth.types';

export class AuthService {
  public static async login(credentials: LoginRequest): Promise<UserSession> {
    const response = await ApiClient.post<LoginRequest, LoginResponseData>(
      '/auth/login',
      credentials
    );

    const session: UserSession = {
      userId: response.user.userId,
      email: response.user.email,
      fullName: response.user.fullName,
      role: response.user.role,
      tenantId: response.user.tenantId,
      permissions: response.user.permissions,
      token: response.token,
      expiresAt: new Date(Date.now() + response.expiresInSeconds * 1000).toISOString(),
    };

    ApiClient.setAuthToken(session.token);
    ApiClient.setTenantId(session.tenantId);

    if (typeof window !== 'undefined') {
      try {
        sessionStorage.setItem('aurix_user_session', JSON.stringify(session));
      } catch (e) {
        console.warn('[AuthService] Could not persist session to sessionStorage', e);
      }
    }

    return session;
  }

  public static getCurrentSession(): UserSession | null {
    if (typeof window === 'undefined') return null;
    try {
      const raw = sessionStorage.getItem('aurix_user_session');
      if (!raw || raw.trim() === '' || raw === 'undefined' || raw === 'null') {
        return null;
      }
      const session: UserSession = JSON.parse(raw);
      if (!session || !session.expiresAt) {
        this.logout();
        return null;
      }
      if (new Date(session.expiresAt).getTime() < Date.now()) {
        this.logout();
        return null;
      }
      return session;
    } catch {
      this.logout();
      return null;
    }
  }

  public static logout(): void {
    ApiClient.setAuthToken(null);
    if (typeof window !== 'undefined') {
      try {
        sessionStorage.removeItem('aurix_user_session');
        sessionStorage.removeItem('aurix_auth_token');
      } catch (e) {
        console.warn('[AuthService] Could not clear sessionStorage', e);
      }
    }
  }
}