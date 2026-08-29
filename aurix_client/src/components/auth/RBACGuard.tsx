"use client";

import React from "react";

export interface RBACGuardProps {
  requiredRole?: string;
  userRole?: string;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export const RBACGuard: React.FC<RBACGuardProps> = ({
  requiredRole = "VIEWER",
  userRole = "ADMIN",
  fallback = null,
  children,
}) => {
  const roleHierarchy: Record<string, number> = {
    VIEWER: 1,
    ANALYST: 2,
    OPERATOR: 3,
    MANAGER: 4,
    ADMIN: 5,
    SUPER_ADMIN: 6,
  };

  const userLevel = roleHierarchy[userRole.toUpperCase()] || 1;
  const requiredLevel = roleHierarchy[requiredRole.toUpperCase()] || 1;

  if (userLevel < requiredLevel) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
