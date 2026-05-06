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
  os_type: string
  os_version?: string | null
  agent_version?: string | null
}
