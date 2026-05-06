export type RoleName = 'admin' | 'user' | 'viewer'

export interface Role {
  id: number
  name: RoleName | string
  description: string | null
}

export interface User {
  id: number
  email: string
  is_active: boolean
  mfa_enabled: boolean
  roles: Role[]
  created_at: string
  updated_at: string
}
