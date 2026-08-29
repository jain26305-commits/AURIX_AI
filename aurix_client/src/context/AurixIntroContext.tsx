'use client';

import React, {
  createContext,
  useCallback,
  useContext,
  useRef,
  useSyncExternalStore,
} from 'react';

export type IntroPhase =
  | 'idle'
  | 'playing'
  | 'flying'
  | 'complete';

export const INTRO_TIMELINE = {
  intelligenceDelay: 600,
  taglineDelay: 1000,
  holdEnd: 1800,
  flightDuration: 650,
};

interface AurixIntroContextType {
  phase: IntroPhase;
  setPhase: (phase: IntroPhase) => void;
  headerLogoRef: React.RefObject<HTMLDivElement | null>;
  skipIntro: () => void;
}

const STORAGE_KEY = 'aurix_session_intro_completed';

function subscribeIntro(
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

function getIntroSnapshot(): IntroPhase {
  if (typeof window === 'undefined') {
    return 'idle';
  }

  try {
    return sessionStorage.getItem(STORAGE_KEY)
      ? 'complete'
      : 'playing';
  } catch {
    return 'playing';
  }
}

function getIntroServerSnapshot(): IntroPhase {
  return 'idle';
}

const AurixIntroContext =
  createContext<
    AurixIntroContextType | undefined
  >(undefined);

export const AurixIntroProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const storagePhase =
    useSyncExternalStore(
      subscribeIntro,
      getIntroSnapshot,
      getIntroServerSnapshot
    );

  const headerLogoRef =
    useRef<HTMLDivElement>(null);

  const setPhase = useCallback(
    (newPhase: IntroPhase) => {
      if (
        newPhase === 'complete' &&
        typeof window !== 'undefined'
      ) {
        try {
          sessionStorage.setItem(
            STORAGE_KEY,
            'true'
          );
        } catch {
          // Storage may be unavailable.
        }
      }
    },
    []
  );

  const phase: IntroPhase = storagePhase;

  const skipIntro = useCallback(() => {
    setPhase('complete');
  }, [setPhase]);

  return (
    <AurixIntroContext.Provider
      value={{
        phase,
        setPhase,
        headerLogoRef,
        skipIntro,
      }}
    >
      {children}
    </AurixIntroContext.Provider>
  );
};

export const useAurixIntro = () => {
  const context =
    useContext(AurixIntroContext);

  if (!context) {
    throw new Error(
      'useAurixIntro must be used within an AurixIntroProvider'
    );
  }

  return context;
};
