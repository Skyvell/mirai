import type { BiomarkerSummary } from '../domain/summary'
import { BiomarkerRow } from './row'

type BiomarkerRowListProps = {
  summaries: BiomarkerSummary[]
}

export function BiomarkerRowList({ summaries }: BiomarkerRowListProps) {
  return (
    <div className="flex flex-col gap-3">
      {summaries.map((summary) => (
        <BiomarkerRow key={summary.name} {...summary} />
      ))}
    </div>
  )
}
