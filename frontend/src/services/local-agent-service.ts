export interface LocalAgentIdentity {
  agent_running: boolean
  agent_id: string | null
  device_id: number | null
}

const localAgentIdentityUrl = 'http://127.0.0.1:8756/identity'

export const localAgentService = {
  async getIdentity(): Promise<LocalAgentIdentity> {
    const response = await fetch(localAgentIdentityUrl, {
      cache: 'no-store',
    })

    if (!response.ok) {
      throw new Error('Local ZT Agent identity endpoint is unavailable')
    }

    return response.json() as Promise<LocalAgentIdentity>
  },
}
