import { apiClient } from '@/services/api-client'
import type { TrafficBatchCreate, TrafficRecord } from '@/types/traffic'

export const trafficService = {
  async ingestBatch(payload: TrafficBatchCreate): Promise<{ inserted: number }> {
    const response = await apiClient.post<{ inserted: number }>('/api/traffic', payload)
    return response.data
  },

  async list(params?: { skip?: number; limit?: number; device_id?: number }): Promise<TrafficRecord[]> {
    const response = await apiClient.get<TrafficRecord[]>('/api/traffic', { params })
    return response.data
  },
}
