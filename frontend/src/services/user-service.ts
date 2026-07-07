import { apiClient } from '@/services/api-client'
import type { RoleName, User } from '@/types/user'

export interface UserCreate {
  email: string
  password: string
}

export interface UserUpdate {
  email?: string | null
  password?: string | null
  is_active?: boolean | null
}

export interface UserList {
  users: User[]
  total: number
}

export const userService = {
  async create(payload: UserCreate): Promise<User> {
    const response = await apiClient.post<User>('/api/users', payload)
    return response.data
  },

  async list(params?: { skip?: number; limit?: number }): Promise<UserList> {
    const response = await apiClient.get<UserList>('/api/users', { params })
    return response.data
  },

  async getById(userId: number): Promise<User> {
    const response = await apiClient.get<User>(`/api/users/${userId}`)
    return response.data
  },

  async update(userId: number, payload: UserUpdate): Promise<User> {
    const response = await apiClient.patch<User>(`/api/users/${userId}`, payload)
    return response.data
  },

  async delete(userId: number): Promise<void> {
    await apiClient.delete(`/api/users/${userId}`)
  },

  async assignRole(userId: number, roleName: RoleName): Promise<User> {
    const response = await apiClient.post<User>(`/api/users/${userId}/roles`, null, {
      params: { role_name: roleName },
    })
    return response.data
  },

  async removeRole(userId: number, roleName: RoleName): Promise<User> {
    const response = await apiClient.delete<User>(`/api/users/${userId}/roles`, {
      params: { role_name: roleName },
    })
    return response.data
  },
}
