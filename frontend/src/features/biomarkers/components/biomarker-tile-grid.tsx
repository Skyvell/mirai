import { BiomarkerTile } from '@/features/biomarkers/components/biomarker-tile'
import type { BiomarkerSummary } from '@/features/biomarkers/summary'

type BiomarkerTileGridProps = {
  cards: BiomarkerSummary[]
}

export function BiomarkerTileGrid({ cards }: BiomarkerTileGridProps) {
  return (
    <div className="grid gap-4 grid-cols-[repeat(auto-fill,minmax(320px,1fr))]">
      {cards.map((card) => (
        <BiomarkerTile key={card.name} {...card} />
      ))}
    </div>
  )
}
