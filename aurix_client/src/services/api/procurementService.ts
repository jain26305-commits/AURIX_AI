import { ApiClient } from '@/services/api/apiClient';
import { ProcurementReport, PurchaseOrder } from '@/types/procurement.types';
import { ProcurementAdapter } from '@/services/adapters/procurementAdapter';

export class ProcurementService {
  public static async fetchProcurementReport(): Promise<ProcurementReport> {
    return ApiClient.get<ProcurementReport>(
      '/procurement/summary',
      () => ProcurementAdapter.generateSimulatedProcurement()
    );
  }

  public static async createPurchaseOrder(poPayload: Partial<PurchaseOrder>): Promise<PurchaseOrder> {
    return ApiClient.post<Partial<PurchaseOrder>, PurchaseOrder>(
      '/procurement/orders',
      poPayload,
      (body) => ({
        poNumber: `PO-2025-${Math.floor(100 + Math.random() * 900)}`,
        vendorId: body.vendorId || 'VEND-001',
        vendorName: body.vendorName || 'Apex Mills & Fabrics Pvt Ltd',
        status: 'DRAFT',
        orderDate: new Date().toISOString().split('T')[0],
        promisedDeliveryDate: body.promisedDeliveryDate || new Date(Date.now() + 1000 * 60 * 60 * 24 * 21).toISOString().split('T')[0],
        totalAmountINR: body.totalAmountINR || 150000,
        currency: 'INR',
        paymentTerms: 'Net 45 Days',
        lineItems: body.lineItems || [],
      })
    );
  }
}