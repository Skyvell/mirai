import type { BiomarkerStatus } from '@/features/biomarkers/status'

export function matchesName(
  name: string,
  query: string | undefined
): boolean {
  const needle = query?.trim().toLowerCase() ?? ''
  if (needle === '') return true

  return name.toLowerCase().includes(needle)
}

export function matchesStatus(
  status: BiomarkerStatus,
  filter: BiomarkerStatus | undefined
): boolean {
  if (filter === undefined) return true

  return status === filter
}
