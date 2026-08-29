import { ApiClient } from '@/services/api/apiClient';
import { AssuranceFindingDTO, AssuranceMetricsDTO } from '@/types/assurance.types';

export class AssuranceService {
  public static async getFindings(
    domain?: string,
    severity?: string
  ): Promise<AssuranceFindingDTO[]> {
    const queryParts: string[] = [];
    if (domain) queryParts.push(`domain=${encodeURIComponent(domain)}`);
    if (severity) queryParts.push(`severity=${encodeURIComponent(severity)}`);
    const query = queryParts.length > 0 ? `?${queryParts.join('&')}` : '';

    return ApiClient.get<AssuranceFindingDTO[]>(`/assurance/findings${query}`, () => [
      {
        finding_id: 'FND-MOCK-001',
        tenant_id: 'GLOBAL',
        domain: 'THREE_WAY_MATCH',
        severity: 'HIGH',
        status: 'OPEN',
        title: 'Price Mismatch on Invoice INV-9901',
        description: 'Billed $60.00/unit vs contracted PO price of $50.00/unit.',
        financial_exposure: 1000.0,
        currency: 'USD',
        entity_type: 'invoice',
        entity_id: 'INV-9901',
        evidence_data: { po_price: 50.0, inv_price: 60.0 },
        recommended_action: 'Hold invoice payment pending vendor credit memo.',
        detected_at: new Date().toISOString(),
      },
      {
        finding_id: 'FND-MOCK-002',
        tenant_id: 'GLOBAL',
        domain: 'UNBILLED_SHIPMENT',
        severity: 'CRITICAL',
        status: 'OPEN',
        title: 'Unbilled Shipment: SHIP-4471',
        description: 'Goods dispatched and confirmed delivered 14 days ago with no corresponding invoice raised.',
        financial_exposure: 24800.0,
        currency: 'USD',
        entity_type: 'shipment',
        entity_id: 'SHIP-4471',
        evidence_data: { dispatch_date: '14 days ago', invoice_status: 'NOT_RAISED' },
        recommended_action: 'Escalate to billing team for immediate invoice generation.',
        detected_at: new Date().toISOString(),
      },
      {
        finding_id: 'FND-MOCK-003',
        tenant_id: 'GLOBAL',
        domain: 'DOUBLE_PAYMENT',
        severity: 'HIGH',
        status: 'REMEDIATED',
        title: 'Duplicate Payment Detected: PAY-7723 / PAY-7724',
        description: 'Two payments issued against the same invoice number within a 48-hour window.',
        financial_exposure: 18400.0,
        currency: 'USD',
        entity_type: 'payment',
        entity_id: 'PAY-7724',
        evidence_data: { original_payment: 'PAY-7723', duplicate_payment: 'PAY-7724' },
        recommended_action: 'Vendor credit memo issued and applied against next invoice cycle.',
        detected_at: new Date().toISOString(),
      },
      {
        finding_id: 'FND-MOCK-004',
        tenant_id: 'GLOBAL',
        domain: 'PRICE_VARIANCE',
        severity: 'MEDIUM',
        status: 'OPEN',
        title: 'Purchase Price Variance Clawback: RAW-FAB-001',
        description: 'Received unit price exceeded standard cost baseline by 8.4% across last 3 purchase orders.',
        financial_exposure: 4000.0,
        currency: 'USD',
        entity_type: 'material',
        entity_id: 'RAW-FAB-001',
        evidence_data: { standard_cost: 420.0, actual_avg_cost: 455.3 },
        recommended_action: 'Renegotiate rate card with Apex Mills & Fabrics for next quarter.',
        detected_at: new Date().toISOString(),
      },
    ]);
  }

  public static async getMetrics(): Promise<AssuranceMetricsDTO> {
    return ApiClient.get<AssuranceMetricsDTO>('/assurance/metrics', () => ({
      tenant_id: 'GLOBAL',
      total_findings_count: 1,
      total_financial_leakage: 1000.0,
      critical_severity_count: 0,
      high_severity_count: 1,
      leakage_by_domain: { THREE_WAY_MATCH: 1000.0 },
      findings_count_by_domain: { THREE_WAY_MATCH: 1 },
    }));
  }
}
