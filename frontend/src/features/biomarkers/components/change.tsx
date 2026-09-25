import { computePercentageChange } from '@/lib/math/percentage'

type BiomarkerChangeProps = {
  value: number
  previousValue: number | null
}

function resolveTrendGlyph(change: number): string {
  if (change > 0) return '↑'
  if (change < 0) return '↓'

  return '→'
}

export function BiomarkerChange({ value, previousValue }: BiomarkerChangeProps) {
  const change =
    previousValue === null || previousValue === 0
      ? null
      : computePercentageChange(value, previousValue)

  return <span>{change !== null && `${resolveTrendGlyph(change)} ${Math.abs(change)}%`}</span>
}
