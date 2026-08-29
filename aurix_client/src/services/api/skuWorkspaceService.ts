import { SkuUnifiedStory } from '@/types/sku-workspace.types';
import { SkuWorkspaceAdapter } from '@/services/adapters/skuWorkspaceAdapter';
import { ApiClient } from '@/services/api/apiClient';

export class SkuWorkspaceService {
  public static async fetchSkuStory(skuId: string): Promise<SkuUnifiedStory> {
    return ApiClient.get<SkuUnifiedStory>(
      `/workspace/sku/${skuId}`,
      () => SkuWorkspaceAdapter.generateUnifiedSkuStory(skuId)
    );
  }
}