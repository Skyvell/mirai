export type BiomarkerStatus = 'optimal' | 'normal' | 'critical'

type ComputeBiomarkerStatusInput = {
  value: number
  referenceLow: number | null
  referenceHigh: number | null
  optimalLow: number | null
  optimalHigh: number | null
}

export function computeBiomarkerStatus({
  value,
  referenceLow,
  referenceHigh,
  optimalLow,
  optimalHigh,
}: ComputeBiomarkerStatusInput): BiomarkerStatus {
  // If outside reference range --> critical.
  if (isOutsideRange(value, referenceLow, referenceHigh)) return 'critical'

  // No optimal range exists --> normal.
  if (optimalLow === null && optimalHigh === null) return 'normal'

  // Outside optimal range --> normal. If not outside --> optimal.
  return isOutsideRange(value, optimalLow, optimalHigh) ? 'normal' : 'optimal'
}

function isOutsideRange(value: number, low: number | null, high: number | null): boolean {
  return (low !== null && value < low) || (high !== null && value > high)
}