'use client';

import { useState, useCallback } from 'react';
import { IntakeState } from '@/types/data-intake.types';
import { IntakeService } from '@/services/api/intakeService';
import { validateSchemaMappings } from '@/lib/validators';

const INITIAL_STATE: IntakeState = {
  stage: 'idle',
  progressPercent: 0,
  metadata: null,
  mappings: [],
  previewRows: [],
  validationIssues: [],
  isSubmitting: false,
};

export function useDataIntake() {
  const [state, setState] = useState<IntakeState>(INITIAL_STATE);

  const processUploadedFile = useCallback(async (file: File) => {
    setState((prev) => ({
      ...prev,
      stage: 'file_received',
      progressPercent: 20,
      errorMessage: undefined,
    }));

    try {
      await new Promise((r) => setTimeout(r, 400));
      setState((prev) => ({ ...prev, stage: 'understanding_data', progressPercent: 45 }));

      const { metadata, mappings, previewRows, validationIssues } = await IntakeService.uploadOperationalData(file);

      setState((prev) => ({ ...prev, stage: 'mapping_structure', progressPercent: 75 }));
      await new Promise((r) => setTimeout(r, 400));

      setState((prev) => ({ ...prev, stage: 'validating', progressPercent: 90 }));
      const customIssues = validateSchemaMappings(mappings);
      await new Promise((r) => setTimeout(r, 300));

      setState({
        stage: 'ready',
        progressPercent: 100,
        metadata,
        mappings,
        previewRows,
        validationIssues: [...validationIssues, ...customIssues],
        isSubmitting: false,
      });
    } catch (err: unknown) {
      setState((prev) => ({
        ...prev,
        stage: 'error',
        progressPercent: 0,
        errorMessage: err instanceof Error ? err.message : 'An error occurred during file ingestion.',
      }));
    }
  }, []);

  const updateColumnMapping = useCallback((canonicalKey: string, newDetectedColumn: string) => {
    setState((prev) => {
      const updatedMappings = prev.mappings.map((item) => {
        if (item.canonicalKey === canonicalKey) {
          return {
            ...item,
            detectedColumn: newDetectedColumn === 'UNMAPPED' ? null : newDetectedColumn,
            confidence: 'manual' as const,
            status: (item.required && newDetectedColumn === 'UNMAPPED' ? 'missing' : 'valid') as 'valid' | 'missing',
          };
        }
        return item;
      });

      const recalculatedIssues = validateSchemaMappings(updatedMappings);

      return {
        ...prev,
        mappings: updatedMappings,
        validationIssues: recalculatedIssues,
      };
    });
  }, []);

  const resetIntake = useCallback(() => {
    setState(INITIAL_STATE);
  }, []);

  return {
    ...state,
    processUploadedFile,
    updateColumnMapping,
    resetIntake,
  };
}