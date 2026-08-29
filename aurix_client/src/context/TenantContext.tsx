'use client';

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react';
import {
  UserSession,
  UserRole,
} from '@/types/auth.types';
import { AuthService } from '@/services/api/authService';
import { ApiClient } from '@/services/api/apiClient';

interface TenantContextType {
  session: UserSession | null;
  tenantId: string;
  role: UserRole | null;
  isAuthenticated: boolean;
  login: (credentials: {
    email: string;
    password?: string;
    tenantId: string;
  }) => Promise<UserSession>;
  logout: () => void;
  hasPermission: (
    permission: string
  ) => boolean;
  switchTenant: (
    newTenantId: string
  ) => void;
}

const TenantContext =
  createContext<
    TenantContextType | undefined
  >(undefined);

export const TenantProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const [session, setSession] =
    useState<UserSession | null>(() => {
      if (typeof window === 'undefined') {
        return null;
      }

      return AuthService.getCurrentSession();
    });

  useEffect(() => {
    const existing =
      AuthService.getCurrentSession();

    if (!existing) {
      return;
    }

    ApiClient.setAuthToken(existing.token);
    ApiClient.setTenantId(existing.tenantId);
  }, []);

  const login = useCallback(
    async (credentials: {
      email: string;
      password?: string;
      tenantId: string;
    }) => {
      const newSession =
        await AuthService.login(credentials);

      ApiClient.setAuthToken(
        newSession.token
      );

      ApiClient.setTenantId(
        newSession.tenantId
      );

      setSession(newSession);

      return newSession;
    },
    []
  );

  const logout = useCallback(() => {
    AuthService.logout();
    ApiClient.clearAuth();
    setSession(null);
  }, []);

  const switchTenant = useCallback(
    (newTenantId: string) => {
      if (!newTenantId) {
        return;
      }

      ApiClient.setTenantId(newTenantId);

      setSession((previous) => {
        if (!previous) {
          return null;
        }

        const updated: UserSession = {
          ...previous,
          tenantId: newTenantId,
        };

        if (
          typeof window !== 'undefined'
        ) {
          try {
            sessionStorage.setItem(
              'aurix_user_session',
              JSON.stringify(updated)
            );
          } catch {
            // Storage may be unavailable.
          }
        }

        return updated;
      });
    },
    []
  );

  const hasPermission = useCallback(
    (permission: string) => {
      if (!session) {
        return false;
      }

      if (
        session.permissions.includes('*')
      ) {
        return true;
      }

      return session.permissions.includes(
        permission
      );
    },
    [session]
  );

  return (
    <TenantContext.Provider
      value={{
        session,
        tenantId:
          session?.tenantId ||
          ApiClient.getTenantId(),
        role: session?.role || null,
        isAuthenticated: !!session,
        login,
        logout,
        hasPermission,
        switchTenant,
      }}
    >
      {children}
    </TenantContext.Provider>
  );
};

export const useTenant = () => {
  const context =
    useContext(TenantContext);

  if (!context) {
    throw new Error(
      'useTenant must be used within a TenantProvider'
    );
  }

  return context;
};
