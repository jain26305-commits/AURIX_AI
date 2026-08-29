import { ApiClient } from '@/services/api/apiClient';
import {
  APAgingReportDTO,
  ARAgingReportDTO,
  FinancialAnomalyDTO,
  FinancialExposureReport,
  FinanceSummaryDTO,
  PnLStatementDTO,
  WorkingCapitalDTO,
} from '@/types/finance.types';
import { FinanceAdapter } from '@/services/adapters/financeAdapter';

export class FinanceService {
  // Preserved Phase 8 economics method
  public static async fetchFinancialExposure(): Promise<FinancialExposureReport> {
    return ApiClient.get<FinancialExposureReport>(
      '/economics/working-capital',
      () => FinanceAdapter.generateSimulatedFinancials()
    );
  }

  // Phase 21 Business Finance Intelligence Endpoints
  public static async getFinanceSummary(periodKey: string = 'CURRENT'): Promise<FinanceSummaryDTO> {
    return ApiClient.get<FinanceSummaryDTO>(
      `/finance/summary?period=${encodeURIComponent(periodKey)}`,
      () => ({
        tenantId: 'GLOBAL',
        reportingCurrency: 'USD',
        fiscalPeriod: periodKey,
        grossRevenue: 1250000.0,
        netRevenue: 1215000.0,
        cogs: 720000.0,
        grossProfit: 495000.0,
        grossMarginPercent: 40.74,
        operatingWorkingCapital: 385000.0,
        cashConversionCycleDays: 48.5,
        daysSalesOutstanding: 38.2,
        daysPayablesOutstanding: 31.7,
        daysInventoryOutstanding: 42.0,
        activeAnomaliesCount: 2,
        totalReceivablesOverdue: 45000.0,
        evaluatedAt: new Date().toISOString(),
      })
    );
  }

  public static async getPnL(periodKey: string = 'CURRENT'): Promise<PnLStatementDTO> {
    return ApiClient.get<PnLStatementDTO>(
      `/finance/pnl?period=${encodeURIComponent(periodKey)}`,
      () => ({
        tenantId: 'GLOBAL',
        periodKey: periodKey,
        grossRevenue: 1250000.0,
        returns: 20000.0,
        discounts: 10000.0,
        credits: 5000.0,
        netRevenue: 1215000.0,
        cogs: 720000.0,
        grossProfit: 495000.0,
        grossMarginPercent: 40.74,
        operatingExpenses: null,
        operatingProfit: null,
        operatingProfitStatus: 'UNAVAILABLE',
        ebitda: null,
        ebitdaStatus: 'UNAVAILABLE',
      })
    );
  }

  public static async getAR(): Promise<ARAgingReportDTO> {
    return ApiClient.get<ARAgingReportDTO>('/finance/ar', () => ({
      tenantId: 'GLOBAL',
      totalReceivables: 320000.0,
      totalOverdue: 45000.0,
      dsoDays: 38.2,
      buckets: [
        { bucket: 'CURRENT', label: 'Current', totalAmount: 275000.0, invoicesCount: 42, percentOfTotal: 85.9 },
        { bucket: '1_30', label: '1–30 Days', totalAmount: 30000.0, invoicesCount: 6, percentOfTotal: 9.4 },
        { bucket: '31_60', label: '31–60 Days', totalAmount: 10000.0, invoicesCount: 2, percentOfTotal: 3.1 },
        { bucket: '61_90', label: '61–90 Days', totalAmount: 5000.0, invoicesCount: 1, percentOfTotal: 1.6 },
        { bucket: '90_PLUS', label: '90+ Days', totalAmount: 0.0, invoicesCount: 0, percentOfTotal: 0.0 },
      ],
      topOverdueCustomers: [
        {
          customerId: 'CUST-001',
          customerName: 'Acme Retail Corp',
          overdueAmount: 30000.0,
          oldestInvoiceDays: 28,
          riskTier: 'MEDIUM',
        },
      ],
    }));
  }

  public static async getAP(): Promise<APAgingReportDTO> {
    return ApiClient.get<APAgingReportDTO>('/finance/ap', () => ({
      tenantId: 'GLOBAL',
      totalPayables: 240000.0,
      totalOverdue: 12000.0,
      dpoDays: 31.7,
      buckets: [
        { bucket: 'CURRENT', label: 'Current', totalAmount: 228000.0, invoicesCount: 35 },
        { bucket: '1_30', label: '1–30 Days', totalAmount: 12000.0, invoicesCount: 3 },
        { bucket: '31_60', label: '31–60 Days', totalAmount: 0.0, invoicesCount: 0 },
        { bucket: '61_90', label: '61–90 Days', totalAmount: 0.0, invoicesCount: 0 },
        { bucket: '90_PLUS', label: '90+ Days', totalAmount: 0.0, invoicesCount: 0 },
      ],
      upcomingDisbursements: [
        {
          supplierId: 'SUPP-001',
          supplierName: 'Apex Raw Materials',
          amount: 45000.0,
          dueDate: new Date(Date.now() + 86400000 * 5).toISOString(),
          discountAvailable: true,
        },
      ],
    }));
  }

  public static async getWorkingCapital(): Promise<WorkingCapitalDTO> {
    return ApiClient.get<WorkingCapitalDTO>('/finance/working-capital', () => ({
      tenantId: 'GLOBAL',
      inventoryValuation: 305000.0,
      accountsReceivable: 320000.0,
      accountsPayable: 240000.0,
      operatingWorkingCapital: 385000.0,
      dsoDays: 38.2,
      dioDays: 42.0,
      dpoDays: 31.7,
      cashConversionCycleDays: 48.5,
      drivers: [
        { driver: 'Accounts Receivable Collection Speed', impactDays: -2.4, capitalImpact: -18000.0, direction: 'FAVORABLE' },
        { driver: 'Inventory Holding Growth', impactDays: 4.1, capitalImpact: 32000.0, direction: 'UNFAVORABLE' },
      ],
    }));
  }

  public static async getAnomalies(): Promise<FinancialAnomalyDTO[]> {
    return ApiClient.get<FinancialAnomalyDTO[]>('/finance/anomalies', () => [
      {
        anomalyId: 'ANOM-FIN-001',
        domain: 'GROSS_MARGIN',
        severity: 'HIGH',
        title: 'Gross Margin Dilution on SKU-STEEL-01',
        description: 'Margin dropped from 42.0% to 28.5% due to unfavorable vendor PPV.',
        detectedDeviationPercent: -13.5,
        impactAmount: 14500.0,
        entityId: 'SKU-STEEL-01',
        detectedAt: new Date().toISOString(),
      },
    ]);
  }
}
