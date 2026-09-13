export type Interval = { min: number; max: number }

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

// Position of a value inside an interval as 0-100, clamped so values outside it
// pin to an edge. A zero-width interval has no inside, so it reports 0.
export function computePercentWithin(value: number, { min, max }: Interval): number {
  if (max === min) return 0

  return ((clamp(value, min, max) - min) / (max - min)) * 100
}

// Grows an interval at both ends by a fraction of its own width.
export function expandInterval({ min, max }: Interval, fraction: number): Interval {
  const padding = fraction * (max - min)
  return { min: min - padding, max: max + padding }
}

// Evenly spaced values across an interval, including both endpoints.
export function sampleInterval({ min, max }: Interval, count: number): number[] {
  if (count < 2) return count === 1 ? [min] : []

  return Array.from({ length: count }, (_, i) => min + (i / (count - 1)) * (max - min))
}
