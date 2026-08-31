'use client';

import React, {
  createContext,
  useCallback,
  useContext,
  useRef,
  useState,
  useSyncExternalStore,
  type RefObject,
} from 'react';

export const INTRO_TIMELINE = {
  logoRevealDelay: 400,
  intelligenceDelay: 700,
  taglineDelay: 900,
  glassSweepDelay: 1200,
  glassSweepDuration: 1200,
  holdEnd: 3000,
  flightDuration: 1500,
  totalDuration: 4500,
  firstAudioOffset: 200,
} as const;

export type IntroPhase =
  | 'playing'
  | 'flying'
  | 'complete';

interface AurixIntroContextValue {
  phase: IntroPhase;
  setPhase: (phase: IntroPhase) => void;
  navLogoRef: RefObject<HTMLAnchorElement | null>;
  skipIntro: () => void;
}

const STORAGE_KEY =
  'aurix_session_intro_completed';

function subscribeIntro(
  callback: () => void
) {
  if (typeof window === 'undefined') {
    return () => {};
  }

  const handleStorage = (
    event: StorageEvent
  ) => {
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
    return 'playing';
  }

  try {
    return sessionStorage.getItem(
      STORAGE_KEY
    )
      ? 'complete'
      : 'playing';
  } catch {
    return 'playing';
  }
}

function getIntroServerSnapshot():
  IntroPhase {
  return 'playing';
}

const AurixIntroContext =
  createContext<
    AurixIntroContextValue | null
  >(null);

export const AurixIntroProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {

  const storagePhase =
    useSyncExternalStore(
      subscribeIntro,
      getIntroSnapshot,
      getIntroServerSnapshot
    );

  const [
    phaseOverride,
    setPhaseOverride
  ] =
    useState<IntroPhase | null>(null);

  const navLogoRef =
    useRef<HTMLAnchorElement>(null);

  const phase =
    phaseOverride ?? storagePhase;

  const setPhase = useCallback(
    (nextPhase: IntroPhase) => {

      setPhaseOverride(nextPhase);

      if (
        nextPhase === 'complete' &&
        typeof window !== 'undefined'
      ) {
        try {
          sessionStorage.setItem(
            STORAGE_KEY,
            'true'
          );
        } catch {
          // In-memory override still completes the intro.
        }
      }
    },
    []
  );

  const skipIntro = useCallback(
    () => setPhase('complete'),
    [setPhase]
  );

  return (
    <AurixIntroContext.Provider
      value={{
        phase,
        setPhase,
        navLogoRef,
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
      'useAurixIntro must be used within an <AurixIntroProvider>.'
    );
  }

  return context;
};