import { EdaAnalyticsReport } from '@/types/eda.types';
import { EdaAdapter } from '@/services/adapters/edaAdapter';

export class EdaService {
  public static async fetchEdaAnalytics(): Promise<EdaAnalyticsReport> {
    await new Promise((resolve) => setTimeout(resolve, 500));
    return EdaAdapter.generateSimulatedEda();
  }
}