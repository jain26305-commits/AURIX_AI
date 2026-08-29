export type EntityType =
  | 'CUSTOMER'
  | 'SUPPLIER'
  | 'PRODUCT'
  | 'SKU'
  | 'ORDER'
  | 'PURCHASE_ORDER'
  | 'INVOICE'
  | 'PAYMENT'
  | 'SHIPMENT'
  | 'WORK_ORDER'
  | 'WORK_CENTER'
  | 'MACHINE'
  | 'CONTRACT'
  | 'ASSURANCE_FINDING'
  | 'LOCATION';

export type RelationshipType =
  | 'CUSTOMER_OF'
  | 'PLACED_ORDER'
  | 'CONTAINS_ITEM'
  | 'SUPPLIED_BY'
  | 'INVOICED_AS'
  | 'SETTLED_BY'
  | 'FULFILLED_BY_SHIPMENT'
  | 'PRODUCED_VIA'
  | 'ROUTED_TO'
  | 'DEPENDS_ON'
  | 'CONSTRAINED_BY'
  | 'IMPACTS_FINANCE'
  | 'GOVERNED_BY'
  | 'CAUSES'
  | 'ASSOCIATED_WITH';

export interface ContextNodeDTO {
  id: string;
  tenantId: string;
  entityType: EntityType;
  canonicalId: string;
  name: string;
  attributes: Record<string, any>;
  sourceSystem: string;
}

export interface ContextEdgeDTO {
  id: string;
  sourceNodeId: string;
  targetNodeId: string;
  relationshipType: RelationshipType;
  confidenceLevel: string;
  relationshipStatus: string;
  evidence: Record<string, any>;
}

export interface BusinessMemoryRecordDTO {
  id: string;
  category: string;
  title: string;
  description: string;
  contextEntityId?: string;
  outcomeStatus: string;
  lessonsLearned?: string;
  recordedBy: string;
  recordedAt: string;
}

export interface ContextSummaryDTO {
  tenantId: string;
  periodKey: string;
  totalNodesCount: number;
  totalEdgesCount: number;
  activeMemoriesCount: number;
  activeContractsCount: number;
  overallReadinessPct: number;
  businessDnaModel: string;
  evaluatedAt: string;
}
