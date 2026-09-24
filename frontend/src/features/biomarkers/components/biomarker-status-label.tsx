import type { BiomarkerStatus } from '@/features/biomarkers/status'

type BiomarkerStatusLabelProps = {
  status: BiomarkerStatus
}

export function BiomarkerStatusLabel({ status }: BiomarkerStatusLabelProps) {
  return (
    <span className="text-[10px] font-medium tracking-widest uppercase text-(--status-color)">
      {status}
    </span>
  )
}
