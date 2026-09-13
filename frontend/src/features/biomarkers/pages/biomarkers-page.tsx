import { parse } from 'date-fns'
import type { BiomarkerCardProps } from '@/features/biomarkers/components/biomarker-card'
import { BiomarkerCardGrid } from '@/features/biomarkers/components/biomarker-card-grid'
import { Page } from '@/components/page'

// Placeholder data while the card is built, read off docs/biomaker_page/card_designs/l.png.
const FIXTURES: BiomarkerCardProps[] = [
  {
    name: 'HDL Cholesterol',
    value: 1.6,
    unit: 'mmol/L',
    intervals: {
      reference: { low: 1.0, high: 2.2 },
      optimal: { low: 1.3, high: 2.0 },
    },
    previousValue: 1.63,
    measuredAt: parse('2026-08-17', 'yyyy-MM-dd', new Date()),
  },
  {
    name: 'Triglycerides',
    value: 1.2,
    unit: 'mmol/L',
    intervals: {
      reference: { low: 0.5, high: 1.7 },
      optimal: { low: 0.5, high: 1.1 },
    },
    previousValue: 1.2,
    measuredAt: parse('2026-08-17', 'yyyy-MM-dd', new Date()),
  },
  {
    name: 'LDL Cholesterol',
    value: 3.4,
    unit: 'mmol/L',
    intervals: {
      reference: { low: 1.8, high: 3.0 },
      optimal: { low: 1.8, high: 2.6 },
    },
    previousValue: 3.12,
    measuredAt: parse('2026-08-17', 'yyyy-MM-dd', new Date()),
  },
]

export function BiomarkersPage() {
  return (
    <Page
      width="wide"
      title="Biomarkers"
      description="Track your biomarkers over time. Use “Add data” in the top bar to upload a blood-test PDF or enter values manually."
    >
      <BiomarkerCardGrid cards={FIXTURES} />
    </Page>
  )
}
