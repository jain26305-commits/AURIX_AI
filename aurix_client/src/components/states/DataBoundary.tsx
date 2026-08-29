'use client';

import React from 'react';
import {
  LoadingStateView,
  EmptyStateView,
  ErrorStateView,
  DegradedStateView,
} from '@/components/states/StateViews';

export interface DataBoundaryProps {
  isLoading?: boolean;
  isError?: boolean;
  errorMessage?: string;
  isEmpty?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  isDegraded?: boolean;
  degradedMessage?: string;
  onRetry?: () => void;
  loadingMessage?: string;
  children: React.ReactNode;
}

export const DataBoundary: React.FC<DataBoundaryProps> = ({
  isLoading,
  isError,
  errorMessage,
  isEmpty,
  emptyTitle,
  emptyDescription,
  isDegraded,
  degradedMessage,
  onRetry,
  loadingMessage,
  children,
}) => {
  if (isLoading) {
    return <LoadingStateView message={loadingMessage} />;
  }

  if (isError) {
    return <ErrorStateView message={errorMessage} onRetry={onRetry} />;
  }

  if (isEmpty) {
    return <EmptyStateView title={emptyTitle} description={emptyDescription} onAction={onRetry} />;
  }

  return (
    <>
      {isDegraded && <DegradedStateView message={degradedMessage} />}
      {children}
    </>
  );
};
