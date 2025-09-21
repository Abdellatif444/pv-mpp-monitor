import React, { useMemo } from 'react'
import Plot from 'react-plotly.js'
import { Sample, MPP } from '../types'
import { movingAverage, detectVocIsc } from '../store'

function round(value: number, decimals = 2) {
  const factor = Math.pow(10, decimals)
  return Math.round(value * factor) / factor
}

type Props = {
  samples: Sample[]
  mpp?: MPP
  smoothing?: boolean
  window?: number
}

export default function Charts({ samples, mpp, smoothing, window = 5 }: Props) {
  const { xV, yI, yP, mppPoint, vocIsc } = useMemo(() => {
    const xV = samples.map((s) => s.V)
    const yI = samples.map((s) => s.I)
    const yP = samples.map((s) => (s.P ?? s.V * s.I))
    const mppPoint = mpp ? { x: mpp.Vmp, y: mpp.Pmp } : undefined
    const vocIsc = detectVocIsc(samples)
    return { xV, yI, yP, mppPoint, vocIsc }
  }, [samples, mpp])

  const yI_sm = smoothing ? movingAverage(yI, window) : yI
  const yP_sm = smoothing ? movingAverage(yP, window) : yP

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full">
      <div className="bg-white rounded-lg shadow p-3">
        <div className="font-medium mb-2">I-V (Courant en fonction de la tension)</div>
        <Plot
          data={[
            {
              x: xV,
              y: yI_sm.map((v) => round(v, 3)),
              type: 'scatter',
              mode: 'markers+lines',
              marker: { color: '#2563eb' },
              name: 'I(V)'
            },
            vocIsc.Voc !== undefined ? {
              x: [vocIsc.Voc], y: [0], type: 'scatter', mode: 'markers', marker: { color: 'orange', size: 10 }, name: 'Voc'
            } : {},
            vocIsc.Isc !== undefined ? {
              x: [0], y: [vocIsc.Isc], type: 'scatter', mode: 'markers', marker: { color: 'purple', size: 10 }, name: 'Isc'
            } : {},
          ]}
          layout={{
            autosize: true,
            xaxis: { title: 'V (Volts)' },
            yaxis: { title: 'I (Ampères)' },
            margin: { l: 50, r: 10, t: 10, b: 40 },
            showlegend: true,
          }}
          useResizeHandler
          style={{ width: '100%', height: 400 }}
          config={{ displayModeBar: true, toImageButtonOptions: { filename: 'iv-curve' } }}
        />
      </div>

      <div className="bg-white rounded-lg shadow p-3">
        <div className="font-medium mb-2">P-V (Puissance en fonction de la tension)</div>
        <Plot
          data={[
            {
              x: xV,
              y: yP_sm.map((v) => round(v, 2)),
              type: 'scatter',
              mode: 'markers+lines',
              marker: { color: '#059669' },
              name: 'P(V)'
            },
            mpp ? {
              x: [mpp.Vmp],
              y: [mpp.Pmp],
              type: 'scatter',
              mode: 'markers+text',
              marker: { color: 'red', size: 12 },
              text: [`MPP: V=${round(mpp.Vmp, 2)}V, I=${round(mpp.Imp, 3)}A, P=${round(mpp.Pmp, 2)}W`],
              textposition: 'top center',
              name: 'MPP'
            } : {},
          ]}
          layout={{
            autosize: true,
            xaxis: { title: 'V (Volts)' },
            yaxis: { title: 'P (Watts)' },
            margin: { l: 50, r: 10, t: 10, b: 40 },
            showlegend: true,
          }}
          useResizeHandler
          style={{ width: '100%', height: 400 }}
          config={{ displayModeBar: true, toImageButtonOptions: { filename: 'pv-curve' } }}
        />
      </div>
    </div>
  )
}
