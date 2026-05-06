export interface TrafficRecord {
  id: number
  device_id: number
  src_ip: string
  dst_ip: string
  src_port: number
  dst_port: number
  protocol: 'TCP' | 'UDP' | string
  bytes_sent: number
  bytes_received: number
  timestamp: string
}

export interface TrafficRecordCreate {
  src_ip: string
  dst_ip: string
  src_port: number
  dst_port: number
  protocol: string
  bytes_sent?: number
  bytes_received?: number
  timestamp?: string
}

export interface TrafficBatchCreate {
  device_id: number
  records: TrafficRecordCreate[]
}
