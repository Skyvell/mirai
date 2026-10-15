import { differenceInCalendarDays } from 'date-fns'
import type { BiomarkerIntervalRead, IntervalType, Sex } from '@/client'

// A null bound is open on that side; the API guarantees at least one of the two
// is set.
export type BiomarkerInterval = {
  low: number | null
  high: number | null
}

// Null means no such band exists.
export type BiomarkerIntervals = {
  reference: BiomarkerInterval | null
  optimal: BiomarkerInterval | null
}

type BiomarkerBandSubject = {
  sex: Sex
  dateOfBirth: Date
  measuredAt: Date
}

export function isWithinBiomarkerInterval(value: number, { low, high }: BiomarkerInterval): boolean {
  return (low === null || value >= low) && (high === null || value <= high)
}

export function selectBiomarkerBand(
  bands: BiomarkerIntervalRead[],
  type: IntervalType,
  { sex, dateOfBirth, measuredAt }: BiomarkerBandSubject
): BiomarkerIntervalRead | undefined {
  const ageDays = differenceInCalendarDays(measuredAt, dateOfBirth)

  return bands.find(
    (band) =>
      band.type === type &&
      (band.sex === null || band.sex === sex) &&
      (band.age_min_days === null || band.age_min_days <= ageDays) &&
      (band.age_max_days === null || ageDays < band.age_max_days)
  )
}
