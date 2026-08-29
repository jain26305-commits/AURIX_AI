import {
  RecommendationFeedReport,
  WorkflowStatus,
} from '@/types/recommendation.types';
import { IntelligenceAdapter } from '@/services/adapters/intelligenceAdapter';

export class RecommendationService {
  public static async fetchRecommendationFeed(): Promise<RecommendationFeedReport> {
    await new Promise((resolve) => setTimeout(resolve, 500));

    return IntelligenceAdapter.generateSimulatedRecommendations();
  }

  public static async updateActionStatus(
    recommendationId: string,
    status: WorkflowStatus
  ): Promise<boolean> {
    const response = await fetch(
      `/api/v1/recommendations/${recommendationId}/status`,
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status }),
      }
    );

    if (!response.ok) {
      throw new Error(
        `Failed to update recommendation ${recommendationId}: ${response.status}`
      );
    }

    return true;
  }
}