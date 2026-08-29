import { ControlTowerReport } from '@/types/control-tower.types';
import { ControlTowerAdapter } from '@/services/adapters/controlTowerAdapter';

export class ControlTowerService {
  public static async fetchControlTowerSnapshot(): Promise<ControlTowerReport> {
    await new Promise((resolve) => setTimeout(resolve, 500));
    return ControlTowerAdapter.generateSimulatedControlTower();
  }
}