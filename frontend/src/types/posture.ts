export interface PostureReportCreate {
  antivirus_present: boolean
  antivirus_enabled: boolean
  firewall_enabled: boolean
  disk_encrypted: boolean
  os_up_to_date: boolean
}

export interface PostureReport extends PostureReportCreate {
  id: number
  device_id: number
  compliance_score: number
  is_compliant: boolean
  timestamp: string
}
