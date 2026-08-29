export interface AiQueryRequest {
  query?: string;
  prompt?: string;
  entity_id?: string;
  conversation_id?: string;
  page_context?: {
    current_page?: string;
    domain?: string;
    subdomain?: string;
    entity_type?: string;
    entity_id?: string;
    [key: string]: unknown;
  };
  analytical_data?: Record<string, unknown>;
}

export interface AiQueryResponse {
  response_id: string;
  response_type: string;
  headline: string;
  response?: string | null;
  summary?: string;
  narrative?: string;
  verified_facts: string[];
  explanation: string;
  recommendations: string[];
  citations: string[];
  financial_impact: Record<string, unknown>;
  operational_impact: Record<string, unknown>;
  data_limitations: string[];
  source: string;
  evidence_quality: string;
  freshness: string;
  provider_used: string;
  answer_source: string;
  model_used: string;
  is_fallback: boolean;
  confidence_score: number;
  token_usage: Record<string, number>;
  suggested_actions: Record<string, unknown>[];
  provenance: Record<string, unknown>;
}

export interface ApiResponse<T> {
  status: string;
  request_id: string;
  data: T | null;
  meta: {
    tenant_id?: string;
    [key: string]: unknown;
  } | null;
}
