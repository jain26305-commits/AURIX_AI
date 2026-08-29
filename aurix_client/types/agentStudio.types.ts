export type AgentStatus = 'IDLE' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'PAUSED' | 'ACTIVE' | 'PENDING_APPROVAL' | string;

export interface AgentSummaryMetrics {
  totalAgents?: number;
  activeAgents?: number;
  idleAgents?: number;
  pausedAgents?: number;
  runningTasks?: number;
  completedTasks?: number;
  failedTasks?: number;
  pendingApprovals?: number;
  successRatePct?: number;
  avgResponseTimeMs?: number;
  realizedValueUsd?: number;
  [key: string]: any;
}

export interface AgentSummaryDTO extends AgentSummaryMetrics {}

export interface AgentTask {
  id?: string;
  taskId?: string;
  title?: string;
  name?: string;
  description?: string;
  status?: AgentStatus;
  agentId?: string;
  agentName?: string;
  timestamp?: string;
  createdAt?: string;
  completedAt?: string;
  executionTimeMs?: number;
  toolsUsed?: any[];
  inputData?: Record<string, any>;
  outputData?: Record<string, any>;
  error?: string;
  [key: string]: any;
}

export interface AgentActivityReport {
  timestamp?: string;
  totalActiveAgents?: number;
  recentTasks?: AgentTask[];
  tasks?: AgentTask[];
  summary?: Record<string, any>;
  metrics?: AgentSummaryMetrics;
  evaluatedAt?: string;
  [key: string]: any;
}

export interface AgentExecution {
  executionId?: string;
  id?: string;
  agentId?: string;
  agentName?: string;
  action?: string;
  status?: AgentStatus;
  startedAt?: string;
  completedAt?: string;
  durationMs?: number;
  valueUsd?: number;
  riskTier?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  [key: string]: any;
}

export interface ExecutionJournalRecordDTO extends AgentExecution {}

export interface AgentApproval {
  approvalId?: string;
  id?: string;
  agentId?: string;
  agentName?: string;
  actionRequested?: string;
  financialImpactUsd?: number;
  riskTier?: string;
  status?: 'PENDING' | 'APPROVED' | 'REJECTED' | string;
  requestedAt?: string;
  [key: string]: any;
}

export interface ApprovalRequestDTO extends AgentApproval {}

export interface AgentSkill {
  skillId?: string;
  id?: string;
  name?: string;
  description?: string;
  category?: string;
  version?: string;
  isEnabled?: boolean;
  [key: string]: any;
}

export interface SkillDefinitionDTO extends AgentSkill {}

export interface AgentTool {
  toolId?: string;
  id?: string;
  name?: string;
  description?: string;
  parametersSchema?: Record<string, any>;
  rateLimitPerMinute?: number;
  [key: string]: any;
}

export interface AgentDefinitionDTO {
  agentId?: string;
  id?: string;
  name?: string;
  description?: string;
  domain?: string;
  version?: string;
  status?: AgentStatus;
  autonomyLevel?: string;
  skills?: string[];
  tools?: string[];
  [key: string]: any;
}

export interface Agent {
  id?: string;
  agentId?: string;
  name?: string;
  domain?: string;
  status?: AgentStatus;
  successRatePct?: number;
  totalExecutions?: number;
  autonomyLevel?: 'SUPERVISED' | 'SEMI_AUTONOMOUS' | 'FULLY_AUTONOMOUS' | string;
  skills?: string[] | AgentSkill[];
  tools?: string[] | AgentTool[];
  lastActive?: string;
  [key: string]: any;
}

export interface DeploymentRecordDTO {
  deploymentId?: string;
  agentId?: string;
  version?: string;
  environment?: string;
  status?: string;
  deployedAt?: string;
  [key: string]: any;
}

export interface StudioAgentDTO {
  id?: string;
  agentId?: string;
  name?: string;
  description?: string;
  domain?: string;
  version?: string;
  status?: string;
  workflowId?: string;
  config?: Record<string, any>;
  createdAt?: string;
  updatedAt?: string;
  [key: string]: any;
}

export interface StudioTemplateDTO {
  templateId?: string;
  id?: string;
  name?: string;
  category?: string;
  description?: string;
  tags?: string[];
  workflowGraph?: Record<string, any>;
  [key: string]: any;
}

export interface StudioWorkflowDTO {
  workflowId?: string;
  id?: string;
  name?: string;
  nodes?: any[];
  edges?: any[];
  [key: string]: any;
}

export interface ValidationResultDTO {
  isValid?: boolean;
  valid?: boolean;
  errors?: string[];
  warnings?: string[];
  issues?: Array<{ message?: string; severity?: string; [key: string]: any }>;
  hasCycle?: boolean;
  isolatedNodes?: string[];
  missingSecrets?: string[];
  totalErrors?: number;
  totalWarnings?: number;
  blastRadiusSummary?: Record<string, any>;
  [key: string]: any;
}

export interface WorkflowNodeDTO {
  id: string;
  label?: string;
  type?: string;
  stepType?: string;
  config?: Record<string, any>;
  position?: { x: number; y: number };
  [key: string]: any;
}
