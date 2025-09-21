import { Sample } from '../types'
import * as XLSX from 'xlsx'
import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'

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

export function exportXLSX(samples: Sample[], filename = 'samples.xlsx') {
  const aoa = [
    ['t', 'V', 'I', 'P', 'T'],
    ...samples.map((s) => [s.t ?? '', s.V, s.I, s.P ?? s.V * s.I, s.T ?? '']),
  ]
  const ws = XLSX.utils.aoa_to_sheet(aoa)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Samples')
  XLSX.writeFile(wb, filename)
}

export function exportPDF(samples: Sample[], filename = 'samples.pdf') {
  const doc = new jsPDF({ orientation: 'landscape' })
  doc.setFontSize(14)
  doc.text('PV Monitor - Samples Export', 14, 16)
  const head = [['t', 'V', 'I', 'P', 'T']]
  const body = samples.map((s) => [
    s.t ?? '',
    (s.V ?? '').toString(),
    (s.I ?? '').toString(),
    ((s.P ?? (s.V * s.I)) ?? '').toString(),
    (s.T ?? '').toString(),
  ])
  autoTable(doc, {
    head,
    body,
    startY: 22,
    styles: { fontSize: 8 },
    headStyles: { fillColor: [40, 167, 69] },
  })
  doc.save(filename)
}
