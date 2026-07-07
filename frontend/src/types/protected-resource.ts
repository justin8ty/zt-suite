export interface ProtectedFile {
  id: string
  name: string
  size: string
  sensitivity: string
  type: 'pdf' | 'csv' | 'text' | string
  mime_type: string
  summary: string
  content?: string
}

export interface ProtectedFilesResponse {
  message: string
  user: string
  device: string
  files: ProtectedFile[]
}
