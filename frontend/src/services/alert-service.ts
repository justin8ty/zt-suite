import { apiClient } from '@/services/api-client'
import type { AlertCreate, AlertUpdate, SecurityAlert } from '@/types/alert'

export const alertService = {
  async create(payload: AlertCreate): Promise<SecurityAlert> {
    const response = await apiClient.post<SecurityAlert>('/api/alerts', payload)
    return response.data
  },

  async list(params?: {
    skip?: number
    limit?: number
    severity?: string
    is_acknowledged?: boolean
  }): Promise<SecurityAlert[]> {
    const response = await apiClient.get<SecurityAlert[]>('/api/alerts', { params })
    return response.data
  },

  async acknowledge(alertId: number, payload: AlertUpdate = { is_acknowledged: true }): Promise<SecurityAlert> {
    const response = await apiClient.patch<SecurityAlert>(`/api/alerts/${alertId}`, payload)
    return response.data
  },
}
