import { formatDistanceToNow } from 'date-fns'
import { Card, CardAction, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { computeBiomarkerStatus } from '../domain/status'
import { resolveStatusColorProps } from './status-color'
import type { BiomarkerSummary } from '../domain/summary'
import { BiomarkerBulletGraph } from './bullet-graph'
import { BiomarkerStatusLabel } from './status-label'
import { BiomarkerChange } from './change'

export function BiomarkerTile({
  name,
  value,
  unit,
  intervals,
  previousValue,
  measuredAt,
}: BiomarkerSummary) {
  const status = computeBiomarkerStatus({ value, intervals })

  return (
    <Card {...resolveStatusColorProps(status)}>
      <CardHeader>
        <CardTitle>{name}</CardTitle>
        <CardAction>
          <BiomarkerStatusLabel status={status} />
        </CardAction>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <div className="flex items-baseline gap-1.5">
          <span className="text-6xl font-light tracking-tight">{value}</span>
          <span className="text-sm text-muted-foreground">{unit}</span>
        </div>
        <BiomarkerBulletGraph value={value} intervals={intervals} />
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <BiomarkerChange value={value} previousValue={previousValue} />
          <span>{formatDistanceToNow(measuredAt, { addSuffix: true })}</span>
        </div>
      </CardContent>
    </Card>
  )
}
