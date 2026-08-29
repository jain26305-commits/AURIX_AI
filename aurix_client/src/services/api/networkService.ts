import { NetworkAnalyticsReport } from '@/types/network.types';
import { NetworkAdapter } from '@/services/adapters/networkAdapter';

export class NetworkService {
  public static async fetchNetworkTopology(): Promise<NetworkAnalyticsReport> {
    await new Promise((resolve) => setTimeout(resolve, 500));
    return NetworkAdapter.generateSimulatedNetwork();
  }
}