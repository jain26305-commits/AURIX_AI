export type SalesOrderStatus =
  | 'ALLOCATED'
  | 'PARTIALLY_ALLOCATED'
  | 'BACKORDERED'
  | 'FULFILLED'
  | 'CANCELLED';

export type SalesChannel = 'E-COMMERCE' | 'B2B_WHOLESALE' | 'RETAIL_STORE';

export interface SalesOrderItem {
  orderId: string;
  customerName: string;
  channel: SalesChannel;
  orderDate: string;
  promisedDate: string;
  skuId: string;
  skuName: string;
  orderedUnits: number;
  allocatedUnits: number;
  totalAmountINR: number;
  status: SalesOrderStatus;
  allocationPercent: number;
  shippingPriority: 'STANDARD' | 'EXPEDITED' | 'SAME_DAY';
}

export interface AtpInquiryRequest {
  skuId: string;
  requestedUnits: number;
  targetDate: string;
}

export interface AtpInquiryResponse {
  skuId: string;
  skuName: string;
  requestedUnits: number;
  availableToPromiseUnits: number;
  capableToPromiseUnits: number;
  onHandStockUnits: number;
  allocatedStockUnits: number;
  plannedReceiptsUnits: number;
  canFulfillImmediately: boolean;
  promisedDeliveryDate: string;
  leadTimeDaysRequired: number;
  constrainingFactor?: string;
}

export interface FulfillmentSummary {
  totalOrdersCount: number;
  onTimeFulfillmentRatePercent: number;
  backorderedUnitsCount: number;
  totalOrderValueINR: number;
  allocatedRevenueINR: number;
  immediateAtpCoveragePercent: number;
}

export interface FulfillmentReport {
  evaluatedAt: string;
  summary: FulfillmentSummary;
  orders: SalesOrderItem[];
}