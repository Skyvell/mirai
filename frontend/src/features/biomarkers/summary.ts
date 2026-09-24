import type { BiomarkerIntervals } from '@/features/biomarkers/intervals'

export type BiomarkerSummary = {
  name: string
  value: number
  unit: string
  intervals: BiomarkerIntervals
  previousValue: number | null
  measuredAt: Date
}
