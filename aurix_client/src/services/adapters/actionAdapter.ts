import { ActionCenterFeedReport, Phase14ActionItem } from '@/types/action.types';

export class ActionAdapter {
  public static generateSimulatedActions(): ActionCenterFeedReport {
    const actions: Phase14ActionItem[] = [
      {
        id: 'ACT-2026-101',
        title: 'Expedite Air Freight Dispatch for SKU-004',
        domain: 'LOGISTICS',
        priority: 'CRITICAL',
        state: 'AWAITING_APPROVAL',
        targetEntityId: 'SKU-004',
        targetEntityName: '103 Black-XXL (Hoodie)',
        prescriptivePayload: {
          actionType: 'AIR_FREIGHT_EXPEDITE',
          quantity: 300,
          destination: 'Bengaluru Fulfillment Center',
          carrier: 'BlueDart Express Air',
          financialCommitmentINR: 42000,
          expectedRoiINR: 158700,
        },
        initiatedBy: 'AURIX AI Decision Engine',
        assignedApproverRole: 'EXECUTIVE',
        createdAt: new Date(Date.now() - 1000 * 60 * 40).toISOString(),
        updatedAt: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
        preflightCleared: true,
        preflightChecks: [
          {
            checkId: 'CHK-01',
            name: 'Role-Based Approval Authority',
            category: 'SECURITY_RBAC',
            passed: true,
            message: 'User holds required EXECUTIVE authorization for commitments > ₹25,000.',
            timestamp: '11:20 AM IST',
          },
          {
            checkId: 'CHK-02',
            name: 'Working Capital Allocation Clearance',
            category: 'BUDGET_CAPITAL',
            passed: true,
            message: 'Operational logistics buffer ₹1.50L available.',
            timestamp: '11:20 AM IST',
          },
          {
            checkId: 'CHK-03',
            name: 'Carrier EDI Transit Slot Reservation',
            category: 'ERP_CONNECTIVITY',
            passed: true,
            message: 'Air Cargo flight 6E-842 confirmed capacity for 300 units.',
            timestamp: '11:21 AM IST',
          },
          {
            checkId: 'CHK-04',
            name: 'Warehouse Inbound Bay Capacity Check',
            category: 'BUSINESS_CONSTRAINT',
            passed: true,
            message: 'Receiving Dock 04 scheduled for receipt within 24hr ETA window.',
            timestamp: '11:21 AM IST',
          },
        ],
        auditTrail: [
          {
            timestamp: '11:15 AM IST',
            state: 'PENDING',
            actor: 'AURIX Prescriptive Advisor',
            note: 'Action synthesized in response to Case CASE-2026-084.',
          },
          {
            timestamp: '11:21 AM IST',
            state: 'PREFLIGHT',
            actor: 'Phase 14 Preflight Engine',
            note: 'All 4 deterministic gate criteria cleared successfully.',
          },
          {
            timestamp: '11:22 AM IST',
            state: 'AWAITING_APPROVAL',
            actor: 'Governance Router',
            note: 'Queued for human signoff.',
          },
        ],
      },
      {
        id: 'ACT-2026-098',
        title: 'Procurement Order PO-2026-095 Split Allocation',
        domain: 'PROCUREMENT',
        priority: 'HIGH',
        state: 'APPROVED',
        targetEntityId: 'SKU-001',
        targetEntityName: '101 Beige-L (T-Shirt)',
        prescriptivePayload: {
          actionType: 'SPLIT_PO_ALLOCATION',
          quantity: 1200,
          destination: 'Apex Mills (60%) + DenimCraft (40%)',
          financialCommitmentINR: 12000,
          expectedRoiINR: 84000,
        },
        initiatedBy: 'Supply Chain Operations',
        assignedApproverRole: 'PLANNER',
        createdAt: new Date(Date.now() - 1000 * 60 * 180).toISOString(),
        updatedAt: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
        preflightCleared: true,
        preflightChecks: [
          {
            checkId: 'CHK-01',
            name: 'Supplier Contract Unit Rate Check',
            category: 'BUDGET_CAPITAL',
            passed: true,
            message: 'Secondary vendor premium verified at +₹8/unit.',
            timestamp: '09:30 AM IST',
          },
          {
            checkId: 'CHK-02',
            name: 'Secondary Vendor OTIF Rating Validation',
            category: 'BUSINESS_CONSTRAINT',
            passed: true,
            message: 'DenimCraft historical OTIF is 86.5% (> 80% cutoff).',
            timestamp: '09:31 AM IST',
          },
        ],
        executionToken: {
          tokenId: 'TKN-PH14-88492',
          signedBy: 'Kaushik Jain',
          role: 'EXECUTIVE',
          timestamp: '10:00 AM IST',
          sha256Checksum: 'sha256:4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a',
          phase14AuthorizationCode: 'AUTH-P14-2026-EXEC-098',
        },
        auditTrail: [
          {
            timestamp: '09:15 AM IST',
            state: 'PENDING',
            actor: 'Supply Chain Planner',
            note: 'Action queued to mitigate Apex Mill capacity bottleneck.',
          },
          {
            timestamp: '10:00 AM IST',
            state: 'APPROVED',
            actor: 'Kaushik Jain (Executive)',
            note: 'Approved with execution token TKN-PH14-88492.',
          },
        ],
      },
      {
        id: 'ACT-2026-092',
        title: 'Automated 15% Digital Markdown on SKU-005',
        domain: 'PRICING',
        priority: 'MEDIUM',
        state: 'EXECUTED',
        targetEntityId: 'SKU-005',
        targetEntityName: '104 Olive-M (Jeans)',
        prescriptivePayload: {
          actionType: 'PRICE_MARKDOWN_DISPATCH',
          quantity: 178,
          financialCommitmentINR: 18500,
          expectedRoiINR: 213600,
        },
        initiatedBy: 'Working Capital Optimizer',
        assignedApproverRole: 'EXECUTIVE',
        createdAt: new Date(Date.now() - 1000 * 60 * 1440).toISOString(),
        updatedAt: new Date(Date.now() - 1000 * 60 * 600).toISOString(),
        preflightCleared: true,
        preflightChecks: [
          {
            checkId: 'CHK-01',
            name: 'Price Floor Margin Compliance',
            category: 'BUSINESS_CONSTRAINT',
            passed: true,
            message: 'Net margin remains > 24% after 15% markdown.',
            timestamp: 'Yesterday 02:00 PM IST',
          },
        ],
        executionToken: {
          tokenId: 'TKN-PH14-88104',
          signedBy: 'Kaushik Jain',
          role: 'EXECUTIVE',
          timestamp: 'Yesterday 02:30 PM IST',
          sha256Checksum: 'sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
          phase14AuthorizationCode: 'AUTH-P14-2026-EXEC-092',
        },
        auditTrail: [
          {
            timestamp: 'Yesterday 02:30 PM IST',
            state: 'EXECUTED',
            actor: 'Shopify / ERP Connector',
            note: 'Updated MSRP pushed to omnichannel sales channels.',
          },
        ],
      },
    ];

    const totalCommitted = actions.reduce((acc, a) => acc + a.prescriptivePayload.financialCommitmentINR, 0);
    const totalProtected = actions.reduce((acc, a) => acc + a.prescriptivePayload.expectedRoiINR, 0);

    return {
      evaluatedAt: new Date().toISOString(),
      summary: {
        totalPendingCount: actions.filter((a) => a.state === 'PENDING').length,
        awaitingApprovalCount: actions.filter((a) => a.state === 'AWAITING_APPROVAL').length,
        executingCount: actions.filter((a) => a.state === 'EXECUTING').length,
        executedTodayCount: actions.filter((a) => a.state === 'EXECUTED').length,
        failedCount: actions.filter((a) => a.state === 'FAILED').length,
        totalCommittedCapitalINR: totalCommitted,
        totalProtectedExposureINR: totalProtected,
      },
      actions,
    };
  }
}