import { BiomarkerTile } from './tile'
import type { BiomarkerSummary } from '../domain/summary'

type BiomarkerTileGridProps = {
  summaries: BiomarkerSummary[]
}

export function BiomarkerTileGrid({ summaries }: BiomarkerTileGridProps) {
  return (
    <div className="grid gap-4 grid-cols-[repeat(auto-fill,minmax(320px,1fr))]">
      {summaries.map((summary) => (
        <BiomarkerTile key={summary.name} {...summary} />
      ))}
    </div>
  )
}
