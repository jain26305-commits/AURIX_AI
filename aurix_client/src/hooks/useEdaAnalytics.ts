'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { EdaAnalyticsReport, AbcClass, XyzClass } from '@/types/eda.types';
import { EdaService } from '@/services/api/edaService';

export function useEdaAnalytics() {
  const [selectedSkuId, setSelectedSkuId] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedAbc, setSelectedAbc] = useState<AbcClass | 'all'>('all');
  const [selectedXyz, setSelectedXyz] = useState<XyzClass | 'all'>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const {
    data: report = null,
    isLoading,
    isFetching,
    refetch,
  } = useQuery<EdaAnalyticsReport>({
    queryKey: ['eda', 'analytics'],
    queryFn: EdaService.fetchEdaAnalytics,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const effectiveSelectedSkuId =
    selectedSkuId ?? report?.skuProfiles[0]?.skuId ?? null;

  const categories = report
    ? Array.from(new Set(report.skuProfiles.map((p) => p.category)))
    : [];

  const filteredSkus = report
    ? report.skuProfiles.filter((p) => {
        const matchesCategory =
          selectedCategory === 'all' || p.category === selectedCategory;

        const matchesAbc =
          selectedAbc === 'all' || p.abcClass === selectedAbc;

        const matchesXyz =
          selectedXyz === 'all' || p.xyzClass === selectedXyz;

        const matchesSearch =
          searchTerm === '' ||
          p.skuName.toLowerCase().includes(searchTerm.toLowerCase()) ||
          p.skuId.toLowerCase().includes(searchTerm.toLowerCase());

        return matchesCategory && matchesAbc && matchesXyz && matchesSearch;
      })
    : [];

  const activeSkuProfile =
    report?.skuProfiles.find(
      (p) => p.skuId === effectiveSelectedSkuId
    ) || report?.skuProfiles[0];

  return {
    report,
    loading: isLoading || isFetching,
    categories,
    selectedCategory,
    setSelectedCategory,
    selectedAbc,
    setSelectedAbc,
    selectedXyz,
    setSelectedXyz,
    searchTerm,
    setSearchTerm,
    filteredSkus,
    selectedSkuId: effectiveSelectedSkuId,
    setSelectedSkuId,
    activeSkuProfile,
    reload: async () => {
      await refetch();
    },
  };
}
