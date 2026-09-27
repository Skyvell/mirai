import type { BiomarkerStatus } from './status'

export function matchesBiomarkerName(
  name: string,
  query: string | undefined
): boolean {
  const needle = query?.trim().toLowerCase() ?? ''
  if (needle === '') return true

  return name.toLowerCase().includes(needle)
}

export function matchesBiomarkerStatus(
  status: BiomarkerStatus,
  filter: BiomarkerStatus | undefined
): boolean {
  if (filter === undefined) return true

  return status === filter
}
