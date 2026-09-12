import { Card, CardAction, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { computeBiomarkerStatus } from '@/features/biomarkers/status'
import { BiomarkerRuler } from '@/features/biomarkers/components/biomarker-ruler'

// Resolves the status colour once on the card; descendants read var(--status-color).
const STATUS_COLOR_VAR =
  'data-[status=optimal]:[--status-color:var(--optimal)] ' +
  'data-[status=normal]:[--status-color:var(--normal)] ' +
  'data-[status=critical]:[--status-color:var(--critical)]'

export type BiomarkerCardProps = {
  name: string
  value: number
  unit: string
  referenceLow: number | null
  referenceHigh: number | null
  optimalLow: number | null
  optimalHigh: number | null
  previousValue: number | null
  measuredAt: Date
}

export function BiomarkerCard({
  name,
  value,
  unit,
  referenceLow,
  referenceHigh,
  optimalLow,
  optimalHigh,
}: BiomarkerCardProps) {
  const status = computeBiomarkerStatus({
    value,
    referenceLow,
    referenceHigh,
    optimalLow,
    optimalHigh,
  })

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
        <BiomarkerRuler
          value={value}
          referenceLow={referenceLow}
          referenceHigh={referenceHigh}
          optimalLow={optimalLow}
          optimalHigh={optimalHigh}
        />
      </CardContent>
    </Card>
  )
}
