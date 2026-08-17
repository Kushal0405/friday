import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { WIDGET_DEFINITIONS, type WidgetId } from '../types/widgets'

interface WidgetState {
  enabled: Record<WidgetId, boolean>
  setEnabled: (id: WidgetId, value: boolean) => void
  isEnabled: (id: WidgetId) => boolean
}

const defaultEnabled = Object.fromEntries(
  WIDGET_DEFINITIONS.map((w) => [w.id, w.defaultEnabled])
) as Record<WidgetId, boolean>

export const useWidgetStore = create<WidgetState>()(
  persist(
    (set, get) => ({
      enabled: defaultEnabled,
      setEnabled: (id, value) =>
        set((state) => ({ enabled: { ...state.enabled, [id]: value } })),
      isEnabled: (id) => get().enabled[id] ?? false,
    }),
    { name: 'friday-widget-settings' }
  )
)
