import { formatDistanceToNow } from 'date-fns'
import { computePercentageChange } from '@/lib/math/percentage'
import { Card, CardAction, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { BiomarkerIntervals } from '@/features/biomarkers/intervals'
import { computeBiomarkerStatus } from '@/features/biomarkers/status'
import { BiomarkerRuler } from '@/features/biomarkers/components/biomarker-ruler'

// Resolves the status colour once on the card; descendants read var(--status-color).
const STATUS_COLOR_VAR =
  'data-[status=optimal]:[--status-color:var(--optimal)] ' +
  'data-[status=normal]:[--status-color:var(--normal)] ' +
  'data-[status=critical]:[--status-color:var(--critical)]'

export type BiomarkerTileProps = {
  name: string
  value: number
  unit: string
  intervals: BiomarkerIntervals
  previousValue: number | null
  measuredAt: Date
}

export function BiomarkerTile({
  name,
  value,
  unit,
  intervals,
  previousValue,
  measuredAt,
}: BiomarkerTileProps) {
  const status = computeBiomarkerStatus({ value, intervals })
  const change =
    previousValue === null || previousValue === 0 ? null : computePercentageChange(value, previousValue)

  return (
    <Card data-status={status} className={STATUS_COLOR_VAR}>
      <CardHeader>
        <CardTitle>{name}</CardTitle>
        <CardAction>
          <span className="text-[10px] font-medium tracking-widest uppercase text-(--status-color)">
            {status}
          </span>
        </CardAction>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <div className="flex items-baseline gap-1.5">
          <span className="text-6xl font-light tracking-tight">{value}</span>
          <span className="text-sm text-muted-foreground">{unit}</span>
        </div>
        <BiomarkerRuler value={value} intervals={intervals} />
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            {change !== null && `${change > 0 ? '↑' : change < 0 ? '↓' : '→'} ${Math.abs(change)}%`}
          </span>
          <span>{formatDistanceToNow(measuredAt, { addSuffix: true })}</span>
        </div>
      </CardContent>
    </Card>
  )
}

