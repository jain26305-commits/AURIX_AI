export type PoLifecycleStatus =
  | 'DRAFT'
  | 'ISSUED'
  | 'ACKNOWLEDGED'
  | 'IN_TRANSIT'
  | 'RECEIVED'
  | 'RECONCILED'
  | 'CANCELLED';

export type ThreeWayMatchStatus =
  | 'MATCHED'
  | 'DISCREPANCY_QUANTITY'
  | 'DISCREPANCY_PRICE'
  | 'PENDING_RECEIPT'
  | 'PENDING_INVOICE';

export interface PoLineItem {
  lineId: string;
  skuId: string;
  skuName: string;
  orderedQty: number;
  receivedQty: number;
  invoicedQty: number;
  unitPriceINR: number;
  totalPriceINR: number;
}

export interface PurchaseOrder {
  poNumber: string;
  vendorId: string;
  vendorName: string;
  status: PoLifecycleStatus;
  orderDate: string;
  promisedDeliveryDate: string;
  revisedEtaDate?: string;
  totalAmountINR: number;
  lineItems: PoLineItem[];
  currency: string;
  paymentTerms: string;
  inboundCarrier?: string;
  trackingNumber?: string;
  asnNumber?: string;
}

export interface AdvanceShippingNotice {
  asnNumber: string;
  poNumber: string;
  vendorName: string;
  carrier: string;
  trackingNumber: string;
  shippedDate: string;
  estimatedArrival: string;
  itemCount: number;
  totalUnits: number;
  status: 'DISPATCHED' | 'CUSTOMS_CLEARANCE' | 'IN_TRANSIT' | 'DELIVERED';
}

export interface ThreeWayMatchRecord {
  matchId: string;
  poNumber: string;
  vendorName: string;
  invoiceNumber: string;
  poAmountINR: number;
  grnAmountINR: number;
  invoiceAmountINR: number;
  varianceINR: number;
  status: ThreeWayMatchStatus;
  auditedTimestamp: string;
  discrepancyNote?: string;
}

export interface ProcurementSummary {
  totalOpenOrdersCount: number;
  activeInboundValueINR: number;
  threeWayMatchPassRatePercent: number;
  pendingAsnCount: number;
  criticalDelayedOrdersCount: number;
  reconciledOrdersCount: number;
}

export interface ProcurementReport {
  evaluatedAt: string;
  summary: ProcurementSummary;
  purchaseOrders: PurchaseOrder[];
  asns: AdvanceShippingNotice[];
  matches: ThreeWayMatchRecord[];
}