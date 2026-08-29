'use client';

import React, { createContext, useContext, useState } from 'react';

interface SkuWorkspaceContextType {
  selectedSkuId: string;
  setSelectedSkuId: (id: string) => void;
}

const SkuWorkspaceContext = createContext<SkuWorkspaceContextType>({
  selectedSkuId: 'SKU-001',
  setSelectedSkuId: () => {},
});

export const SkuWorkspaceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedSkuId, setSelectedSkuId] = useState('SKU-001');
  return (
    <SkuWorkspaceContext.Provider value={{ selectedSkuId, setSelectedSkuId }}>
      {children}
    </SkuWorkspaceContext.Provider>
  );
};

export const useSkuWorkspaceContext = () => useContext(SkuWorkspaceContext);