import { isWithinBiomarkerInterval, type BiomarkerIntervals } from './intervals'

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
  if (intervals.reference !== null && !isWithinBiomarkerInterval(value, intervals.reference)) {
    return 'critical'
  }

  if (intervals.optimal === null) return 'normal'

  return isWithinBiomarkerInterval(value, intervals.optimal) ? 'optimal' : 'normal'
}
