import { ApiClient } from '@/services/api/apiClient';
import { ActionCenterFeedReport, Phase14ActionItem } from '@/types/action.types';

export class ActionService {
  public static async fetchActionFeed(): Promise<ActionCenterFeedReport> {
    return ApiClient.get<ActionCenterFeedReport>('/actions');
  }

  public static async approveAction(actionId: string): Promise<Phase14ActionItem> {
    return ApiClient.post<{ actionId: string; decision: string }, Phase14ActionItem>(
      `/actions/${actionId}/approve`,
      { actionId, decision: 'APPROVED' }
    );
  }

  public static async executeAction(actionId: string): Promise<Phase14ActionItem> {
    return ApiClient.post<{ actionId: string; execute: boolean }, Phase14ActionItem>(
      `/actions/${actionId}/execute`,
      { actionId, execute: true }
    );
  }

  public static async rejectAction(actionId: string, reason?: string): Promise<boolean> {
    const res = await ApiClient.post<{ actionId: string; decision: string; reason?: string }, { status: string }>(
      `/actions/${actionId}/reject`,
      { actionId, decision: 'REJECTED', reason }
    );
    return res.status === 'SUCCESS';
  }
}