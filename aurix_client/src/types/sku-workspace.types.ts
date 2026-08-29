import { SkuDemandProfile } from '@/types/eda.types';
import { ChampionModelMetadata, ForecastTimelinePoint } from '@/types/forecast.types';
import { SkuInventoryMetrics } from '@/types/inventory.types';
import { SupplierPerformanceProfile } from '@/types/supply.types';
import { RecommendationItem } from '@/types/recommendation.types';

export interface SkuUnifiedStory {
  skuId: string;
  skuName: string;
  category: string;
  evaluatedAt: string;
  overallHealthStatus: 'OPTIMAL' | 'WATCH' | 'CRITICAL';
  naturalLanguageSummary: string;
  demand: SkuDemandProfile;
  forecast: {
    metadata: ChampionModelMetadata;
    timeline: ForecastTimelinePoint[];
  };
  inventory: SkuInventoryMetrics;
  supplier: SupplierPerformanceProfile;
  activeRecommendations: RecommendationItem[];
}