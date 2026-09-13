import { BiomarkerCard, type BiomarkerCardProps } from '@/features/biomarkers/components/biomarker-card'

type BiomarkerCardGridProps = {
  cards: BiomarkerCardProps[]
}

export function BiomarkerCardGrid({ cards }: BiomarkerCardGridProps) {
  return (
    <div className="grid gap-4 grid-cols-[repeat(auto-fill,minmax(320px,1fr))]">
      {cards.map((card) => (
        <BiomarkerCard key={card.name} {...card} />
      ))}
    </div>
  )
}
