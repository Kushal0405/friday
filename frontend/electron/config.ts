export interface BackendConfig {
  host: string
  port: number
}

export function getBackendConfig(): BackendConfig {
  return {
    host: process.env['FRIDAY_HOST'] || '127.0.0.1',
    port: Number(process.env['FRIDAY_PORT']) || 8765
  }
}
