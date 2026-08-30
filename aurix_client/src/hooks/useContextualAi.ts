'use client';

import { useState, useCallback } from 'react';
import {
  AiQueryResponse,
} from '@/types/ai-query.types';
import { AiQueryService } from '@/services/api/aiQueryService';
export interface AiQueryUiError {
  code: string;
  message: string;
  statusCode?: number;
}

export function useContextualAi(
  workspaceContext: string = 'Control Tower',
) {
  const [isOpen, setIsOpen] = useState(false);
  const [queryText, setQueryText] = useState('');
  const [queryHistory, setQueryHistory] = useState<AiQueryResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<AiQueryUiError | null>(null);

  const submitQuery = useCallback(
    async (customText?: string) => {
      const textToSubmit = (customText ?? queryText).trim();

      if (!textToSubmit || isLoading) {
        return;
      }

      setError(null);
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
      } catch (caught: unknown) {
        const candidate = caught as {
          message?: string;
          code?: string;
          statusCode?: number;
        };

        const message =
          typeof candidate?.message === 'string' &&
          candidate.message.trim()
            ? candidate.message
            : 'AURIX AI could not complete this request. Please try again.';

        setError({
          code:
            typeof candidate?.code === 'string' && candidate.code
              ? candidate.code
              : 'AI_QUERY_FAILED',
          message,
          statusCode:
            typeof candidate?.statusCode === 'number'
              ? candidate.statusCode
              : undefined,
        });

        console.error(
          '[useContextualAi] Query execution failed:',
          caught,
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
    error,
    submitQuery,
    clearError: () => setError(null),
  };
}
