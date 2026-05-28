import { apiClient } from '@/services/api-client'
import type {
  LoginRequest,
  LoginResponse,
  MFAEnrollResponse,
  MFAValidateRequest,
  MFAVerifyRequest,
  RefreshRequest,
  TokenResponse,
} from '@/types/auth'
import type { User } from '@/types/user'

export const authService = {
  async login(payload: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/api/auth/login', payload)
    return response.data
  },

  async validateMfa(payload: MFAValidateRequest): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/api/auth/mfa/validate', payload)
    return response.data
  },

  async enrollMfa(): Promise<MFAEnrollResponse> {
    const response = await apiClient.post<MFAEnrollResponse>('/api/auth/mfa/enroll')
    return response.data
  },

  async verifyMfa(payload: MFAVerifyRequest): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>('/api/auth/mfa/verify', payload)
    return response.data
  },

  async refresh(payload: RefreshRequest = {}): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/api/auth/refresh', payload)
    return response.data
  },

  async logout(payload: RefreshRequest = {}): Promise<void> {
    await apiClient.post('/api/auth/logout', payload)
  },

  async getMe(): Promise<User> {
    const response = await apiClient.get<User>('/api/auth/me')
    return response.data
  },
}

export function isMfaRequired(response: LoginResponse): response is { mfa_required: true; temp_token: string } {
  return 'mfa_required' in response && response.mfa_required
}
