import { computeBiomarkerStatus, type BiomarkerStatus } from './status'
import type { BiomarkerSummary } from './summary'

export function matchesBiomarkerName(
  name: string,
  query: string | undefined
): boolean {
  const needle = query?.trim().toLowerCase() ?? ''
  if (needle === '') return true

  return name.toLowerCase().includes(needle)
}

function matchesBiomarkerStatus(
  status: BiomarkerStatus,
  filter: BiomarkerStatus | undefined
): boolean {
  if (filter === undefined) return true

  return status === filter
}

type BiomarkerSummaryFilter = {
  query: string | undefined
  status: BiomarkerStatus | undefined
}

// Alphabetical because status order would reshuffle with every new measurement.
export function selectVisibleBiomarkerSummaries(
  summaries: BiomarkerSummary[],
  { query, status }: BiomarkerSummaryFilter
): BiomarkerSummary[] {
  return summaries
    .filter(
      (summary) =>
        matchesBiomarkerName(summary.name, query) &&
        matchesBiomarkerStatus(computeBiomarkerStatus(summary), status)
    )
    .sort((a, b) => a.name.localeCompare(b.name))
}
