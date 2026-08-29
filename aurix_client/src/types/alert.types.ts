export type AlertSeverity = 'CRITICAL' | 'WARNING' | 'INFO';
export type AlertStatus = 'ACTIVE' | 'ACKNOWLEDGED' | 'SNOOZED' | 'ESCALATED' | 'DISMISSED';
export type AlertDomain = 'INVENTORY' | 'SUPPLY' | 'LOGISTICS' | 'NETWORK' | 'QUALITY' | 'FORECAST';

export interface OperationalAlert {
  id: string;
  title: string;
  domain: AlertDomain;
  severity: AlertSeverity;
  status: AlertStatus;
  entityId: string;
  entityName: string;
  summary: string;
  exposureINR: number;
  breachWindow: string;
  detectedAt: string;
  acknowledgedBy?: string;
  linkedCaseId?: string;
  provenance: {
    ruleOrModel: string;
    thresholdTriggered: string;
    actualValue: string;
  };
}

export interface AlertFeedSummary {
  totalActive: number;
  criticalCount: number;
  warningCount: number;
  infoCount: number;
  totalFinancialExposureINR: number;
  unacknowledgedCount: number;
}

export interface AlertFeedReport {
  evaluatedAt: string;
  summary: AlertFeedSummary;
  alerts: OperationalAlert[];
}