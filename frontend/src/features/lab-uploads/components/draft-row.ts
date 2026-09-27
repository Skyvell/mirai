import type { LabDraftItemRead } from '@/client'

// One editable draft row, shared by both tables. Matched rows arrive pre-mapped;
// unmatched rows carry the parser's original label and start unmapped.
export type LabUploadDraftRow = {
  id: string
  origin: 'matched' | 'unmatched'
  sourceName: string | null
  displayName: string | null
  slug: string
  value: string
  unit: string
  referenceLow: string
  referenceHigh: string
  included: boolean
}

// Strip trailing zeros (and a bare trailing dot) so parsed decimals read
// cleanly; only touches strings that carry a decimal point.
function trimDecimal(value: string): string {
  if (!value.includes('.')) return value
  return value.replace(/\.?0+$/, '')
}

export function constructLabUploadDraftRow(item: LabDraftItemRead, origin: 'matched' | 'unmatched'): LabUploadDraftRow {
  return {
    id: item.id,
    origin,
    sourceName: item.source_name,
    displayName: item.display_name,
    slug: item.biomarker_slug ?? '',
    value: trimDecimal(item.value ?? item.raw_value ?? ''),
    unit: item.unit ?? '',
    referenceLow: trimDecimal(item.reference_low ?? ''),
    referenceHigh: trimDecimal(item.reference_high ?? ''),
    included: item.included,
  }
}
