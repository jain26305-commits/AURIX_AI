export type ReturnDisposition =
  | 'RESTOCK'
  | 'REWORK'
  | 'SCRAP'
  | 'LIQUIDATE'
  | 'PENDING_INSPECTION';

export type ReturnReason =
  | 'SIZE_FIT'
  | 'FABRIC_DEFECT'
  | 'SHIPPING_DAMAGE'
  | 'BUYER_REMORSE'
  | 'WRONG_ITEM';

export interface ReturnRecord {
  rmaNumber: string;
  orderId: string;
  skuId: string;
  skuName: string;
  customerName: string;
  returnReason: ReturnReason;
  disposition: ReturnDisposition;
  returnQty: number;
  refundAmountINR: number;
  salvageValueINR: number;
  netFinancialLossINR: number;
  requestedDate: string;
  inspectedDate?: string;
  inspectionNotes?: string;
}

export interface DispositionMetric {
  disposition: ReturnDisposition;
  unitsCount: number;
  percentageOfTotal: number;
  totalRefundINR: number;
  salvageRecoveryINR: number;
}

export interface ReturnsSummary {
  totalReturnsCount: number;
  totalReturnedUnits: number;
  aggregateRefundINR: number;
  netLossINR: number;
  portfolioReturnRatePercent: number;
  topReturnReason: ReturnReason;
  dispositionMetrics: DispositionMetric[];
}

export interface ReturnsReport {
  evaluatedAt: string;
  summary: ReturnsSummary;
  returns: ReturnRecord[];
}