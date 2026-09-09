import { Card, CardHeader, CardTitle } from '@/components/ui/card'

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

export function BiomarkerCard({ name }: BiomarkerCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{name}</CardTitle>
      </CardHeader>
    </Card>
  )
}
