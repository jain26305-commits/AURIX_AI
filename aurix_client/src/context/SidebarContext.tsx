'use client';

import React, {
  createContext,
  useCallback,
  useContext,
  useSyncExternalStore,
} from 'react';

interface SidebarContextType {
  isCollapsed: boolean;
  toggleSidebar: () => void;
  setCollapsed: (collapsed: boolean) => void;
}

const STORAGE_KEY =
  'aurix_sidebar_collapsed';

function subscribeSidebar(
  callback: () => void
) {
  if (typeof window === 'undefined') {
    return () => {};
  }

  const handleStorage = (event: StorageEvent) => {
    if (event.key === STORAGE_KEY) {
      callback();
    }
  };

  window.addEventListener(
    'storage',
    handleStorage
  );

  return () =>
    window.removeEventListener(
      'storage',
      handleStorage
    );
}

function getSidebarSnapshot() {
  if (typeof window === 'undefined') {
    return true;
  }

  try {
    const stored = localStorage.getItem(
      STORAGE_KEY
    );

    return stored === null
      ? true
      : stored === 'true';
  } catch {
    return true;
  }
}

function getSidebarServerSnapshot() {
  return true;
}

const SidebarContext =
  createContext<SidebarContextType>({
    isCollapsed: true,
    toggleSidebar: () => {},
    setCollapsed: () => {},
  });

export const SidebarProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const isCollapsed =
    useSyncExternalStore(
      subscribeSidebar,
      getSidebarSnapshot,
      getSidebarServerSnapshot
    );

  const toggleSidebar = useCallback(() => {
    const next = !getSidebarSnapshot();

    try {
      localStorage.setItem(
        STORAGE_KEY,
        String(next)
      );
    } catch {
      // Storage may be unavailable.
    }

    window.dispatchEvent(
      new StorageEvent('storage', {
        key: STORAGE_KEY,
        newValue: String(next),
      })
    );
  }, []);

  const setCollapsed = useCallback(
    (collapsed: boolean) => {
      try {
        localStorage.setItem(
          STORAGE_KEY,
          String(collapsed)
        );
      } catch {
        // Storage may be unavailable.
      }

      window.dispatchEvent(
        new StorageEvent('storage', {
          key: STORAGE_KEY,
          newValue: String(collapsed),
        })
      );
    },
    []
  );

  return (
    <SidebarContext.Provider
      value={{
        isCollapsed,
        toggleSidebar,
        setCollapsed,
      }}
    >
      {children}
    </SidebarContext.Provider>
  );
};

export const useSidebar = () =>
  useContext(SidebarContext);
