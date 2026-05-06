import axios, { AxiosError, type AxiosRequestConfig } from 'axios'

import { useAuthStore } from '@/stores/auth-store'
import type { TokenResponse } from '@/types/auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

interface RetryableAxiosRequestConfig extends AxiosRequestConfig {
  _retry?: boolean
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableAxiosRequestConfig | undefined
    const refreshToken = useAuthStore.getState().refreshToken

    if (error.response?.status !== 401 || !originalRequest || originalRequest._retry) {
      return Promise.reject(error)
    }

    if (!refreshToken) {
      useAuthStore.getState().clearAuth()
      return Promise.reject(error)
    }

    originalRequest._retry = true

    try {
      const response = await axios.post<TokenResponse>(`${API_BASE_URL}/api/auth/refresh`, {
        refresh_token: refreshToken,
      })

      useAuthStore.getState().setTokens(response.data)
      originalRequest.headers = {
        ...originalRequest.headers,
        Authorization: `Bearer ${response.data.access_token}`,
      }

      return apiClient(originalRequest)
    } catch (refreshError) {
      useAuthStore.getState().clearAuth()
      return Promise.reject(refreshError)
    }
  },
)

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail

    if (typeof detail === 'string') {
      return detail
    }

    if (Array.isArray(detail)) {
      return detail
        .map((item: unknown) => {
          if (typeof item === 'object' && item !== null && 'msg' in item) {
            return String(item.msg)
          }
          return 'Validation error'
        })
        .join(', ')
    }

    return error.message
  }

  if (error instanceof Error) {
    return error.message
  }

  return 'Unexpected error'
}
