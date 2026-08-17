import { ChildProcess, spawn } from 'child_process'
import { app } from 'electron'
import { existsSync } from 'fs'
import { join } from 'path'
import { is } from './env'
import { getBackendConfig } from './config'

let backendProcess: ChildProcess | null = null

function getBackendExePath(): string {
  const exeName = 'friday-backend.exe'
  return is.dev
    ? join(__dirname, '../../resources/backend', exeName)
    : join(process.resourcesPath, 'backend', exeName)
}

export function startBackend(): void {
  const exePath = getBackendExePath()
  if (!existsSync(exePath)) {
    console.error(`[FRIDAY] Backend executable not found at ${exePath}`)
    return
  }

  const { host, port } = getBackendConfig()

  backendProcess = spawn(exePath, [], {
    env: { ...process.env, FRIDAY_HOST: host, FRIDAY_PORT: String(port) },
    windowsHide: true
  })

  backendProcess.stdout?.on('data', (data) => console.log(`[backend] ${data.toString().trim()}`))
  backendProcess.stderr?.on('data', (data) => console.error(`[backend] ${data.toString().trim()}`))
  backendProcess.on('exit', (code) => {
    console.log(`[FRIDAY] Backend process exited with code ${code}`)
    backendProcess = null
  })
}

export function stopBackend(): void {
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill()
    backendProcess = null
  }
}

app.on('before-quit', stopBackend)
