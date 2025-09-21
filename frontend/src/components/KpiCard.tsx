import React from 'react'

type Props = {
  label: string
  value?: number | string
  unit?: string
}

export default function KpiCard({ label, value, unit }: Props) {
  return (
    <div className="bg-white rounded-lg shadow p-4 min-w-[140px]">
      <div className="text-sm text-gray-500">{label}</div>
      <div className="text-2xl font-semibold">
        {value === undefined || value === null || Number.isNaN(value as number) ? '--' : value}
        {unit ? <span className="text-base font-normal text-gray-500 ml-1">{unit}</span> : null}
      </div>
    </div>
  )
}
