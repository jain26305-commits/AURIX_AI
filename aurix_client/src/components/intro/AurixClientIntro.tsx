'use client';

import React, {
  useEffect,
  useLayoutEffect,
  useRef,
  useSyncExternalStore,
} from 'react';
import {
  useAurixIntro,
  INTRO_TIMELINE,
} from '@/context/AurixIntroContext';
import { AurixLogoMark } from '@/components/brand/AurixLogoMark';

const REDUCED_MOTION_QUERY =
  '(prefers-reduced-motion: reduce)';

function subscribeReducedMotion(
  callback: () => void
) {
  if (typeof window === 'undefined') {
    return () => {};
  }

  const mediaQuery =
    window.matchMedia(
      REDUCED_MOTION_QUERY
    );

  const handleChange = () =>
    callback();

  mediaQuery.addEventListener(
    'change',
    handleChange
  );

  return () =>
    mediaQuery.removeEventListener(
      'change',
      handleChange
    );
}

function getReducedMotionSnapshot() {
  if (typeof window === 'undefined') {
    return false;
  }

  return window
    .matchMedia(
      REDUCED_MOTION_QUERY
    )
    .matches;
}

function getReducedMotionServerSnapshot() {
  return false;
}

export const AurixClientIntro: React.FC = () => {
  const {
    phase,
    setPhase,
    headerLogoRef,
    skipIntro,
  } = useAurixIntro();

  const overlayLogoRef =
    useRef<HTMLDivElement>(null);

  const reducedMotion =
    useSyncExternalStore(
      subscribeReducedMotion,
      getReducedMotionSnapshot,
      getReducedMotionServerSnapshot
    );

  useLayoutEffect(() => {
    if (!reducedMotion) {
      return;
    }

    const frame =
      requestAnimationFrame(() => {
        setPhase('complete');
      });

    return () =>
      cancelAnimationFrame(frame);
  }, [reducedMotion, setPhase]);

  useEffect(() => {
    if (
      phase !== 'playing' ||
      reducedMotion
    ) {
      return;
    }

    document.body.style.overflow =
      'hidden';

    const holdTimer = setTimeout(() => {
      setPhase('flying');
      document.body.style.overflow = '';
    }, INTRO_TIMELINE.holdEnd);

    return () => {
      clearTimeout(holdTimer);
      document.body.style.overflow = '';
    };
  }, [phase, reducedMotion, setPhase]);

  useLayoutEffect(() => {
    if (phase !== 'flying') {
      return;
    }

    const overlay =
      overlayLogoRef.current;

    const target =
      headerLogoRef.current;

    if (!overlay || !target) {
      const frame =
        requestAnimationFrame(() => {
          setPhase('complete');
        });

      return () =>
        cancelAnimationFrame(frame);
    }

    const first =
      overlay.getBoundingClientRect();

    const last =
      target.getBoundingClientRect();

    const scale =
      last.width /
      (first.width || 1);

    const translateX =
      last.left +
      last.width / 2 -
      (first.left +
        first.width / 2);

    const translateY =
      last.top +
      last.height / 2 -
      (first.top +
        first.height / 2);

    overlay.style.setProperty(
      '--flight-x',
      `${translateX}px`
    );

    overlay.style.setProperty(
      '--flight-y',
      `${translateY}px`
    );

    overlay.style.setProperty(
      '--flight-scale',
      `${scale}`
    );

    const frame =
      requestAnimationFrame(() => {
        overlay.classList.add(
          'aurix-logo-flying'
        );
      });

    const handleTransitionEnd = (
      event: TransitionEvent
    ) => {
      if (
        event.propertyName ===
        'transform'
      ) {
        setPhase('complete');
      }
    };

    overlay.addEventListener(
      'transitionend',
      handleTransitionEnd
    );

    const fallback = setTimeout(
      () =>
        setPhase('complete'),
      INTRO_TIMELINE.flightDuration +
        100
    );

    return () => {
      cancelAnimationFrame(frame);

      overlay.removeEventListener(
        'transitionend',
        handleTransitionEnd
      );

      clearTimeout(fallback);
    };
  }, [
    phase,
    headerLogoRef,
    setPhase,
  ]);

  if (
    phase === 'complete' ||
    reducedMotion ||
    phase === 'idle'
  ) {
    return null;
  }

  const isFlying =
    phase === 'flying';

  return (
    <div
      className={`fixed inset-0 z-[9999] flex items-center justify-center overflow-hidden transition-colors duration-700 bg-[#030303] ${
        isFlying
          ? 'bg-opacity-0 pointer-events-none'
          : 'bg-opacity-100 pointer-events-auto'
      }`}
    >
      <style>{`
        .aurix-flight-element {
          transition: transform ${INTRO_TIMELINE.flightDuration}ms cubic-bezier(0.22, 1, 0.36, 1);
          transform-origin: center center;
        }

        .aurix-logo-flying {
          transform: translate3d(var(--flight-x, 0px), var(--flight-y, 0px), 0) scale3d(var(--flight-scale, 1), var(--flight-scale, 1), 1);
        }
      `}</style>

      <div
        className="absolute inset-0 bg-[radial-gradient(ellipse_60%_60%_at_50%_50%,rgba(212,175,55,0.06)_0%,rgba(212,175,55,0.02)_40%,transparent_100%)]"
        style={{
          opacity: isFlying ? 0 : 1,
          transition:
            'opacity 500ms ease',
        }}
      />

      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 flex flex-col items-center">
        <div
          ref={overlayLogoRef}
          className={`aurix-flight-element flex flex-col items-center ${
            isFlying
              ? 'aurix-logo-flying'
              : ''
          }`}
        >
          <AurixLogoMark
            idPrefix="intro"
            iconClassName="w-14 h-14 lg:w-16 lg:h-16"
            textClassName="text-[2.75rem] lg:text-[3.5rem]"
            trackingClassName="tracking-[0.28em]"
          />

          <div
            className={`mt-2 transition-opacity duration-300 ${
              isFlying
                ? 'opacity-0'
                : 'opacity-100'
            }`}
          >
            <span className="font-mono text-xs lg:text-sm uppercase tracking-[0.45em] text-transparent bg-clip-text bg-gradient-to-r from-[#D4AF37] via-[#F3E5AB] to-[#D4AF37] font-bold drop-shadow-[0_0_12px_rgba(212,175,55,0.4)]">
              ENTERPRISE INTELLIGENCE
            </span>
          </div>
        </div>
      </div>

      {!isFlying && (
        <button
          onClick={skipIntro}
          className="absolute bottom-8 right-8 z-20 px-3 py-1.5 rounded-lg bg-white/[0.05] border border-white/10 hover:bg-white/[0.1] text-[11px] font-mono tracking-widest text-slate-400 hover:text-white transition-colors cursor-pointer"
        >
          SKIP INTRO [ESC]
        </button>
      )}
    </div>
  );
};
