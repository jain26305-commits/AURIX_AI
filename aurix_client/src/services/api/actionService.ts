import { ApiClient } from '@/services/api/apiClient';
import { ActionCenterFeedReport, Phase14ActionItem } from '@/types/action.types';

const INITIAL_MOCK_ACTIONS: Phase14ActionItem[] = [
  {
    id: 'ACT-2026-101',
    title: 'Expedite PO-8821 Air Freight Delivery (Apex Mills)',
    domain: 'INVENTORY',
    priority: 'CRITICAL',
    state: 'AWAITING_APPROVAL',
    targetEntityId: 'SKU-004',
    targetEntityName: 'Dotknit White S',
    prescriptivePayload: {
      actionType: 'EXPEDITE_AIR_FREIGHT',
      quantity: 500,
      destination: 'BLR_CENTRAL_DC',
      carrier: 'GATI_AIR_EXPRESS',
      financialCommitmentINR: 24500,
      expectedRoiINR: 340000,
    },
    initiatedBy: 'Autonomous Stockout Sentinel',
    assignedApproverRole: 'SUPER_ADMIN',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    preflightCleared: true,
    preflightChecks: [
      {
        checkId: 'CHK-01',
        name: 'Supplier Capacity Verification',
        category: 'ERP_CONNECTIVITY',
        passed: true,
        message: 'Apex Mills confirmed 48h ready-to-ship lot readiness.',
        timestamp: new Date().toISOString(),
      },
      {
        checkId: 'CHK-02',
        name: 'Contingency Budget Authority',
        category: 'BUDGET_CAPITAL',
        passed: true,
        message: 'Within authorized ₹50,000 contingency reserve threshold.',
        timestamp: new Date().toISOString(),
      },
      {
        checkId: 'CHK-03',
        name: 'Receiving Dock Slotting',
        category: 'BUSINESS_CONSTRAINT',
        passed: true,
        message: 'Bengaluru warehouse intake slot reserved for delivery window.',
        timestamp: new Date().toISOString(),
      },
    ],
    executionToken: {
      tokenId: 'TKN-SHA256-88192-A',
      signedBy: 'Kaushik Jain (Super Admin)',
      role: 'SUPER_ADMIN',
      timestamp: new Date().toISOString(),
      sha256Checksum: '0x9b7a4c8e1f52d9a34e78b12c56df90a12e34bc78',
      phase14AuthorizationCode: 'PH14-AUTH-99014',
    },
    auditTrail: [
      {
        timestamp: new Date().toISOString(),
        state: 'PREFLIGHT',
        actor: 'Preflight Gatekeeper',
        note: 'All static constraints and budget allowances cleared.',
      },
      {
        timestamp: new Date().toISOString(),
        state: 'AWAITING_APPROVAL',
        actor: 'Autonomous Dispatch Router',
        note: 'Submitted to Super Admin approval queue.',
      },
    ],
  },
  {
    id: 'ACT-2026-102',
    title: 'Split Inbound Fabric Batch Across Secondary Mill',
    domain: 'PROCUREMENT',
    priority: 'HIGH',
    state: 'APPROVED',
    targetEntityId: 'SUP-002',
    targetEntityName: 'Vardhman Poly-Cotton Ltd',
    prescriptivePayload: {
      actionType: 'SPLIT_ORDER_REBALANCING',
      quantity: 1200,
      destination: 'BLR_MILL_NORTH',
      carrier: 'VARDHMAN_DIRECT',
      financialCommitmentINR: 12000,
      expectedRoiINR: 185000,
    },
    initiatedBy: 'Supplier Telematics Anomaly Engine',
    assignedApproverRole: 'SUPER_ADMIN',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    preflightCleared: true,
    preflightChecks: [
      {
        checkId: 'CHK-04',
        name: 'Fabric GSM Spec Verification',
        category: 'BUSINESS_CONSTRAINT',
        passed: true,
        message: '180 GSM single jersey compliance laboratory verified.',
        timestamp: new Date().toISOString(),
      },
      {
        checkId: 'CHK-05',
        name: 'Contract Price Parity Guardrail',
        category: 'BUDGET_CAPITAL',
        passed: true,
        message: 'Secondary vendor accepted baseline contract unit rates.',
        timestamp: new Date().toISOString(),
      },
    ],
    executionToken: {
      tokenId: 'TKN-SHA256-44019-B',
      signedBy: 'Kaushik Jain (Super Admin)',
      role: 'SUPER_ADMIN',
      timestamp: new Date().toISOString(),
      sha256Checksum: '0x3c2a1b9e8f74d6c5b4a32e10f98dc76ba54ef321',
      phase14AuthorizationCode: 'PH14-AUTH-99015',
    },
    auditTrail: [
      {
        timestamp: new Date().toISOString(),
        state: 'APPROVED',
        actor: 'Kaushik Jain (Super Admin)',
        note: 'Approved for ERP execution batch dispatch.',
      },
    ],
  },
];

export class ActionService {
  public static async fetchActionFeed(): Promise<ActionCenterFeedReport> {
    return ApiClient.get<ActionCenterFeedReport>('/actions', () => ({
      evaluatedAt: new Date().toISOString(),
      summary: {
        totalPendingCount: 4,
        awaitingApprovalCount: 1,
        executingCount: 0,
        executedTodayCount: 6,
        failedCount: 0,
        totalCommittedCapitalINR: 148500,
        totalProtectedExposureINR: 780000,
      },
      actions: INITIAL_MOCK_ACTIONS,
    }));
  }

  public static async approveAction(actionId: string): Promise<Phase14ActionItem> {
    return ApiClient.post<{ actionId: string; decision: string }, Phase14ActionItem>(
      `/actions/${actionId}/approve`,
      { actionId, decision: 'APPROVED' },
      () => {
        const existing = INITIAL_MOCK_ACTIONS.find((a) => a.id === actionId) || INITIAL_MOCK_ACTIONS[0];
        return {
          ...existing,
          state: 'APPROVED',
          updatedAt: new Date().toISOString(),
          auditTrail: [
            ...existing.auditTrail,
            {
              timestamp: new Date().toISOString(),
              state: 'APPROVED',
              actor: 'Operator (Authenticated Session)',
              note: 'Manually cleared via Phase 14 Execution Gate.',
            },
          ],
        };
      }
    );
  }

  public static async executeAction(actionId: string): Promise<Phase14ActionItem> {
    return ApiClient.post<{ actionId: string; execute: boolean }, Phase14ActionItem>(
      `/actions/${actionId}/execute`,
      { actionId, execute: true },
      () => {
        const existing = INITIAL_MOCK_ACTIONS.find((a) => a.id === actionId) || INITIAL_MOCK_ACTIONS[0];
        return {
          ...existing,
          state: 'EXECUTED',
          updatedAt: new Date().toISOString(),
          auditTrail: [
            ...existing.auditTrail,
            {
              timestamp: new Date().toISOString(),
              state: 'EXECUTED',
              actor: 'AURIX Dispatch Engine',
              note: 'Cryptographic execution token broadcasted to ERP connectors.',
            },
          ],
        };
      }
    );
  }

  public static async rejectAction(actionId: string, reason?: string): Promise<boolean> {
    return ApiClient.post<{ actionId: string; decision: string; reason?: string }, boolean>(
      `/actions/${actionId}/reject`,
      { actionId, decision: 'REJECTED', reason },
      () => true
    );
  }
}