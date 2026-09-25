import type { BiomarkerIntervals } from './intervals'

export type BiomarkerSummary = {
  name: string
  value: number
  unit: string
  intervals: BiomarkerIntervals
  previousValue: number | null
  measuredAt: Date
}
