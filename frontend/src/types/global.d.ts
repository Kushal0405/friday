export interface BackendConfig {
  host: string
  port: number
}

export interface FridayAPI {
  windowMinimize: () => void
  windowMaximize: () => void
  windowClose: () => void
  getBackendConfig: () => Promise<BackendConfig>
}

declare global {
  interface Window {
    friday: FridayAPI
  }
}
