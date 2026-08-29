import { ApiClient } from '@/services/api/apiClient';
import { ReturnsReport } from '@/types/returns.types';
import { ReturnsAdapter } from '@/services/adapters/returnsAdapter';

export class ReturnsService {
  public static async fetchReturnsReport(): Promise<ReturnsReport> {
    return ApiClient.get<ReturnsReport>(
      '/returns/summary',
      () => ReturnsAdapter.generateSimulatedReturns()
    );
  }
}