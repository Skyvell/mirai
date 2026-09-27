import { isOutsideBiomarkerInterval, type BiomarkerIntervals } from './intervals'

export const BIOMARKER_STATUSES = ['optimal', 'normal', 'critical'] as const
export type BiomarkerStatus = (typeof BIOMARKER_STATUSES)[number]

export function parseBiomarkerStatus(value: string | null): BiomarkerStatus | undefined {
  return BIOMARKER_STATUSES.find((status) => status === value)
}

type ComputeBiomarkerStatusInput = {
  value: number
  intervals: BiomarkerIntervals
}

export function computeBiomarkerStatus({
  value,
  intervals,
}: ComputeBiomarkerStatusInput): BiomarkerStatus {
  // If outside reference interval --> critical.
  if (isOutsideBiomarkerInterval(value, intervals.reference)) return 'critical'

  // No optimal interval exists --> normal.
  if (intervals.optimal === null) return 'normal'

  // Outside optimal interval --> normal. If not outside --> optimal.
  return isOutsideBiomarkerInterval(value, intervals.optimal) ? 'normal' : 'optimal'
}
