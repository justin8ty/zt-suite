import { apiClient } from '@/services/api-client'
import type { NetworkFlow } from '@/types/flow'

export const flowService = {
  async list(params?: {
    skip?: number
    limit?: number
    device_id?: number
    prediction?: number
  }): Promise<NetworkFlow[]> {
    const response = await apiClient.get<NetworkFlow[]>('/api/flows', { params })
    return response.data
  },
}
