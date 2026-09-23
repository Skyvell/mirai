import { useMemo } from 'react'
import { getRouteApi } from '@tanstack/react-router'
import { parse } from 'date-fns'
import { Page } from '@/components/page'
import type { BiomarkerCardProps } from '@/features/biomarkers/components/biomarker-card'
import { BiomarkerCardGrid } from '@/features/biomarkers/components/biomarker-card-grid'
import { BiomarkerToolbar } from '@/features/biomarkers/components/biomarker-toolbar'
import { matchesQuery } from '@/features/biomarkers/filters'

const route = getRouteApi('/_authenticated/biomarkers/')

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
  const { q } = route.useSearch()
  const navigate = route.useNavigate()

  const cards = useMemo(
    () =>
      FIXTURES.filter((card) => matchesQuery(card.name, q)).sort((a, b) =>
        a.name.localeCompare(b.name)
      ),
    [q]
  )

  const handleQueryChange = (value: string) =>
    navigate({ search: (prev) => ({ ...prev, q: value || undefined }), replace: true })

  return (
    <Page
      width="wide"
      title="Biomarkers"
      description="Track your biomarkers over time. Use “Add data” in the top bar to upload a blood-test PDF or enter values manually."
    >
      <BiomarkerToolbar query={q ?? ''} onQueryChange={handleQueryChange} />
      <BiomarkerCardGrid cards={cards} />
    </Page>
  )
}
