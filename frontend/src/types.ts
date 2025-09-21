export type Sample = {
  id?: number
  t?: string
  V: number
  I: number
  P?: number
  T?: number | null
  source?: 'SERIAL' | 'BLYNK' | 'IMPORT' | 'MANUAL'
}

export type MPP = {
  Vmp: number
  Imp: number
  Pmp: number
  index: number
  t?: string
}
