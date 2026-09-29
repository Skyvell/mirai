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

export function isOutsideBiomarkerInterval(value: number, interval: BiomarkerInterval | null): boolean {
  if (interval === null) return false

  return (
    (interval.low !== null && value < interval.low) ||
    (interval.high !== null && value > interval.high)
  )
}

// Age is taken at the draw, since that is what the value was measured against;
// the age bounds are half-open, matching the seed.
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
