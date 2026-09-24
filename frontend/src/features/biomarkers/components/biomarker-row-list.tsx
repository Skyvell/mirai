import type { BiomarkerSummary } from '@/features/biomarkers/summary'
import { BiomarkerRow } from '@/features/biomarkers/components/biomarker-row'

type BiomarkerRowListProps = {
  cards: BiomarkerSummary[]
}

export function BiomarkerRowList({ cards }: BiomarkerRowListProps) {
  return (
    <div className="flex flex-col gap-3">
      {cards.map((card) => (
        <BiomarkerRow key={card.name} {...card} />
      ))}
    </div>
  )
}
