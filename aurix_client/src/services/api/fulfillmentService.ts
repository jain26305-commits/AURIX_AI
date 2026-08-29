import { ApiClient } from '@/services/api/apiClient';
import {
  AtpInquiryRequest,
  AtpInquiryResponse,
  FulfillmentReport,
} from '@/types/fulfillment.types';
import { FulfillmentAdapter } from '@/services/adapters/fulfillmentAdapter';

export class FulfillmentService {
  public static async fetchFulfillmentReport(): Promise<FulfillmentReport> {
    return ApiClient.get<FulfillmentReport>(
      '/fulfillment/orders',
      () => FulfillmentAdapter.generateSimulatedFulfillment()
    );
  }

  public static async checkAtp(req: AtpInquiryRequest): Promise<AtpInquiryResponse> {
    return ApiClient.post<AtpInquiryRequest, AtpInquiryResponse>(
      '/fulfillment/atp-check',
      req,
      (body) => {
        const isHoodie = body.skuId === 'SKU-004';
        const onHand = isHoodie ? 42 : 327;
        const allocated = isHoodie ? 42 : 250;
        const unallocated = Math.max(0, onHand - allocated);
        const canFulfill = unallocated >= body.requestedUnits;

        return {
          skuId: body.skuId,
          skuName: isHoodie ? '103 Black-XXL (Hoodie)' : '101 Beige-L (T-Shirt)',
          requestedUnits: body.requestedUnits,
          availableToPromiseUnits: unallocated,
          capableToPromiseUnits: unallocated + (isHoodie ? 150 : 250),
          onHandStockUnits: onHand,
          allocatedStockUnits: allocated,
          plannedReceiptsUnits: isHoodie ? 150 : 250,
          canFulfillImmediately: canFulfill,
          promisedDeliveryDate: canFulfill
            ? body.targetDate
            : new Date(Date.now() + 1000 * 60 * 60 * 24 * (isHoodie ? 18 : 7)).toISOString().split('T')[0],
          leadTimeDaysRequired: canFulfill ? 1 : isHoodie ? 18 : 7,
          constrainingFactor: canFulfill
            ? undefined
            : isHoodie
            ? 'Inbound PO-2025-084 transit delay (+2.5d) and high allocated customer reservations.'
            : 'Standard manufacturing release cycle time.',
        };
      }
    );
  }
}