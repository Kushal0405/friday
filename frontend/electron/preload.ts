import { contextBridge, ipcRenderer } from 'electron'

const fridayAPI = {
  windowMinimize: () => ipcRenderer.send('window:minimize'),
  windowMaximize: () => ipcRenderer.send('window:maximize'),
  windowClose: () => ipcRenderer.send('window:close'),
  getBackendConfig: () => ipcRenderer.invoke('config:get-backend')
}

contextBridge.exposeInMainWorld('friday', fridayAPI)

export type FridayAPI = typeof fridayAPI
