import { useMemo } from 'react'
import { getRouteApi } from '@tanstack/react-router'
import { parse } from 'date-fns'
import { SearchX } from 'lucide-react'
import { EmptyState } from '@/components/empty-state'
import { Page } from '@/components/page'
import type { BiomarkerSummary } from '../domain/summary'
import { BiomarkerRowList } from '../components/row-list'
import { BiomarkerTileGrid } from '../components/tile-grid'
import { BiomarkerToolbar } from '../components/toolbar'
import { matchesName, matchesStatus } from '../domain/filters'
import { computeBiomarkerStatus, type BiomarkerStatus } from '../domain/status'
import { useViewMode } from '../hooks/use-view-mode'

const route = getRouteApi('/_authenticated/biomarkers/')

// Placeholder data while the card is built, read off docs/biomaker_page/card_designs/l.png.
const FIXTURES: BiomarkerSummary[] = [
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
  const { viewMode, selectViewMode } = useViewMode()

  const summaries = useMemo(
    () =>
      FIXTURES.filter(
        (summary) =>
          matchesName(summary.name, query) &&
          matchesStatus(computeBiomarkerStatus(summary), statusFilter)
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
    >
      <BiomarkerToolbar
        query={query ?? ''}
        onQueryChange={updateSearchQuery}
        statusFilter={statusFilter}
        onStatusFilterChange={updateStatusFilter}
        viewMode={viewMode}
        onViewModeChange={selectViewMode}
      />
      {summaries.length === 0 ? (
        <EmptyState
          icon={<SearchX />}
          title="No markers match"
          description="Adjust your search or status filter."
        />
      ) : viewMode === 'tile' ? (
        <BiomarkerTileGrid summaries={summaries} />
      ) : (
        <BiomarkerRowList summaries={summaries} />
      )}
    </Page>
  )
}
