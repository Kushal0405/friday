import { app, BrowserWindow, globalShortcut, ipcMain } from 'electron'
import { createMainWindow } from './window'
import { getBackendConfig } from './config'
import { startBackend, stopBackend } from './backend'
import { is } from './env'

let mainWindow: BrowserWindow | null = null

function toggleMainWindow(): void {
  if (!mainWindow || mainWindow.isDestroyed()) return
  if (mainWindow.isVisible() && mainWindow.isFocused()) {
    mainWindow.hide()
  } else {
    mainWindow.show()
    mainWindow.focus()
  }
}

ipcMain.on('window:minimize', () => mainWindow?.minimize())
ipcMain.on('window:maximize', () => {
  if (!mainWindow) return
  if (mainWindow.isMaximized()) {
    mainWindow.unmaximize()
  } else {
    mainWindow.maximize()
  }
})
ipcMain.on('window:close', () => mainWindow?.close())
ipcMain.handle('config:get-backend', () => getBackendConfig())

app.whenReady().then(() => {
  if (!is.dev) {
    startBackend()
  }

  mainWindow = createMainWindow()

  const registered = globalShortcut.register('Control+Alt+Space', toggleMainWindow)
  if (!registered) {
    console.error('[FRIDAY] Failed to register global shortcut Ctrl+Alt+Space')
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      mainWindow = createMainWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('will-quit', () => {
  globalShortcut.unregisterAll()
  stopBackend()
})
