import { useMemo } from 'react'
import { getRouteApi } from '@tanstack/react-router'
import { parse } from 'date-fns'
import { SearchX } from 'lucide-react'
import { EmptyState } from '@/components/empty-state'
import { Page } from '@/components/page'
import type { BiomarkerTileProps } from '@/features/biomarkers/components/biomarker-tile'
import { BiomarkerTileGrid } from '@/features/biomarkers/components/biomarker-tile-grid'
import { BiomarkerToolbar } from '@/features/biomarkers/components/biomarker-toolbar'
import { matchesName, matchesStatus } from '@/features/biomarkers/filters'
import { computeBiomarkerStatus, type BiomarkerStatus } from '@/features/biomarkers/status'

const route = getRouteApi('/_authenticated/biomarkers/')

// Placeholder data while the card is built, read off docs/biomaker_page/card_designs/l.png.
const FIXTURES: BiomarkerTileProps[] = [
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
  const { query, status: statusFilter } = route.useSearch()
  const navigate = route.useNavigate()

  const cards = useMemo(
    () =>
      FIXTURES.filter(
        (card) =>
          matchesName(card.name, query) && matchesStatus(computeBiomarkerStatus(card), statusFilter)
      ).sort((a, b) => a.name.localeCompare(b.name)),
    [query, statusFilter]
  )

  const updateSearchQuery = (value: string) =>
    navigate({ search: (prev) => ({ ...prev, query: value || undefined }), replace: true })

  const updateStatusFilter = (value: BiomarkerStatus | undefined) =>
    navigate({ search: (prev) => ({ ...prev, status: value }), replace: true })

  return (
    <Page
      width="wide"
      title="Biomarkers"
      description="Track your biomarkers over time. Use “Add data” in the top bar to upload a blood-test PDF or enter values manually."
    >
      <BiomarkerToolbar
        query={query ?? ''}
        onQueryChange={updateSearchQuery}
        statusFilter={statusFilter}
        onStatusFilterChange={updateStatusFilter}
      />
      {cards.length === 0 ? (
        <EmptyState
          icon={<SearchX />}
          title="No markers match"
          description="Adjust your search or status filter."
        />
      ) : (
        <BiomarkerTileGrid cards={cards} />
      )}
    </Page>
  )
}
