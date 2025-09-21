import React, { useEffect, useMemo, useState } from 'react'
import { useStore } from './store'
import KpiCard from './components/KpiCard'
import Charts from './components/Charts'
import { exportCSV } from './utils/export'

function useKPIs() {
  const samples = useStore((s) => s.samples)
  return useMemo(() => {
    const last = samples.length ? samples[samples.length - 1] : undefined
    const V = last?.V
    const I = last?.I
    const P = last ? (last.P ?? last.V * last.I) : undefined
    const T = last?.T
    return { V, I, P, T }
  }, [samples])
}

export default function App() {
  const { samples, mpp, wsStatus, connectWS, fetchSamples, fetchMPP, importText, setFilters } = useStore()
  const [text, setText] = useState<string>('')
  const [smoothing, setSmoothing] = useState(false)
  const [window, setWindow] = useState(5)
  const [from, setFrom] = useState<string>('')
  const [to, setTo] = useState<string>('')
  const [downsample, setDownsample] = useState<number>(1)

  useEffect(() => {
    connectWS()
    fetchSamples().then(() => fetchMPP())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const KPIs = useKPIs()
  const displaySamples = useMemo(() => {
    const factor = Math.max(1, Math.floor(downsample))
    if (factor === 1) return samples
    return samples.filter((_, i) => i % factor === 0)
  }, [samples, downsample])

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold">PV Monitor</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm">WebSocket: <b className={wsStatus === 'connected' ? 'text-green-600' : (wsStatus === 'connecting' ? 'text-yellow-600' : 'text-red-600')}>{wsStatus}</b></span>
            <button className="px-3 py-1 rounded bg-indigo-600 text-white" onClick={() => exportCSV(samples)}>Exporter CSV</button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto px-4 py-6 w-full">
        <div className="flex flex-wrap gap-3 mb-6">
          <KpiCard label="Tension" value={KPIs.V?.toFixed(2)} unit="V" />
          <KpiCard label="Courant" value={KPIs.I?.toFixed(3)} unit="A" />
          <KpiCard label="Puissance" value={KPIs.P?.toFixed(2)} unit="W" />
          <KpiCard label="Température" value={KPIs.T?.toFixed?.(1)} unit="°C" />
          {mpp ? <KpiCard label="MPP" value={`${mpp.Vmp.toFixed(2)}V / ${mpp.Imp.toFixed(3)}A / ${mpp.Pmp.toFixed(2)}W`} /> : null}
        </div>

        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="font-medium mb-2">Import texte/CSV</div>
          <textarea
            placeholder="Collez ici des lignes comme: V:20.2V I:0.10A P:2.1W"
            className="w-full h-32 p-2 border rounded"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <div className="mt-3 flex gap-3">
            <button
              className="px-3 py-1 rounded bg-green-600 text-white"
              onClick={async () => {
                if (!text.trim()) return
                await importText(text)
                setText('')
              }}
            >Importer</button>
            <button
              className="px-3 py-1 rounded bg-gray-100"
              onClick={async () => {
                setFilters({ from: from.trim() || undefined, to: to.trim() || undefined })
                await fetchSamples(); await fetchMPP();
              }}
            >Rafraîchir</button>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={smoothing} onChange={(e) => setSmoothing(e.target.checked)} />
              Lissage (moyenne glissante)
            </label>
            <input type="number" min={3} max={51} step={2} value={window} onChange={(e) => setWindow(parseInt(e.target.value || '5'))} className="w-20 border rounded px-2 py-1" />
            <label className="flex items-center gap-2">
              Downsample
              <input type="number" min={1} max={100} step={1} value={downsample} onChange={(e) => setDownsample(parseInt(e.target.value || '1'))} className="w-20 border rounded px-2 py-1" />
            </label>
          </div>

          <div className="mt-3 flex gap-3 items-end flex-wrap">
            <div>
              <label className="text-sm text-gray-600">From (ISO)</label>
              <input type="text" placeholder="2025-01-01T00:00:00Z" className="w-64 border rounded px-2 py-1 block" value={from} onChange={(e) => setFrom(e.target.value)} />
            </div>
            <div>
              <label className="text-sm text-gray-600">To (ISO)</label>
              <input type="text" placeholder="2025-12-31T23:59:59Z" className="w-64 border rounded px-2 py-1 block" value={to} onChange={(e) => setTo(e.target.value)} />
            </div>
            <button className="px-3 py-1 rounded bg-indigo-600 text-white" onClick={async () => {
              setFilters({ from: from.trim() || undefined, to: to.trim() || undefined })
              await fetchSamples(); await fetchMPP();
            }}>Appliquer la plage</button>
          </div>
        </div>

        <Charts samples={displaySamples} mpp={mpp} smoothing={smoothing} window={window} />
      </main>

      <footer className="text-center text-xs text-gray-500 py-4">© {new Date().getFullYear()} PV Monitor</footer>
    </div>
  )
}
