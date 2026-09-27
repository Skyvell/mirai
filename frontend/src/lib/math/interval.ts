export type Interval = { min: number; max: number }

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

// Clamped so a value outside the interval pins to an edge of the scale; a
// zero-width interval has no inside, so it reports 0.
export function computePercentWithin(value: number, { min, max }: Interval): number {
  if (max === min) return 0

  return ((clamp(value, min, max) - min) / (max - min)) * 100
}

export function expandInterval({ min, max }: Interval, fraction: number): Interval {
  const padding = fraction * (max - min)
  return { min: min - padding, max: max + padding }
}

export function sampleInterval({ min, max }: Interval, count: number): number[] {
  if (count < 2) return count === 1 ? [min] : []

  return Array.from({ length: count }, (_, i) => min + (i / (count - 1)) * (max - min))
}
