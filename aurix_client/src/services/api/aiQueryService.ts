import { ApiClient } from '@/services/api/apiClient';
import {
  AiQueryRequest,
  AiQueryResponse,
} from '@/types/ai-query.types';

export class AiQueryService {
  public static async executeQuery(
    req: AiQueryRequest,
  ): Promise<AiQueryResponse> {
    return ApiClient.post<AiQueryRequest, AiQueryResponse>(
      '/ai/query',
      req,
    );
  }
}
