import { Sample } from '../types'

export function exportCSV(samples: Sample[], filename = 'samples.csv') {
  const headers = ['t', 'V', 'I', 'P', 'T']
  const rows = samples.map((s) => [s.t ?? '', s.V, s.I, s.P ?? s.V * s.I, s.T ?? ''])
  const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
