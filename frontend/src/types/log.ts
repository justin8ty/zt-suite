export interface AccessLog {
  id: number
  user_id: number | null
  action: string
  resource: string | null
  ip_address: string | null
  user_agent: string | null
  status: 'success' | 'failure' | string
  details: string | null
  timestamp: string
}

export interface AccessLogList {
  logs: AccessLog[]
  total: number
}
