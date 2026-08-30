'use client';

import React, { useState } from 'react';
import { EnterpriseSidebar } from '@/components/navigation/EnterpriseSidebar';
import { EnterpriseHeader } from '@/components/navigation/EnterpriseHeader';
import { CommandPalette } from '@/components/modals/CommandPalette';
import { NotificationDrawer } from '@/components/notifications/NotificationDrawer';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { useSidebar } from '@/context/SidebarContext';
import { useWorkspaceHeaderContext } from '@/context/WorkspaceHeaderContext';
import { useContextualAi } from '@/hooks/useContextualAi';
import { ContextualAiDrawer } from '@/components/features/ai/ContextualAiDrawer';

export interface AppShellProps {
  children: React.ReactNode;
}

/**
 * The single, app-wide chrome: sidebar + header + command palette +
 * notification drawer + AURIX AI drawer.
 */
export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const { isCollapsed, toggleSidebar } = useSidebar();
  const { header } = useWorkspaceHeaderContext();

  const [isExecutiveMode, setIsExecutiveMode] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const ai = useContextualAi(
    header.activeWorkspaceTitle ||
      header.subdomainTitle ||
      header.domainTitle ||
      'Control Tower',
  );

  useKeyboardShortcuts({
    onOpenCommandPalette: () => setPaletteOpen(true),
    onCloseDrawer: () => {
      setPaletteOpen(false);
      setNotificationsOpen(false);
      ai.setIsOpen(false);
    },
    onToggleExecutiveMode: () => setIsExecutiveMode((m) => !m),
    onToggleSidebar: toggleSidebar,
  });

  return (
    <div className="min-h-screen bg-[#030303] text-[#F9FAFB] flex font-sans selection:bg-[#D4AF37]/30 selection:text-white">
      <EnterpriseSidebar
        isCollapsed={isCollapsed}
        onToggle={toggleSidebar}
      />

      <div
        className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ${
          isCollapsed ? 'ml-20' : 'ml-64'
        }`}
      >
        <EnterpriseHeader
          domainTitle={header.domainTitle}
          subdomainTitle={header.subdomainTitle}
          activeWorkspaceTitle={header.activeWorkspaceTitle}
          activeSku={header.activeSku}
          isExecutiveMode={isExecutiveMode}
          onToggleExecutiveMode={() =>
            setIsExecutiveMode((value) => !value)
          }
          onOpenPalette={() => setPaletteOpen(true)}
          onOpenNotifications={() => setNotificationsOpen(true)}
          onOpenAi={() => ai.setIsOpen(true)}
        />

        <main className="flex-1 p-6 sm:p-8 max-w-[1700px] w-full mx-auto overflow-y-auto">
          {children}
        </main>
      </div>

      <CommandPalette
        isOpen={paletteOpen}
        onClose={() => setPaletteOpen(false)}
      />

      <NotificationDrawer
        isOpen={notificationsOpen}
        onClose={() => setNotificationsOpen(false)}
      />

      <ContextualAiDrawer
        isOpen={ai.isOpen}
        onClose={() => ai.setIsOpen(false)}
        queryText={ai.queryText}
        onQueryTextChange={ai.setQueryText}
        onSubmitQuery={ai.submitQuery}
        queryHistory={ai.queryHistory}
        isLoading={ai.isLoading}
        error={ai.error}
workspaceTitle={
          header.activeWorkspaceTitle ||
          header.subdomainTitle ||
          header.domainTitle ||
          'Control Tower'
        }
      />
    </div>
  );
};
