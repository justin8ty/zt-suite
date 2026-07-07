import { apiClient } from '@/services/api-client'
import type { ProtectedFilesResponse } from '@/types/protected-resource'

export const protectedService = {
  async getFiles(deviceId: number): Promise<ProtectedFilesResponse> {
    const response = await apiClient.get<ProtectedFilesResponse>('/api/protected/files', {
      headers: {
        'X-Device-ID': deviceId,
      },
    })
    return response.data
  },

  async getFileContent(fileId: string, deviceId: number): Promise<Blob> {
    const response = await apiClient.get<Blob>(`/api/protected/files/${fileId}/content`, {
      headers: {
        'X-Device-ID': deviceId,
      },
      responseType: 'blob',
    })
    return response.data
  },
}
