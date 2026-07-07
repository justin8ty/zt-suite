export interface Device {
  id: number
  hostname: string
  os_type: string
  os_version: string | null
  agent_version: string | null
  user_id: number | null
  last_seen: string
  is_compliant: boolean
}

export interface DeviceList {
  devices: Device[]
  total: number
}

export interface DeviceCreate {
  hostname: string
  user_id?: number | null
  os_type?: string
  os_version?: string | null
  agent_version?: string | null
}

export interface AgentTokenCreate {
  name: string
}

export interface AgentTokenRead {
  id: number
  device_id: number
  name: string
  created_at: string
  last_used_at: string | null
  revoked_at: string | null
}

export interface AgentTokenIssued extends AgentTokenRead {
  token: string
}
