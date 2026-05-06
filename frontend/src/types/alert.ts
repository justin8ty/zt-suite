export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical'

export interface SecurityAlert {
  id: number
  device_id: number
  severity: AlertSeverity | string
  category: string
  title: string
  description: string
  source_ip: string | null
  is_acknowledged: boolean
  acknowledged_by: number | null
  acknowledged_at: string | null
  timestamp: string
}

export interface AlertCreate {
  device_id: number
  severity: AlertSeverity | string
  category: string
  title: string
  description: string
  source_ip?: string | null
}

export interface AlertUpdate {
  is_acknowledged: boolean
}
