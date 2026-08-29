import { QualityAuditReport } from '@/types/quality.types';
import { QualityAdapter } from '@/services/adapters/qualityAdapter';

export class QualityService {
  /**
   * Fetches deterministic data quality audit report for the active dataset.
   */
  public static async fetchQualityReport(): Promise<QualityAuditReport> {
    await new Promise((resolve) => setTimeout(resolve, 600));
    return QualityAdapter.generateSimulatedAudit();
  }
}