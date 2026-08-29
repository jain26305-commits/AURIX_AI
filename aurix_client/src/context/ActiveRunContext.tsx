'use client';

import React, { createContext, useContext, useState } from 'react';

interface ActiveRunContextType {
  activeRunId: string | null;
  setActiveRunId: (id: string | null) => void;
}

const ActiveRunContext = createContext<ActiveRunContextType>({
  activeRunId: null,
  setActiveRunId: () => {},
});

export const ActiveRunProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeRunId, setActiveRunId] = useState<string | null>('RUN-2025-08');
  return (
    <ActiveRunContext.Provider value={{ activeRunId, setActiveRunId }}>
      {children}
    </ActiveRunContext.Provider>
  );
};

export const useActiveRun = () => useContext(ActiveRunContext);