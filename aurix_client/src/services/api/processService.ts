import { ApiClient } from '@/services/api/apiClient';
import {
  ProcessBottleneckDTO,
  ProcessSummaryDTO,
  ProcessVariantDTO,
} from '@/types/process.types';

export class ProcessService {
  public static async getSummary(periodKey: string = 'CURRENT'): Promise<ProcessSummaryDTO> {
    return ApiClient.get<ProcessSummaryDTO>(
      `/process/summary?period=${encodeURIComponent(periodKey)}`,
      () => ({
        tenantId: 'GLOBAL',
        periodKey: periodKey,
        overallProcessHealthScore: 88.5,
        totalEventsProcessed: 1420,
        activeCasesCount: 145,
        discoveredVariantsCount: 4,
        conformanceRatePct: 94.2,
        slaComplianceRatePct: 91.8,
        averageO2cCycleDays: 42.1,
        averageP2pCycleDays: 43.5,
        topBottleneckStep: 'Payment Settlement & Reconciliation',
        totalProcessFinancialDragUsd: 39780.0,
        evaluatedAt: new Date().toISOString(),
      })
    );
  }

  public static async getBottlenecks(): Promise<ProcessBottleneckDTO[]> {
    return ApiClient.get<ProcessBottleneckDTO[]>('/process/bottlenecks', () => [
      {
        bottleneckId: 'BNK-001',
        processType: 'ORDER_TO_CASH',
        stepName: 'Payment Settlement & Reconciliation',
        queueDepthCases: 34,
        averageWaitingHours: 82.0,
        slaBreachRatePct: 18.5,
        severity: 'HIGH',
        primaryFrictionCause: 'Manual remittance matching and customer payment terms latency.',
        annualizedFinancialDrag: 45000.0,
      },
      {
        bottleneckId: 'BNK-002',
        processType: 'PROCURE_TO_PAY',
        stepName: 'Purchase Order Approval',
        queueDepthCases: 19,
        averageWaitingHours: 41.5,
        slaBreachRatePct: 12.1,
        severity: 'MEDIUM',
        primaryFrictionCause: 'Multi-tier approval routing for orders exceeding $10K threshold.',
        annualizedFinancialDrag: 18400.0,
      },
      {
        bottleneckId: 'BNK-003',
        processType: 'MANUFACTURING_PRODUCTION',
        stepName: 'Quality Inspection Hold',
        queueDepthCases: 8,
        averageWaitingHours: 14.2,
        slaBreachRatePct: 6.4,
        severity: 'LOW',
        primaryFrictionCause: 'Single-shift QA staffing creates overnight inspection backlog.',
        annualizedFinancialDrag: 6200.0,
      },
    ]);
  }

  public static async getVariants(): Promise<ProcessVariantDTO[]> {
    return ApiClient.get<ProcessVariantDTO[]>('/process/variants', () => [
      {
        variantId: 'VAR-O2C-001',
        processType: 'ORDER_TO_CASH',
        stepSequence: ['Order Placed', 'Credit Check', 'Pick & Pack', 'Dispatch', 'Delivery', 'Invoice', 'Payment Received'],
        caseCount: 892,
        frequencyPct: 61.4,
        averageDurationHours: 96.5,
        isStandardPath: true,
      },
      {
        variantId: 'VAR-O2C-002',
        processType: 'ORDER_TO_CASH',
        stepSequence: ['Order Placed', 'Credit Check', 'Credit Hold', 'Manual Override', 'Pick & Pack', 'Dispatch', 'Delivery', 'Invoice', 'Payment Received'],
        caseCount: 214,
        frequencyPct: 14.7,
        averageDurationHours: 142.8,
        isStandardPath: false,
      },
      {
        variantId: 'VAR-P2P-001',
        processType: 'PROCURE_TO_PAY',
        stepSequence: ['PO Created', 'Approval', 'PO Issued', 'Goods Receipt', '3-Way Match', 'Payment'],
        caseCount: 458,
        frequencyPct: 76.2,
        averageDurationHours: 168.0,
        isStandardPath: true,
      },
      {
        variantId: 'VAR-P2P-002',
        processType: 'PROCURE_TO_PAY',
        stepSequence: ['PO Created', 'Approval', 'Rejection', 'Revision', 'Re-Approval', 'PO Issued', 'Goods Receipt', '3-Way Match', 'Payment'],
        caseCount: 96,
        frequencyPct: 16.0,
        averageDurationHours: 231.4,
        isStandardPath: false,
      },
      {
        variantId: 'VAR-RET-001',
        processType: 'RETURNS_AND_REVERSE_LOGISTICS',
        stepSequence: ['Return Initiated', 'Inspection', 'Restock or Disposal', 'Refund Issued'],
        caseCount: 61,
        frequencyPct: 4.1,
        averageDurationHours: 72.3,
        isStandardPath: true,
      },
    ]);
  }
}
