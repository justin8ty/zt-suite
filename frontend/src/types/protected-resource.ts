export interface ProtectedFile {
  name: string
  size: string
  sensitivity: string
}

export interface ProtectedFilesResponse {
  message: string
  user: string
  device: string
  files: ProtectedFile[]
}
