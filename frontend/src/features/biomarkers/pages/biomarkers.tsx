import { getRouteApi } from '@tanstack/react-router'
import { SearchX } from 'lucide-react'
import { EmptyState } from '@/components/empty-state'
import { Page } from '@/components/page'
import { QueryPane } from '@/components/query-pane'
import { useBiomarkerSummaries } from '../api/summaries'
import { BiomarkerRowList } from '../components/row-list'
import { BiomarkerTileGrid } from '../components/tile-grid'
import { BiomarkerToolbar } from '../components/toolbar'
import { selectVisibleBiomarkerSummaries } from '../domain/filters'
import type { BiomarkerStatus } from '../domain/status'
import { useBiomarkerViewMode } from '../hooks/use-view-mode'

const route = getRouteApi('/_authenticated/biomarkers/')

export function BiomarkersPage() {
  const { query, status: statusFilter } = route.useSearch()
  const navigate = route.useNavigate()
  const { viewMode, selectViewMode } = useBiomarkerViewMode()
  const summaries = useBiomarkerSummaries()

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
      <QueryPane query={summaries}>
        {(data) => {
          const visible = selectVisibleBiomarkerSummaries(data, { query, status: statusFilter })

          if (visible.length === 0) {
            return (
              <EmptyState
                icon={<SearchX />}
                title="No markers match"
                description="Adjust your search or status filter."
              />
            )
          }

          return viewMode === 'tile' ? (
            <BiomarkerTileGrid summaries={visible} />
          ) : (
            <BiomarkerRowList summaries={visible} />
          )
        }}
      </QueryPane>
    </Page>
  )
}
