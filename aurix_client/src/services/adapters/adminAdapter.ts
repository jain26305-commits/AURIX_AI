import {
  AdminUserRecord,
  EnterpriseConnector,
  ModelRegistryEntry,
  SystemAuditLogEntry,
  SystemHealthReport,
} from '@/types/admin.types';

export class AdminAdapter {
  public static generateSimulatedConnectors(): EnterpriseConnector[] {
    return [
      {
        connectorId: 'CONN-SAP-01',
        name: 'SAP S/4HANA Enterprise ERP Gateway',
        type: 'ERP_SAP',
        status: 'CONNECTED',
        lastSyncTimestamp: '2 minutes ago',
        recordsSyncedLast24h: 184520,
        errorRatePercent: 0.02,
        syncFrequency: 'Every 5 minutes (CDC)',
        endpointMasked: 'https://sap-gateway.internal.aurix.ai/***',
        healthNote: 'Operational. Bi-directional PO and Goods Receipt sync active.',
      },
      {
        connectorId: 'CONN-WMS-02',
        name: 'Manhattan WMS Fulfillment Bridge',
        type: 'WMS_MANHATTAN',
        status: 'CONNECTED',
        lastSyncTimestamp: '4 minutes ago',
        recordsSyncedLast24h: 94210,
        errorRatePercent: 0.00,
        syncFrequency: 'Near Real-Time Webhooks',
        endpointMasked: 'https://wms-blr-dc.internal.aurix.ai/***',
        healthNote: 'Operational. Dock receiving and bin allocations synchronized.',
      },
      {
        connectorId: 'CONN-TMS-03',
        name: 'Freight Carrier Telematics & GPS Listener',
        type: 'TMS_FREIGHT',
        status: 'DEGRADED',
        lastSyncTimestamp: '18 minutes ago',
        recordsSyncedLast24h: 12450,
        errorRatePercent: 2.84,
        syncFrequency: 'Every 15 minutes',
        endpointMasked: 'https://tms-gateway.gatikwe.com/***',
        healthNote: 'Intermittent timeout responses detected on Gati KWE GPS webhook.',
      },
      {
        connectorId: 'CONN-SHP-04',
        name: 'Shopify Plus Omnichannel Commerce',
        type: 'SHOPIFY_COMMERCE',
        status: 'CONNECTED',
        lastSyncTimestamp: '1 minute ago',
        recordsSyncedLast24h: 4210,
        errorRatePercent: 0.00,
        syncFrequency: 'Instantaneous Webhooks',
        endpointMasked: 'https://quidch-store.myshopify.com/***',
        healthNote: 'Operational. Real-time orders and inventory levels synced.',
      },
    ];
  }

  public static generateSimulatedModels(): ModelRegistryEntry[] {
    return [
      {
        modelId: 'MDL-FCST-XGB-V4',
        modelName: 'XGBoost Multi-Horizon Demand Predictor',
        algorithmFamily: 'XGBOOST',
        version: 'v4.2.1',
        isChampion: true,
        targetDomain: 'DEMAND_FORECAST',
        wapePercent: 8.2,
        rmse: 14.8,
        driftStatus: 'STABLE',
        lastTrainedAt: '2025-02-10 03:00 AM IST',
        trainingSamplesCount: 145000,
        deployedEnvironment: 'PRODUCTION',
      },
      {
        modelId: 'MDL-FCST-SARIMA-V3',
        modelName: 'Seasonal ARIMA Benchmark Challenger',
        algorithmFamily: 'SARIMA',
        version: 'v3.1.0',
        isChampion: false,
        targetDomain: 'DEMAND_FORECAST',
        wapePercent: 11.4,
        rmse: 18.2,
        driftStatus: 'STABLE',
        lastTrainedAt: '2025-02-10 03:30 AM IST',
        trainingSamplesCount: 145000,
        deployedEnvironment: 'STAGING',
      },
      {
        modelId: 'MDL-LT-QUANT-V2',
        modelName: 'Empirical Lead-Time Quantile Estimator',
        algorithmFamily: 'ETS',
        version: 'v2.0.4',
        isChampion: true,
        targetDomain: 'LEAD_TIME_QUANTILE',
        wapePercent: 6.8,
        rmse: 2.1,
        driftStatus: 'MODERATE_DRIFT',
        lastTrainedAt: '2025-02-08 02:00 AM IST',
        trainingSamplesCount: 8400,
        deployedEnvironment: 'PRODUCTION',
      },
    ];
  }

  public static generateSimulatedSystemHealth(): SystemHealthReport {
    return {
      evaluatedAt: new Date().toISOString(),
      overallHealth: 'HEALTHY',
      meanApiLatencyMs: 28.4,
      activeDatabaseConnections: 14,
      celeryQueueDepth: 3,
      services: [
        {
          serviceKey: 'SRV-FASTAPI',
          serviceName: 'FastAPI Canonical API Engine',
          status: 'HEALTHY',
          latencyMs: 18.2,
          uptimePercent: 99.98,
          activeWorkersOrConnections: 8,
          resourceUtilizationPercent: 42.0,
          lastCheckedAt: 'Just now',
        },
        {
          serviceKey: 'SRV-POSTGRES',
          serviceName: 'PostgreSQL Primary (RLS Enforced)',
          status: 'HEALTHY',
          latencyMs: 4.8,
          uptimePercent: 99.99,
          activeWorkersOrConnections: 14,
          resourceUtilizationPercent: 36.5,
          lastCheckedAt: 'Just now',
        },
        {
          serviceKey: 'SRV-REDIS-QUEUE',
          serviceName: 'Redis Queue & Celery Worker Cluster',
          status: 'HEALTHY',
          latencyMs: 1.2,
          uptimePercent: 100.0,
          activeWorkersOrConnections: 4,
          resourceUtilizationPercent: 22.1,
          lastCheckedAt: 'Just now',
        },
        {
          serviceKey: 'SRV-ML-INFERENCE',
          serviceName: 'ML Inference & Stochastic Simulation Node',
          status: 'HEALTHY',
          latencyMs: 84.5,
          uptimePercent: 99.95,
          activeWorkersOrConnections: 2,
          resourceUtilizationPercent: 68.4,
          lastCheckedAt: 'Just now',
        },
      ],
    };
  }

  public static generateSimulatedUsers(): AdminUserRecord[] {
    return [
      {
        userId: 'USR-001',
        email: 'kaushik@aurix.ai',
        fullName: 'Kaushik Jain',
        role: 'SUPER_ADMIN',
        tenantId: 'ENTERPRISE_GLOBAL',
        status: 'ACTIVE',
        lastLoginAt: 'Today 10:14 AM IST',
        mfaEnabled: true,
      },
      {
        userId: 'USR-002',
        email: 'executive@aurix.ai',
        fullName: 'Executive Operator',
        role: 'EXECUTIVE',
        tenantId: 'ENTERPRISE_GLOBAL',
        status: 'ACTIVE',
        lastLoginAt: 'Today 09:30 AM IST',
        mfaEnabled: true,
      },
      {
        userId: 'USR-003',
        email: 'planner.blr@aurix.ai',
        fullName: 'Bengaluru SC Planner',
        role: 'PLANNER',
        tenantId: 'ENTERPRISE_GLOBAL',
        status: 'ACTIVE',
        lastLoginAt: 'Yesterday 04:20 PM IST',
        mfaEnabled: true,
      },
      {
        userId: 'USR-004',
        email: 'auditor.external@kpmg.com',
        fullName: 'Statutory SC Auditor',
        role: 'AUDITOR',
        tenantId: 'ENTERPRISE_GLOBAL',
        status: 'ACTIVE',
        lastLoginAt: '3 days ago',
        mfaEnabled: true,
      },
    ];
  }

  public static generateSimulatedAuditLogs(): SystemAuditLogEntry[] {
    return [
      {
        logId: 'AUD-9941',
        timestamp: '11:22 AM IST',
        actorEmail: 'kaushik@aurix.ai',
        actorRole: 'SUPER_ADMIN',
        actionCategory: 'ACTION_EXECUTION',
        eventSummary: 'Phase 14 preflight signoff executed for Action ACT-2026-101 (Air Expedite SKU-004).',
        ipAddress: '103.14.120.44',
        resultStatus: 'SUCCESS',
      },
      {
        logId: 'AUD-9940',
        timestamp: '10:00 AM IST',
        actorEmail: 'planner.blr@aurix.ai',
        actorRole: 'PLANNER',
        actionCategory: 'DATA_INGESTION',
        eventSummary: 'Committed schema mapping overrides for Inbound PO dataset upload (892 rows).',
        ipAddress: '103.14.120.44',
        resultStatus: 'SUCCESS',
      },
      {
        logId: 'AUD-9938',
        timestamp: '09:15 AM IST',
        actorEmail: 'executive@aurix.ai',
        actorRole: 'EXECUTIVE',
        actionCategory: 'SECURITY',
        eventSummary: 'Authenticated via Session Token against tenant ENTERPRISE_GLOBAL.',
        ipAddress: '103.14.120.44',
        resultStatus: 'SUCCESS',
      },
    ];
  }
}