export interface BomComponent {
  componentSkuId?: string;
  componentId?: string;
  componentName?: string;
  name?: string;
  level?: number;
  quantityPerParent?: number;
  unitOfMeasure?: string;
  leadTimeDays?: number;
  scrapPercentage?: number;
  scrapFactorPercent?: number;
  unitCostINR?: number;
  extendedCostINR?: number;
  supplierName?: string;
  category?: string;
  [key: string]: any;
}

export interface BomHierarchy {
  parentSkuId?: string;
  name?: string;
  version?: string;
  components?: BomComponent[];
  [key: string]: any;
}

export interface ManufacturingSummaryDTO {
  totalWorkOrders?: number;
  overallOeePct?: number;
  netRequirementsUnits?: number;
  scrapRatePct?: number;
  bottlenecksCount?: number;
  [key: string]: any;
}

export interface ManufacturingSummary extends ManufacturingSummaryDTO {}

export interface OEEMetricsDTO {
  availabilityPct?: number;
  performancePct?: number;
  qualityPct?: number;
  overallOeePct?: number;
  [key: string]: any;
}

export interface TimeBucketPlan {
  bucketIndex?: number;
  periodLabel?: string;
  date?: string;
  grossRequirement?: number;
  grossRequirements?: number;
  scheduledReceipts?: number;
  projectedAvailable?: number;
  projectedAvailableBalance?: number;
  netRequirement?: number;
  netRequirements?: number;
  plannedOrderReceipt?: number;
  plannedOrderReceipts?: number;
  plannedOrderRelease?: number;
  plannedOrderReleases?: number;
  [key: string]: any;
}

export interface MrpItemPlan {
  skuId?: string;
  skuName?: string;
  leadTimeDays?: number;
  safetyStock?: number;
  lotSizeRule?: string;
  timeBuckets?: TimeBucketPlan[];
  [key: string]: any;
}

export interface WorkCenterCapacityDTO {
  workCenterId?: string;
  workCenterName?: string;
  name?: string;
  facilityLocation?: string;
  weeklyCapacityHours?: number;
  availableHoursPerWeek?: number;
  allocatedLoadHours?: number;
  requiredHoursPerWeek?: number;
  utilizationPct?: number;
  utilizationPercent?: number;
  isBottleneck?: boolean;
  status?: string;
  primaryConstrainingOperation?: string;
  [key: string]: any;
}

export interface WorkCenterCapacity extends WorkCenterCapacityDTO {}

export interface ManufacturingReport {
  timestamp?: string;
  summary?: ManufacturingSummaryDTO;
  boms?: BomHierarchy[];
  mrpPlans?: MrpItemPlan[];
  workCenters?: WorkCenterCapacityDTO[];
  [key: string]: any;
}
