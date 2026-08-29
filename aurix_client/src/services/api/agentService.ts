import { ApiClient } from '@/services/api/apiClient';
import { AgentDefinitionDTO, AgentSummaryDTO, SkillDefinitionDTO, StudioAgentDTO, StudioTemplateDTO, ValidationResultDTO } from '@/types/agent.types';

export class AgentService {
  // Phase 29 Core APIs
  public static async getSummary(periodKey: string = 'CURRENT'): Promise<AgentSummaryDTO> {
    return ApiClient.get<AgentSummaryDTO>(
      `/agents/summary?period=${encodeURIComponent(periodKey)}`,
      () => ({
        tenantId: 'GLOBAL',
        periodKey: periodKey,
        registeredAgentsCount: 4,
        activeAgentsCount: 3,
        totalExecutionsCount: 42,
        successRatePct: 97.6,
        pendingApprovalsCount: 2,
        deadLetterCount: 0,
        totalRealizedValueUsd: 84500.0,
        evaluatedAt: new Date().toISOString(),
      })
    );
  }

    public static async fetchAgentActivity(): Promise<any> {
    return ApiClient.get<any>('/agents/activity', () => ({
      timestamp: new Date().toISOString(),
      totalActiveAgents: 4,
      recentTasks: [],
      metrics: { totalAgents: 4, activeAgents: 4, successRatePct: 97.6 }
    }));
  }

  public static async listAgents(): Promise<AgentDefinitionDTO[]> {
    return ApiClient.get<AgentDefinitionDTO[]>('/agents', () => [
      {
        agentId: 'AGT-FIN-01',
        tenantId: 'GLOBAL',
        agentType: 'FINANCE_AGENT',
        name: 'Working Capital & Finance Agent',
        version: 'v1.0',
        status: 'ACTIVE',
        owner: 'CFO_OFFICE',
        capabilities: ['analyze_invoice', 'propose_payment_hold'],
        riskClassification: 'MEDIUM',
        allowedTools: ['ERP_INVOICE_API'],
        maxStepsPerExecution: 8,
        createdAt: new Date().toISOString(),
      },
    ]);
  }

  public static async listSkills(): Promise<SkillDefinitionDTO[]> {
    return ApiClient.get<SkillDefinitionDTO[]>('/agents/skills', () => [
      {
        skillId: 'SKL-INV-01',
        name: 'analyze_invoice',
        version: '1.0.0',
        description: 'Inspect billing records for 3-way match exceptions.',
        riskLevel: 'LOW',
        requiresApproval: false,
        sideEffect: 'REVERSIBLE',
      },
    ]);
  }

  // Phase 30 Agent Studio APIs
  public static async getStudioSummary(): Promise<AgentSummaryDTO> {
    return ApiClient.get<AgentSummaryDTO>('/agent-studio/summary', () => ({
      tenantId: 'GLOBAL',
      periodKey: 'CURRENT',
      registeredAgentsCount: 3,
      activeAgentsCount: 2,
      totalExecutionsCount: 28,
      successRatePct: 96.4,
      pendingApprovalsCount: 1,
      deadLetterCount: 0,
      totalRealizedValueUsd: 64200.0,
      evaluatedAt: new Date().toISOString(),
    }));
  }

  public static async listStudioAgents(): Promise<StudioAgentDTO[]> {
    return ApiClient.get<StudioAgentDTO[]>('/agent-studio/agents', () => [
      {
        agentId: 'ST-AGT-PROC-01',
        tenantId: 'GLOBAL',
        name: 'Procurement Reallocation Agent',
        businessPurpose: 'Autonomous purchase order splitting on supplier disruption.',
        domain: 'SUPPLY_CHAIN',
        owner: 'PROCUREMENT_LEAD',
        agentType: 'PROCUREMENT_AGENT',
        version: '1.0.0',
        status: 'DEPLOYED',
        allowedSkills: ['propose_po_split'],
        allowedTools: ['ERP_PO_API'],
        allowedContextDomains: ['SUPPLIERS', 'PURCHASE_ORDERS'],
        riskClassification: 'HIGH',
        maxStepsPerExecution: 10,
        budgetLimitUsd: 50000.0,
        createdAt: new Date().toISOString(),
      },
    ]);
  }

  public static async validateAgent(draft: StudioAgentDTO): Promise<ValidationResultDTO> {
    return ApiClient.post<any, any>('/agent-studio/validate', draft, () => ({
      isValid: true,
      totalErrors: 0,
      totalWarnings: 0,
      issues: [],
      blastRadiusSummary: { riskTier: draft.riskClassification, maxExposureUsd: draft.budgetLimitUsd },
    }));
  }

  public static async publishAgent(agentId: string, publishedBy: string, changeSummary: string): Promise<any> {
    return ApiClient.post(`/agent-studio/agents/${agentId}/publish`, { publishedBy, changeSummary }, () => ({
      versionNumber: '1.0.0',
      status: 'PUBLISHED',
    }));
  }

  public static async listTemplates(): Promise<StudioTemplateDTO[]> {
    return ApiClient.get<StudioTemplateDTO[]>('/agent-studio/templates', () => [
      {
        templateId: 'TPL-COLL-01',
        templateType: 'AGENT',
        name: 'AR Collections & Aging Review Agent',
        category: 'FINANCE',
        description: 'Inspects 60+ day overdue customer invoices and prepares governed reminder actions.',
        suggestedRisk: 'MEDIUM',
        definitionJson: {},
      },
    ]);
  }
}
