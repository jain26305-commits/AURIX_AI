'use client';

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

export interface WorkspaceHeaderState {
  domainTitle?: string;
  subdomainTitle?: string;
  activeSku?: string;
  activeWorkspaceTitle?: string;
}

interface WorkspaceHeaderContextType {
  header: WorkspaceHeaderState;
  setHeader: (state: WorkspaceHeaderState) => void;
  clearHeader: () => void;
}

const EMPTY_STATE: WorkspaceHeaderState = {};

const WorkspaceHeaderContext = createContext<WorkspaceHeaderContextType>({
  header: EMPTY_STATE,
  setHeader: () => {},
  clearHeader: () => {},
});

export const WorkspaceHeaderProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [header, setHeaderState] = useState<WorkspaceHeaderState>(EMPTY_STATE);

  const setHeader = useCallback((state: WorkspaceHeaderState) => {
    setHeaderState(state);
  }, []);

  const clearHeader = useCallback(() => {
    setHeaderState(EMPTY_STATE);
  }, []);

  return (
    <WorkspaceHeaderContext.Provider value={{ header, setHeader, clearHeader }}>
      {children}
    </WorkspaceHeaderContext.Provider>
  );
};

export const useWorkspaceHeaderContext = () => useContext(WorkspaceHeaderContext);

/**
 * Call from any page/workspace to publish breadcrumb context (domain, subdomain,
 * active SKU, workspace title) up to the single app-level header/shell.
 *
 * Replaces the old pattern of each page mounting its own <AppShell> with props —
 * there is exactly one AppShell, rendered once in the root layout.
 */
export function useWorkspaceHeader(state: WorkspaceHeaderState) {
  const { setHeader, clearHeader } = useWorkspaceHeaderContext();

  // Stringify to keep the effect dependency stable across re-renders with
  // structurally-equal but referentially-new objects.
  const key = JSON.stringify(state);

  useEffect(() => {
    setHeader(state);
    return () => clearHeader();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
}
