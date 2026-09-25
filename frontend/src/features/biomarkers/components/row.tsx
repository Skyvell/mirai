import { formatDistanceToNow } from 'date-fns'
import { Card } from '@/components/ui/card'
import { computeBiomarkerStatus } from '../domain/status'
import { resolveStatusColorProps } from './status-color'
import type { BiomarkerSummary } from '../domain/summary'
import { BiomarkerBulletGraph } from './bullet-graph'
import { BiomarkerStatusLabel } from './status-label'
import { BiomarkerChange } from './change'

const ROW_LAYOUT =
  'grid grid-cols-1 gap-2 px-4 ' +
  'md:grid-cols-[minmax(0,1fr)_8rem_5rem_minmax(0,1.4fr)_3.5rem_7rem] md:items-center md:gap-4'

export function BiomarkerRow({
  name,
  value,
  unit,
  intervals,
  previousValue,
  measuredAt,
}: BiomarkerSummary) {
  const status = computeBiomarkerStatus({ value, intervals })

  return (
    <Card {...resolveStatusColorProps(status, ROW_LAYOUT)}>
      <span className="font-medium">{name}</span>
      <div className="flex items-baseline gap-1.5">
        <span className="text-xl font-light tracking-tight">{value}</span>
        <span className="text-xs text-muted-foreground">{unit}</span>
      </div>
      <BiomarkerStatusLabel status={status} />
      <BiomarkerBulletGraph value={value} intervals={intervals} showBounds={false} />
      <div className="text-xs text-muted-foreground">
        <BiomarkerChange value={value} previousValue={previousValue} />
      </div>
      <span className="text-xs text-muted-foreground md:text-right">
        {formatDistanceToNow(measuredAt, { addSuffix: true })}
      </span>
    </Card>
  )
}
