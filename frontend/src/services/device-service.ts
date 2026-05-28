import { apiClient } from '@/services/api-client'
import type { AgentTokenCreate, AgentTokenIssued, Device, DeviceCreate, DeviceList } from '@/types/device'
import type { PostureReport, PostureReportCreate } from '@/types/posture'

export const deviceService = {
  async register(payload: DeviceCreate): Promise<Device> {
    const response = await apiClient.post<Device>('/api/devices', payload)
    return response.data
  },

  async list(params?: { skip?: number; limit?: number }): Promise<DeviceList> {
    const response = await apiClient.get<DeviceList>('/api/devices', { params })
    return response.data
  },

  async getById(deviceId: number): Promise<Device> {
    const response = await apiClient.get<Device>(`/api/devices/${deviceId}`)
    return response.data
  },

  async submitPosture(deviceId: number, payload: PostureReportCreate): Promise<PostureReport> {
    const response = await apiClient.post<PostureReport>(`/api/devices/${deviceId}/posture`, payload)
    return response.data
  },

  async getLatestPosture(deviceId: number): Promise<PostureReport> {
    const response = await apiClient.get<PostureReport>(`/api/devices/${deviceId}/posture`)
    return response.data
  },

  async issueAgentToken(deviceId: number, payload: AgentTokenCreate): Promise<AgentTokenIssued> {
    const response = await apiClient.post<AgentTokenIssued>(`/api/devices/${deviceId}/agent-tokens`, payload)
    return response.data
  },
}
