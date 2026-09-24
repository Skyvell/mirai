import { formatDistanceToNow } from 'date-fns'
import { Card } from '@/components/ui/card'
import { computeBiomarkerStatus } from '@/features/biomarkers/status'
import { resolveStatusColorProps } from '@/features/biomarkers/status-color'
import type { BiomarkerSummary } from '@/features/biomarkers/summary'
import { BiomarkerRuler } from '@/features/biomarkers/components/biomarker-ruler'
import { BiomarkerStatusLabel } from '@/features/biomarkers/components/biomarker-status-label'
import { BiomarkerTrend } from '@/features/biomarkers/components/biomarker-trend'

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
      <BiomarkerRuler value={value} intervals={intervals} showBounds={false} />
      <div className="text-xs text-muted-foreground">
        <BiomarkerTrend value={value} previousValue={previousValue} />
      </div>
      <span className="text-xs text-muted-foreground md:text-right">
        {formatDistanceToNow(measuredAt, { addSuffix: true })}
      </span>
    </Card>
  )
}
