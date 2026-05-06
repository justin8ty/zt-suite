import { apiClient } from '@/services/api-client'
import type { AccessLogList } from '@/types/log'

export const logService = {
  async list(params?: {
    skip?: number
    limit?: number
    user_id?: number
    action?: string
  }): Promise<AccessLogList> {
    const response = await apiClient.get<AccessLogList>('/api/logs', { params })
    return response.data
  },
}
