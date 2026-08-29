'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import {
  QualityAuditReport,
  QualitySeverity,
} from '@/types/quality.types';
import { QualityService } from '@/services/api/qualityService';

export function useQualityAssessment() {
  const [selectedSeverityFilter, setSelectedSeverityFilter] =
    useState<QualitySeverity | 'all'>('all');

  const [searchTerm, setSearchTerm] = useState<string>('');

  const {
    data: report = null,
    isLoading,
    isFetching,
    refetch,
  } = useQuery<QualityAuditReport>({
    queryKey: ['quality', 'audit-report'],
    queryFn: QualityService.fetchQualityReport,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const filteredAnomalies = report
    ? report.anomalies.filter((item) => {
        const matchesSeverity =
          selectedSeverityFilter === 'all' ||
          item.severity === selectedSeverityFilter;

        const matchesSearch =
          searchTerm === '' ||
          item.field.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (item.skuId &&
            item.skuId.toLowerCase().includes(searchTerm.toLowerCase())) ||
          item.category.toLowerCase().includes(searchTerm.toLowerCase());

        return matchesSeverity && matchesSearch;
      })
    : [];

  return {
    report,
    loading: isLoading || isFetching,
    selectedSeverityFilter,
    setSelectedSeverityFilter,
    searchTerm,
    setSearchTerm,
    filteredAnomalies,
    reloadReport: async () => {
      await refetch();
    },
  };
}
