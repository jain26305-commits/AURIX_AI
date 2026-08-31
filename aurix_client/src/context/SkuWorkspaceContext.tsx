'use client';

import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from 'react';

export interface SkuOption {
  id: string;
  name: string;
}

export const DEFAULT_SKU_CATALOG: SkuOption[] = [
  { id: 'SKU-001', name: '101 Beige-L (T-Shirt)' },
  { id: 'SKU-002', name: '101 Beige-M (T-Shirt)' },
  { id: 'SKU-003', name: '102 Navy-L (Polo)' },
  { id: 'SKU-004', name: '103 Black-XXL (Hoodie)' },
  { id: 'SKU-005', name: '104 Olive-M (Jeans)' },
];

interface SkuWorkspaceContextType {
  selectedSkuId: string;
  setSelectedSkuId: (id: string) => void;
  availableSkus: SkuOption[];
}

const STORAGE_KEY = 'aurix.activeSkuId';

const SkuWorkspaceContext =
  createContext<SkuWorkspaceContextType | null>(null);

export const SkuWorkspaceProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const [selectedSkuId, setSelectedSkuIdState] = useState<string>(() => {
    if (typeof window === 'undefined') {
      return 'SKU-001';
    }

    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);

      if (
        stored &&
        DEFAULT_SKU_CATALOG.some((sku) => sku.id === stored)
      ) {
        return stored;
      }
    } catch {
      // Persistence failure must never block the workspace.
    }

    return 'SKU-001';
  });

  const [availableSkus] =
    useState<SkuOption[]>(DEFAULT_SKU_CATALOG);

  const setSelectedSkuId = useCallback(
    (id: string) => {
      if (
        !DEFAULT_SKU_CATALOG.some(
          (sku) => sku.id === id
        )
      ) {
        return;
      }

      setSelectedSkuIdState(id);

      try {
        window.localStorage.setItem(
          STORAGE_KEY,
          id
        );
      } catch {
        // Persistence failure must never block the workspace.
      }
    },
    []
  );

  const value = useMemo(
    () => ({
      selectedSkuId,
      setSelectedSkuId,
      availableSkus,
    }),
    [
      selectedSkuId,
      setSelectedSkuId,
      availableSkus,
    ]
  );

  return (
    <SkuWorkspaceContext.Provider value={value}>
      {children}
    </SkuWorkspaceContext.Provider>
  );
};

export const useSkuWorkspaceContext =
  (): SkuWorkspaceContextType => {
    const context = useContext(
      SkuWorkspaceContext
    );

    if (!context) {
      throw new Error(
        'useSkuWorkspaceContext must be used inside SkuWorkspaceProvider.'
      );
    }

    return context;
  };
