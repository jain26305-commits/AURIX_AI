export type UserRole = 'SUPER_ADMIN' | 'EXECUTIVE' | 'PLANNER' | 'ANALYST' | 'AUDITOR';

export interface UserSession {
  userId: string;
  email: string;
  fullName: string;
  role: UserRole;
  tenantId: string;
  permissions: string[];
  token: string;
  expiresAt: string;
}

export interface LoginRequest {
  email: string;
  password?: string;
  tenantId: string;
}

export interface LoginResponseData {
  token: string;
  user: {
    userId: string;
    email: string;
    fullName: string;
    role: UserRole;
    tenantId: string;
    permissions: string[];
  };
  expiresInSeconds: number;
}