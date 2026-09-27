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

export function isOutsideBiomarkerInterval(value: number, interval: BiomarkerInterval | null): boolean {
  if (interval === null) return false

  return (
    (interval.low !== null && value < interval.low) ||
    (interval.high !== null && value > interval.high)
  )
}
