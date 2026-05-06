import type { User } from '@/types/user'

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: 'bearer' | string
}

export interface MFARequiredResponse {
  mfa_required: true
  temp_token: string
}

export type LoginResponse = TokenResponse | MFARequiredResponse

export interface RefreshRequest {
  refresh_token: string
}

export interface MFAValidateRequest {
  temp_token: string
  code: string
}

export interface MFAEnrollResponse {
  secret: string
  provisioning_uri: string
}

export interface MFAVerifyRequest {
  code: string
}

export interface AuthStateSnapshot {
  accessToken: string | null
  refreshToken: string | null
  mfaTempToken: string | null
  currentUser: User | null
}
