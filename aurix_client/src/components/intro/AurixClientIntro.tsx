'use client';

import React, {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from 'react';

import {
  useAurixIntro,
  INTRO_TIMELINE,
} from '@/context/AurixIntroContext';

const REDUCED_MOTION_QUERY =
  '(prefers-reduced-motion: reduce)';

const IntroBrandMark: React.FC = () => (
  <div className="flex items-center select-none">
    <div className="relative mr-2 flex items-center justify-center shrink-0 w-14 h-14 lg:w-16 lg:h-16">
      <div className="absolute inset-0 bg-[#B8912A]/25 blur-lg rounded-full" />

      <svg
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full relative z-10 filter drop-shadow-[0_0_8px_rgba(212,175,55,0.5)]"
        aria-hidden="true"
      >
        <defs>
          <linearGradient
            id="aurix-intro-leg-left"
            x1="15"
            y1="95"
            x2="50"
            y2="5"
            gradientUnits="userSpaceOnUse"
          >
            <stop
              offset="0%"
              stopColor="#94A3B8"
            />
            <stop
              offset="50%"
              stopColor="#F8FAFC"
            />
            <stop
              offset="100%"
              stopColor="#E2E8F0"
            />
          </linearGradient>

          <linearGradient
            id="aurix-intro-leg-right"
            x1="85"
            y1="95"
            x2="50"
            y2="5"
            gradientUnits="userSpaceOnUse"
          >
            <stop
              offset="0%"
              stopColor="#475569"
            />
            <stop
              offset="50%"
              stopColor="#94A3B8"
            />
            <stop
              offset="100%"
              stopColor="#CBD5E1"
            />
          </linearGradient>

          <linearGradient
            id="aurix-intro-core"
            x1="50"
            y1="95"
            x2="50"
            y2="50"
            gradientUnits="userSpaceOnUse"
          >
            <stop
              offset="0%"
              stopColor="#B8912A"
            />
            <stop
              offset="100%"
              stopColor="#D4AF37"
            />
          </linearGradient>

          <linearGradient
            id="aurix-intro-ai-grad"
            x1="0"
            y1="0"
            x2="0"
            y2="100"
            gradientUnits="userSpaceOnUse"
          >
            <stop
              offset="0%"
              stopColor="#F8FAFC"
            />
            <stop
              offset="50%"
              stopColor="#E2E8F0"
            />
            <stop
              offset="100%"
              stopColor="#94A3B8"
            />
          </linearGradient>
        </defs>

        <path
          d="M50 5 L15 95 L30 95 L50 40 Z"
          fill="url(#aurix-intro-leg-left)"
        />

        <path
          d="M50 5 L50 40 L70 95 L85 95 Z"
          fill="url(#aurix-intro-leg-right)"
        />

        <path
          d="M50 58 L36 92 L50 78 L64 92 Z"
          fill="url(#aurix-intro-core)"
        />
      </svg>
    </div>

    <span className="font-sans tracking-[0.28em] text-transparent bg-clip-text bg-gradient-to-b from-[#F8FAFC] via-[#E2E8F0] to-[#94A3B8] font-bold flex items-center text-[2.75rem] lg:text-[3.5rem]">
      URIX

      <span className="ml-2 inline-flex items-center gap-[0.08em]">
        <svg
          viewBox="0 0 76 100"
          className="h-[0.80em] w-auto inline-block align-baseline -translate-y-[0.03em]"
          aria-label="A"
        >
          <path
            d="M38 4 L4 96 L22 96 L38 52 L54 96 L72 96 Z"
            fill="url(#aurix-intro-ai-grad)"
          />
        </svg>

        <span>I</span>
      </span>
    </span>
  </div>
);

export const AurixClientIntro: React.FC = () => {

  const {
    phase,
    setPhase,
    navLogoRef,
    skipIntro,
  } = useAurixIntro();

  const overlayLogoRef =
    useRef<HTMLDivElement>(null);

  const audio1Ref =
    useRef<HTMLAudioElement | null>(null);

  const audio2Ref =
    useRef<HTMLAudioElement | null>(null);

  const audioTimer1Ref =
    useRef<number | null>(
      null
    );

  const audioTimer2Ref =
    useRef<number | null>(
      null
    );

  const mountedRef =
    useRef(false);

  const introSessionRef =
    useRef(false);

  const introStartTimeRef =
    useRef<number | null>(null);

  const audio1ScheduledRef =
    useRef(false);

  const audio2ScheduledRef =
    useRef(false);

  const audioInterruptedRef =
    useRef(false);

  const phaseRef =
    useRef(phase);

  const [
    reducedMotion,
    setReducedMotion
  ] = useState(false);

  const [
    sequenceStarted,
    setSequenceStarted
  ] = useState(false);

  const [
    audioBlocked,
    setAudioBlocked
  ] = useState(false);

  const [
    audioStarted,
    setAudioStarted
  ] = useState(false);

  useEffect(() => {
    phaseRef.current = phase;

    if (phase === 'complete') {
      if (audioTimer1Ref.current) {
        clearTimeout(
          audioTimer1Ref.current
        );
      }

      if (audioTimer2Ref.current) {
        clearTimeout(
          audioTimer2Ref.current
        );
      }

      audio1Ref.current?.pause();
      audio2Ref.current?.pause();
      document.body.style.overflow = '';
    }
  }, [phase]);

  useLayoutEffect(() => {
    const mediaQuery = window.matchMedia(
      REDUCED_MOTION_QUERY
    );

    if (!mediaQuery.matches) {
      return;
    }

    const frame = window.requestAnimationFrame(() => {
      setReducedMotion(true);
      setPhase('complete');
    });

    return () => {
      window.cancelAnimationFrame(frame);
    };
  }, [setPhase]);

  useEffect(() => {

    mountedRef.current = true;

    const navigation =
      performance.getEntriesByType(
        'navigation'
      )[0] as
        | PerformanceNavigationTiming
        | undefined;

    if (
      navigation?.type ===
      'back_forward'
    ) {
      setPhase('complete');
      mountedRef.current = false;

      return () => {
        mountedRef.current = false;
      };
    }

    const a1 =
      new Audio(
        '/audio/aurix-intro-voice.mp3'
      );

    const a2 =
      new Audio(
        '/audio/aurix-welcome-voice.mp3'
      );

    a1.preload = 'auto';
    a2.preload = 'auto';

    a1.volume = 0.8;
    a2.volume = 0.8;

    a1.muted = true;
    a2.muted = true;

    a1.onerror = () =>
      console.error(
        '[AurixIntro Audio] Failed to load /aurix-intro-voice.mp3'
      );

    a2.onerror = () =>
      console.error(
        '[AurixIntro Audio] Failed to load /aurix-welcome-voice.mp3'
      );

    audio1Ref.current = a1;
    audio2Ref.current = a2;

    audioInterruptedRef.current = false;
    audio1ScheduledRef.current = false;
    audio2ScheduledRef.current = false;

    const handleUserGesture = () => {

      if (audio1Ref.current) {
        audio1Ref.current.muted = false;
      }

      if (audio2Ref.current) {
        audio2Ref.current.muted = false;
      }

      setAudioStarted(true);
      setAudioBlocked(false);
    };

    window.addEventListener(
      'click',
      handleUserGesture,
      { once: true }
    );

    window.addEventListener(
      'keydown',
      handleUserGesture,
      { once: true }
    );

    window.addEventListener(
      'touchstart',
      handleUserGesture,
      { once: true }
    );

    return () => {

      mountedRef.current = false;
      audioInterruptedRef.current = true;

      if (audioTimer1Ref.current) {
        clearTimeout(
          audioTimer1Ref.current
        );
      }

      if (audioTimer2Ref.current) {
        clearTimeout(
          audioTimer2Ref.current
        );
      }

      a1.pause();
      a2.pause();

      a1.currentTime = 0;
      a2.currentTime = 0;

      window.removeEventListener(
        'click',
        handleUserGesture
      );

      window.removeEventListener(
        'keydown',
        handleUserGesture
      );

      window.removeEventListener(
        'touchstart',
        handleUserGesture
      );
    };

  }, [setPhase]);

  useEffect(() => {

    const handleVisibilityChange = () => {

      if (
        document.visibilityState !==
        'visible'
      ) {

        audioInterruptedRef.current =
          true;

        if (audioTimer1Ref.current) {
          clearTimeout(
            audioTimer1Ref.current
          );
        }

        if (audioTimer2Ref.current) {
          clearTimeout(
            audioTimer2Ref.current
          );
        }

        audio1Ref.current?.pause();
        audio2Ref.current?.pause();

      } else if (
        phaseRef.current ===
        'playing'
      ) {

        audioInterruptedRef.current =
          false;
      }
    };

    document.addEventListener(
      'visibilitychange',
      handleVisibilityChange
    );

    return () =>
      document.removeEventListener(
        'visibilitychange',
        handleVisibilityChange
      );

  }, []);

  const playFirstAudio = () => {

    const audio =
      audio1Ref.current;

    if (
      !audio ||
      !mountedRef.current ||
      !introSessionRef.current ||
      audioInterruptedRef.current ||
      document.visibilityState !==
        'visible' ||
      audio1ScheduledRef.current ||
      phaseRef.current ===
        'complete'
    ) {
      return;
    }

    audio1ScheduledRef.current =
      true;

    audio.currentTime = 0;

    audio.play()
      .then(() => {

        if (
          !mountedRef.current ||
          audioInterruptedRef.current
        ) {
          audio.pause();
          return;
        }

        setAudioStarted(true);
        setAudioBlocked(false);
      })
      .catch((error) => {

        console.warn(
          '[AurixIntro Audio] First playback unavailable:',
          error
        );

        setAudioBlocked(true);
      });
  };

  const playSecondAudio = () => {

    const audio =
      audio2Ref.current;

    if (
      !audio ||
      !mountedRef.current ||
      !introSessionRef.current ||
      audioInterruptedRef.current ||
      document.visibilityState !==
        'visible' ||
      audio2ScheduledRef.current ||
      phaseRef.current ===
        'complete'
    ) {
      return;
    }

    audio2ScheduledRef.current =
      true;

    audio.currentTime = 0;

    audio.play()
      .then(() => {

        if (
          !mountedRef.current ||
          audioInterruptedRef.current
        ) {
          audio.pause();
          return;
        }

        setAudioStarted(true);
        setAudioBlocked(false);
      })
      .catch((error) => {

        console.warn(
          '[AurixIntro Audio] Second playback unavailable:',
          error
        );

        setAudioBlocked(true);
      });
  };

  useEffect(() => {
    if (
      phase !== 'playing' ||
      reducedMotion
    ) {
      return;
    }

    const frame = window.requestAnimationFrame(() => {
      setSequenceStarted(true);
    });

    return () => {
      window.cancelAnimationFrame(frame);
    };
  }, [phase, reducedMotion]);

  useEffect(() => {

    if (
      !sequenceStarted ||
      reducedMotion ||
      !mountedRef.current ||
      phaseRef.current === 'complete'
    ) {
      return;
    }

    document.body.style.overflow =
      'hidden';

    introSessionRef.current = true;
    introStartTimeRef.current =
      performance.now();

    audioInterruptedRef.current =
      false;

    const firstTimer =
      window.setTimeout(
        playFirstAudio,
        INTRO_TIMELINE.firstAudioOffset
      );

    const secondTimer =
      window.setTimeout(
        playSecondAudio,
        INTRO_TIMELINE.holdEnd +
          INTRO_TIMELINE.flightDuration
      );

    audioTimer1Ref.current =
      firstTimer;

    audioTimer2Ref.current =
      secondTimer;

    const holdTimer =
      window.setTimeout(() => {

        if (
          !mountedRef.current ||
          phaseRef.current ===
            'complete'
        ) {
          return;
        }

        setPhase('flying');
        document.body.style.overflow =
          '';

      }, INTRO_TIMELINE.holdEnd);

    const escapeHandler = (
      event: KeyboardEvent
    ) => {

      if (
        event.key === 'Escape' &&
        phaseRef.current !==
          'complete'
      ) {
        event.preventDefault();
        skipIntro();
      }
    };

    window.addEventListener(
      'keydown',
      escapeHandler
    );

    return () => {

      window.clearTimeout(
        firstTimer
      );

      window.clearTimeout(
        holdTimer
      );

      window.removeEventListener(
        'keydown',
        escapeHandler
      );

      document.body.style.overflow =
        '';
    };

  }, [
    sequenceStarted,
    reducedMotion,
    setPhase,
    skipIntro,
  ]);

  useLayoutEffect(() => {

    if (phase !== 'flying') {
      return;
    }

    const overlay =
      overlayLogoRef.current;

    const target =
      navLogoRef.current;

    if (!overlay || !target) {

      setPhase('complete');
      return;
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
      (
        first.left +
        first.width / 2
      );

    const translateY =
      last.top +
      last.height / 2 -
      (
        first.top +
        first.height / 2
      );

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

    const raf =
      requestAnimationFrame(() => {
        overlay.classList.add(
          'aurix-logo-flying'
        );
      });

    const handleTransitionEnd =
      (event: TransitionEvent) => {

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

    const fallback =
      window.setTimeout(
        () =>
          setPhase('complete'),
        INTRO_TIMELINE.flightDuration +
          250
      );

    return () => {

      cancelAnimationFrame(raf);

      overlay.removeEventListener(
        'transitionend',
        handleTransitionEnd
      );

      clearTimeout(
        fallback
      );
    };

  }, [
    phase,
    navLogoRef,
    setPhase,
  ]);

  const handleEnableSound = async (
    event?: React.MouseEvent<HTMLButtonElement>
  ) => {

    event?.stopPropagation();

    if (
      !mountedRef.current ||
      !introSessionRef.current ||
      document.visibilityState !==
        'visible'
    ) {
      return;
    }

    try {

      const now =
        performance.now();

      const elapsed =
        now -
        (
          introStartTimeRef.current ??
          now
        );

      const secondAudioOffset =
        INTRO_TIMELINE.holdEnd +
        INTRO_TIMELINE.flightDuration;

      const a1 =
        audio1Ref.current;

      const a2 =
        audio2Ref.current;

      if (
        a1 &&
        elapsed <
          secondAudioOffset
      ) {

        if (
          Number.isFinite(
            a1.duration
          ) &&
          a1.duration > 0
        ) {

          const desiredTime =
            Math.max(
              0,
              Math.min(
                (
                  elapsed -
                  INTRO_TIMELINE.firstAudioOffset
                ) / 1000,
                Math.max(
                  0,
                  a1.duration -
                    0.05
                )
              )
            );

          a1.currentTime =
            desiredTime;

        } else {
          a1.currentTime = 0;
        }

        a1.volume = 0.8;
        a1.muted = false;

        await a1.play();

        audio1ScheduledRef.current =
          true;

      } else if (a2) {

        a2.currentTime = 0;
        a2.volume = 0.8;
        a2.muted = false;

        await a2.play();

        audio2ScheduledRef.current =
          true;
      }

      setAudioStarted(true);
      setAudioBlocked(false);

    } catch (error) {

      console.error(
        '[AurixIntro Audio] Manual sound enable failed:',
        error
      );

      setAudioBlocked(true);
    }
  };

  if (
    phase === 'complete' ||
    reducedMotion
  ) {
    return null;
  }

  const isFlying =
    phase === 'flying';

  return (
    <div
      className={`fixed inset-0 z-[9999] flex items-center justify-center overflow-hidden transition-[opacity,background-color] duration-1000 ease-[cubic-bezier(0.25,1,0.5,1)] bg-[#030303] ${
        isFlying
          ? 'bg-opacity-0 pointer-events-none'
          : 'bg-opacity-100'
      }`}
      role="presentation"
    >

      <style>{`
        @keyframes aurix-pure-fade-in {
          0% {
            opacity: 0;
          }
          100% {
            opacity: 1;
          }
        }

        @keyframes aurix-ambient-pulse {
          0%, 100% {
            opacity: 0.25;
          }

          50% {
            opacity: 0.75;
          }
        }

        @keyframes aurix-particle-rise {
          0% {
            opacity: 0;
            transform:
              translate3d(
                0,
                0,
                0
              );
          }

          20% {
            opacity: 0.55;
          }

          80% {
            opacity: 0.55;
          }

          100% {
            opacity: 0;
            transform:
              translate3d(
                0,
                -120px,
                0
              );
          }
        }

        @keyframes aurix-glass-reflection {
          0% {
            transform:
              translate3d(
                -140%,
                0,
                0
              );
            opacity: 0;
          }

          20% {
            opacity: 0.45;
          }

          80% {
            opacity: 0.45;
          }

          100% {
            transform:
              translate3d(
                140%,
                0,
                0
              );
            opacity: 0;
          }
        }

        .aurix-logo-flight {
          transition:
            transform
            ${INTRO_TIMELINE.flightDuration}ms
            cubic-bezier(
              0.22,
              1,
              0.36,
              1
            );

          transform-origin:
            center center;

          animation:
            aurix-pure-fade-in
            1.2s
            ease-in-out
            0.2s
            both;
        }

        .aurix-logo-flying {
          animation: none;

          transform:
            translate3d(
              var(--flight-x, 0px),
              var(--flight-y, 0px),
              0
            )
            scale3d(
              var(--flight-scale, 1),
              var(--flight-scale, 1),
              1
            );
        }

        .aurix-glass-sweep {
          animation:
            aurix-glass-reflection
            ${INTRO_TIMELINE.glassSweepDuration}ms
            ease-in-out
            ${INTRO_TIMELINE.glassSweepDelay}ms
            both;
        }
      `}</style>

      <div
        className="absolute inset-0 bg-[radial-gradient(ellipse_70%_70%_at_50%_50%,rgba(212,175,55,0.07)_0%,rgba(148,163,184,0.025)_40%,transparent_100%)]"
        style={{
          animation:
            'aurix-pure-fade-in 1.5s ease-in-out 0.1s both',
          opacity:
            isFlying
              ? 0
              : undefined,
          transition:
            isFlying
              ? 'opacity 1000ms ease'
              : undefined,
        }}
      />

      {!isFlying && (
        <div
          className="absolute inset-0 pointer-events-none"
          aria-hidden="true"
        >
          {[18, 34, 52, 66, 78].map(
            (left, i) => (
              <span
                key={left}
                className="absolute bottom-1/3 w-[2px] h-[2px] rounded-full bg-[#D4AF37]/80 shadow-[0_0_8px_rgba(212,175,55,0.6)]"
                style={{
                  left: `${left}%`,
                  animation:
                    `aurix-particle-rise ${
                      3.6 + i * 0.4
                    }s ease-in ${
                      0.6 + i * 0.3
                    }s infinite`,
                }}
              />
            )
          )}
        </div>
      )}

      <div
        className="absolute top-1/2 left-1/2 z-10"
        style={{
          transform:
            'translate3d(-50%, -50%, 0)',
        }}
      >

        <div
          ref={overlayLogoRef}
          className={`aurix-logo-flight relative flex flex-col items-center justify-center overflow-visible ${
            isFlying
              ? 'aurix-logo-flying'
              : ''
          }`}
        >

          <div
            className="absolute -inset-10 rounded-full bg-[radial-gradient(circle,rgba(212,175,55,0.16)_0%,rgba(148,163,184,0.05)_45%,transparent_75%)] blur-2xl pointer-events-none"
            style={{
              animation:
                !isFlying
                  ? 'aurix-ambient-pulse 3.4s ease-in-out infinite'
                  : 'none',

              opacity:
                isFlying
                  ? 0
                  : 0.3,

              transition:
                'opacity 400ms ease',
            }}
          />

          <div className="relative flex items-center px-6 py-3 overflow-hidden">

            <IntroBrandMark />

            <div
              className="aurix-glass-sweep absolute inset-y-0 left-0 w-1/3 pointer-events-none"
              aria-hidden="true"
            >
              <div className="h-full w-full bg-gradient-to-r from-transparent via-white/30 to-transparent blur-sm" />
            </div>

          </div>

          <div
            className={`mt-3 transition-opacity duration-300 ${
              isFlying
                ? 'opacity-0'
                : 'opacity-100'
            }`}
            style={{
              animation:
                !isFlying
                  ? `aurix-pure-fade-in 1.2s ease-in-out ${
                      (
                        INTRO_TIMELINE.intelligenceDelay +
                        200
                      ) / 1000
                    }s both`
                  : undefined,
            }}
          >
            <span className="font-mono text-sm lg:text-base uppercase tracking-[0.45em] text-transparent bg-clip-text bg-gradient-to-r from-[#D4AF37] via-[#F3E5AB] to-[#D4AF37] font-bold drop-shadow-[0_0_15px_rgba(212,175,55,0.5)]">
              INTELLIGENCE
            </span>
          </div>

          <div
            className={`mt-3.5 ${
              isFlying
                ? 'opacity-0'
                : 'opacity-100'
            }`}
            style={{
              animation:
                !isFlying
                  ? `aurix-pure-fade-in 1.2s ease-in-out ${
                      (
                        INTRO_TIMELINE.taglineDelay +
                        200
                      ) / 1000
                    }s both`
                  : undefined,
              transition:
                'opacity 300ms ease',
            }}
          >
            <span className="text-xs sm:text-sm text-slate-300 tracking-[0.38em] uppercase leading-tight font-medium whitespace-nowrap">
              Transforming Enterprise Decisions
            </span>
          </div>

        </div>
      </div>

      {audioBlocked &&
        !audioStarted &&
        !isFlying && (
          <button
            onClick={
              handleEnableSound
            }
            aria-label="Enable intro sound"
            title="Enable intro sound"
            className="absolute bottom-8 right-8 z-20 pointer-events-auto w-10 h-10 rounded-full bg-white/[0.06] border border-white/15 backdrop-blur-xl flex items-center justify-center text-white/70 hover:text-white hover:bg-white/[0.12] transition-all duration-300 shadow-[0_4px_20px_rgba(0,0,0,0.4)]"
          >
            <svg
              className="w-4 h-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.8}
              aria-hidden="true"
            >
              <path
                d="M11 5 6 9H3v6h3l5 4V5z"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              <path
                d="M16 8a5 5 0 0 1 0 8M19 5a9 9 0 0 1 0 14"
                strokeLinecap="round"
                strokeLinejoin="round"
                opacity="0.5"
              />
            </svg>
          </button>
        )}

      {!isFlying && (
        <button
          type="button"
          onClick={skipIntro}
          aria-label="Skip intro"
          className="absolute bottom-8 left-8 z-20 pointer-events-auto px-3 py-1.5 rounded-lg bg-white/[0.05] border border-white/10 hover:bg-white/[0.1] text-[11px] font-mono tracking-widest text-slate-400 hover:text-white transition-colors cursor-pointer"
        >
          SKIP INTRO [ESC]
        </button>
      )}

    </div>
  );
};
