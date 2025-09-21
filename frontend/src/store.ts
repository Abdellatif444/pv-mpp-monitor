import { create } from 'zustand'
import { Sample, MPP } from './types'
import { api, wsUrl } from './api/client'

export type Filters = {
  from?: string
  to?: string
  smoothing: boolean
  window: number
}

export type WSStatus = 'disconnected' | 'connecting' | 'connected'

type State = {
  samples: Sample[]
  mpp?: MPP
  wsStatus: WSStatus
  filters: Filters
  setFilters: (f: Partial<Filters>) => void
  connectWS: () => void
  disconnectWS: () => void
  fetchSamples: () => Promise<void>
  fetchMPP: () => Promise<void>
  importText: (text: string) => Promise<void>
}

let socket: WebSocket | null = null

export const useStore = create<State>((set, get) => ({
  samples: [],
  mpp: undefined,
  wsStatus: 'disconnected',
  filters: { smoothing: false, window: 5 },
  setFilters: (f) => set((s) => ({ filters: { ...s.filters, ...f } })),

  connectWS: () => {
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) return
    set({ wsStatus: 'connecting' })
    socket = new WebSocket(wsUrl)
    socket.onopen = () => set({ wsStatus: 'connected' })
    socket.onclose = () => set({ wsStatus: 'disconnected' })
    socket.onerror = () => set({ wsStatus: 'disconnected' })
    socket.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data)
        if (msg?.type === 'sample' && msg?.data) {
          set((s) => ({ samples: [...s.samples, msg.data as Sample] }))
        }
      } catch {}
    }
  },

  disconnectWS: () => {
    if (socket) {
      socket.close()
      socket = null
      set({ wsStatus: 'disconnected' })
    }
  },

  fetchSamples: async () => {
    const { filters } = get()
    const params: any = {}
    if (filters.from) params.from = filters.from
    if (filters.to) params.to = filters.to
    const r = await api.get<Sample[]>('/api/samples', { params })
    set({ samples: r.data })
  },

  fetchMPP: async () => {
    const { filters } = get()
    const params: any = {}
    if (filters.from) params.from = filters.from
    if (filters.to) params.to = filters.to
    const r = await api.get<MPP>('/api/mpp', { params })
    set({ mpp: r.data })
  },

  importText: async (text: string) => {
    await api.post('/api/import/text', { text })
    // refresh after import
    await get().fetchSamples()
    await get().fetchMPP()
  },
}))

export function movingAverage(y: number[], window: number): number[] {
  const n = y.length
  const out = new Array(n).fill(0)
  const half = Math.floor(window / 2)
  for (let i = 0; i < n; i++) {
    let sum = 0
    let count = 0
    for (let j = Math.max(0, i - half); j <= Math.min(n - 1, i + half); j++) {
      sum += y[j]
      count++
    }
    out[i] = count > 0 ? sum / count : y[i]
  }
  return out
}

export function detectVocIsc(samples: Sample[]): { Voc?: number; Isc?: number } {
  if (!samples.length) return {}
  const eps = 1e-3
  let Voc = undefined as number | undefined
  let Isc = undefined as number | undefined

  for (const s of samples) {
    if (Math.abs(s.I) <= eps) {
      Voc = Voc === undefined ? s.V : Math.max(Voc, s.V)
    }
    if (Math.abs(s.V) <= eps) {
      Isc = Isc === undefined ? s.I : Math.max(Isc, s.I)
    }
  }
  return { Voc, Isc }
}
