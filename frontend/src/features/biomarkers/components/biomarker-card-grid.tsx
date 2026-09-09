import { BiomarkerCard, type BiomarkerCardProps } from '@/features/biomarkers/components/biomarker-card'

type BiomarkerCardGridProps = {
  cards: BiomarkerCardProps[]
}

export function BiomarkerCardGrid({ cards }: BiomarkerCardGridProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {cards.map((card) => (
        <BiomarkerCard key={card.name} {...card} />
      ))}
    </div>
  )
}
