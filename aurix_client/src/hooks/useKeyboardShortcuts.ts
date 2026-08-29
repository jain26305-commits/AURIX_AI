"use client";

import { useEffect } from "react";

export interface ShortcutHandlers {
  onOpenCommandPalette?: () => void;
  onCloseDrawer?: () => void;
  onToggleExecutiveMode?: () => void;
  onToggleSidebar?: () => void;
}

export function useKeyboardShortcuts(handlers: ShortcutHandlers) {
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      // Ctrl+K or Cmd+K: Open Command Palette
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        handlers.onOpenCommandPalette?.();
      }
      // Esc: Close any active modal/drawer
      if (e.key === "Escape") {
        handlers.onCloseDrawer?.();
      }
      // Alt+E: Toggle Executive Mode
      if (e.altKey && e.key.toLowerCase() === "e") {
        e.preventDefault();
        handlers.onToggleExecutiveMode?.();
      }
      // Alt+B: Toggle Sidebar Collapse
      if (e.altKey && e.key.toLowerCase() === "b") {
        e.preventDefault();
        handlers.onToggleSidebar?.();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handlers]);
}
