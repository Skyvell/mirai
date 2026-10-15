import type { BiomarkerIntervals } from './intervals'

export type BiomarkerSummary = {
  slug: string
  name: string
  value: number
  unit: string
  intervals: BiomarkerIntervals
  previousValue: number | null
  measuredAt: Date
}
