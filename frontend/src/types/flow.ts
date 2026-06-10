export interface NetworkFlow {
  id: number
  device_id: number
  batch_id: string
  src_ip: string | null
  dst_ip: string | null
  src_port: number | null
  dst_port: number | null
  protocol: string | null
  timestamp: string
  flow_duration: number | null
  total_fwd_packets: number | null
  total_bwd_packets: number | null
  total_fwd_bytes: number | null
  total_bwd_bytes: number | null
  malicious_score: number | null
  prediction: number | null
  prediction_label: string | null
  detection_source: string
  raw_features: Record<string, unknown>
}
