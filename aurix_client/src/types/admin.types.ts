export type ConnectorType = 'ERP_SAP' | 'WMS_MANHATTAN' | 'TMS_FREIGHT' | 'SHOPIFY_COMMERCE' | 'POSTGRES_CDC';
export type ConnectorStatus = 'CONNECTED' | 'DEGRADED' | 'DISCONNECTED' | 'SYNCING';

export interface EnterpriseConnector {
  connectorId: string;
  name: string;
  type: ConnectorType;
  status: ConnectorStatus;
  lastSyncTimestamp: string;
  recordsSyncedLast24h: number;
  errorRatePercent: number;
  syncFrequency: string;
  endpointMasked: string;
  healthNote: string;
}

export interface ModelRegistryEntry {
  modelId: string;
  modelName: string;
  algorithmFamily: 'XGBOOST' | 'SARIMA' | 'PROPHET' | 'ETS' | 'NEURAL_PROPHET';
  version: string;
  isChampion: boolean;
  targetDomain: 'DEMAND_FORECAST' | 'LEAD_TIME_QUANTILE' | 'ANOMALY_DETECTION';
  wapePercent: number;
  rmse: number;
  driftStatus: 'STABLE' | 'MODERATE_DRIFT' | 'CRITICAL_DRIFT';
  lastTrainedAt: string;
  trainingSamplesCount: number;
  deployedEnvironment: 'PRODUCTION' | 'STAGING' | 'CANARY';
}

export interface ServiceHealthMetric {
  serviceKey: string;
  serviceName: string;
  status: 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY';
  latencyMs: number;
  uptimePercent: number;
  activeWorkersOrConnections: number;
  resourceUtilizationPercent: number;
  lastCheckedAt: string;
}

export interface SystemHealthReport {
  evaluatedAt: string;
  overallHealth: 'HEALTHY' | 'DEGRADED' | 'CRITICAL';
  meanApiLatencyMs: number;
  activeDatabaseConnections: number;
  celeryQueueDepth: number;
  services: ServiceHealthMetric[];
}

export interface AdminUserRecord {
  userId: string;
  email: string;
  fullName: string;
  role: 'SUPER_ADMIN' | 'EXECUTIVE' | 'PLANNER' | 'ANALYST' | 'AUDITOR';
  tenantId: string;
  status: 'ACTIVE' | 'SUSPENDED' | 'INVITED';
  lastLoginAt: string;
  mfaEnabled: boolean;
}

export interface SystemAuditLogEntry {
  logId: string;
  timestamp: string;
  actorEmail: string;
  actorRole: string;
  actionCategory: 'SECURITY' | 'ACTION_EXECUTION' | 'MODEL_DEPLOYMENT' | 'DATA_INGESTION';
  eventSummary: string;
  ipAddress: string;
  resultStatus: 'SUCCESS' | 'REJECTED' | 'FAILED';
}