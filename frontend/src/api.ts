export type HealthResponse = {
  status: 'ok'
  service: string
  version: string
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`)

  if (!response.ok) {
    throw new Error(`API health check failed with ${response.status}`)
  }

  return response.json() as Promise<HealthResponse>
}

