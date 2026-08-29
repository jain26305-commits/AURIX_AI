export type AssuranceDomain =
  | 'THREE_WAY_MATCH'
  | 'DOUBLE_PAYMENT'
  | 'UNBILLED_SHIPMENT'
  | 'PHANTOM_INVENTORY'
  | 'PRICE_VARIANCE'
  | 'CONTRACT_COMPLIANCE'
  | 'VENDOR_SLA';

export type LeakageSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type FindingStatus =
  | 'OPEN'
  | 'IN_REVIEW'
  | 'ACTION_PROPOSED'
  | 'REMEDIATED'
  | 'FALSE_POSITIVE'
  | 'SUPPRESSED';

export interface AssuranceFindingDTO {
  finding_id: string;
  tenant_id: string;
  domain: AssuranceDomain;
  severity: LeakageSeverity;
  status: FindingStatus;
  title: string;
  description: string;
  financial_exposure: number;
  currency: string;
  entity_type: string;
  entity_id: string;
  evidence_data: Record<string, any>;
  recommended_action?: string;
  detected_at: string;
}

export interface AssuranceMetricsDTO {
  tenant_id: string;
  total_findings_count: number;
  total_financial_leakage: number;
  critical_severity_count: number;
  high_severity_count: number;
  leakage_by_domain: Record<string, number>;
  findings_count_by_domain: Record<string, number>;
}
