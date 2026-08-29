'use client';

import { useState, useCallback } from 'react';
import {
  AiQueryResponse,
} from '@/types/ai-query.types';
import { AiQueryService } from '@/services/api/aiQueryService';

export function useContextualAi(
  workspaceContext: string = 'Control Tower',
) {
  const [isOpen, setIsOpen] = useState(false);
  const [queryText, setQueryText] = useState('');
  const [queryHistory, setQueryHistory] = useState<AiQueryResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const submitQuery = useCallback(
    async (customText?: string) => {
      const textToSubmit = (customText ?? queryText).trim();

      if (!textToSubmit || isLoading) {
        return;
      }

      setIsLoading(true);

      try {
        const response = await AiQueryService.executeQuery({
          query: textToSubmit,
          page_context: {
            current_page: workspaceContext,
          },
        });

        setQueryHistory((prev) => [response, ...prev]);
        setQueryText('');
      } catch (error) {
        console.error(
          '[useContextualAi] Query execution failed:',
          error,
        );
      } finally {
        setIsLoading(false);
      }
    },
    [queryText, workspaceContext, isLoading],
  );

  return {
    isOpen,
    setIsOpen,
    queryText,
    setQueryText,
    queryHistory,
    isLoading,
    submitQuery,
  };
}
