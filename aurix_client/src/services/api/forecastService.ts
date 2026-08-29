import { ForecastAnalyticsPayload, ForecastHorizon } from '@/types/forecast.types';
import { ForecastAdapter } from '@/services/adapters/forecastAdapter';

export class ForecastService {
  public static async fetchForecastForSku(skuId: string = 'SKU-001', horizon: ForecastHorizon = '3M'): Promise<ForecastAnalyticsPayload> {
    await new Promise((resolve) => setTimeout(resolve, 550));
    return ForecastAdapter.generateSimulatedForecast(skuId, horizon);
  }
}