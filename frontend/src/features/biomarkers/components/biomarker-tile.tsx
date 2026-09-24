import { formatDistanceToNow } from 'date-fns'
import { Card, CardAction, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { computeBiomarkerStatus } from '@/features/biomarkers/status'
import { resolveStatusColorProps } from '@/features/biomarkers/status-color'
import type { BiomarkerSummary } from '@/features/biomarkers/summary'
import { BiomarkerRuler } from '@/features/biomarkers/components/biomarker-ruler'
import { BiomarkerStatusLabel } from '@/features/biomarkers/components/biomarker-status-label'
import { BiomarkerTrend } from '@/features/biomarkers/components/biomarker-trend'

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
        <BiomarkerRuler value={value} intervals={intervals} />
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <BiomarkerTrend value={value} previousValue={previousValue} />
          <span>{formatDistanceToNow(measuredAt, { addSuffix: true })}</span>
        </div>
      </CardContent>
    </Card>
  )
}
