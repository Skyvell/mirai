import type { ReactNode } from 'react'
import type { UseQueryResult } from '@tanstack/react-query'
import { ApiErrorAlert } from '@/components/api-error-alert'
import { TableSkeleton } from '@/components/table-skeleton'

// Standard query rendering: error alert → loading skeleton → optional empty
// state (when the loaded data holds no items) → content from loaded data.
export function QueryPane<T>({
  query,
  empty,
  children,
}: {
  query: UseQueryResult<T, unknown>
  empty?: ReactNode
  children: (data: T) => ReactNode
}) {
  if (query.isError) return <ApiErrorAlert error={query.error} />
  if (query.data === undefined) return <TableSkeleton />
  if (empty !== undefined && isEmpty(query.data)) return empty
  return children(query.data)
}

// Empty covers both list responses and slug-keyed dict responses.
function isEmpty(data: unknown): boolean {
  if (Array.isArray(data)) return data.length === 0
  if (data !== null && typeof data === 'object') return Object.keys(data).length === 0
  return false
}
