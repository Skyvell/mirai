import { isOutsideInterval, type BiomarkerIntervals } from '@/features/biomarkers/intervals'

export const BIOMARKER_STATUSES = ['optimal', 'normal', 'critical'] as const
export type BiomarkerStatus = (typeof BIOMARKER_STATUSES)[number]

type ComputeBiomarkerStatusInput = {
  value: number
  intervals: BiomarkerIntervals
}

export function computeBiomarkerStatus({
  value,
  intervals,
}: ComputeBiomarkerStatusInput): BiomarkerStatus {
  // If outside reference interval --> critical.
  if (isOutsideInterval(value, intervals.reference)) return 'critical'

  // No optimal interval exists --> normal.
  if (intervals.optimal === null) return 'normal'

  // Outside optimal interval --> normal. If not outside --> optimal.
  return isOutsideInterval(value, intervals.optimal) ? 'normal' : 'optimal'
}
