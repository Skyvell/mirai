import { BiomarkerTile, type BiomarkerTileProps } from '@/features/biomarkers/components/biomarker-tile'

type BiomarkerTileGridProps = {
  cards: BiomarkerTileProps[]
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
