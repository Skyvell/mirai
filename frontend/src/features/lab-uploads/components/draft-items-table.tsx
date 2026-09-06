import type { BiomarkerRead, LabDraftItemRead } from '@/client'
import { BiomarkerSelect } from '@/features/biomarkers/components/biomarker-select'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { cn } from 'cn'

// One editable draft row, shared by both tables. Matched rows arrive pre-mapped;
// unmatched rows carry the parser's original label and start unmapped.
export type DraftRow = {
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

export function toRow(item: LabDraftItemRead, origin: 'matched' | 'unmatched'): DraftRow {
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

// Ghost cell input that sizes to its content (so the column fits the value —
// no clipping, no fixed widths); min-width keeps empty cells clickable.
const CELL_CLASS =
  'h-8 w-auto min-w-12 field-sizing-content border-transparent bg-transparent px-1.5 shadow-none hover:border-input focus-visible:border-ring dark:bg-transparent'

// Ghost styling for the biomarker combobox so it reads like the other cells:
// borderless and transparent at rest, border on hover/focus. min-w-0 lets the
// flex column shrink (name truncates) instead of pushing the table past the
// container.
const SELECT_CELL_CLASS =
  'h-8 w-full min-w-0 border-transparent bg-transparent px-1.5 shadow-none hover:border-input hover:bg-transparent dark:bg-transparent dark:hover:bg-transparent'

// Shared editable table for both matched and unmatched draft rows. Each row's
// biomarker is a dropdown: pre-selected when matched, empty when the parser
// couldn't map it (its original label shows above the dropdown).
export function DraftItemsTable({
  rows,
  biomarkers,
  onPatch,
  onMap,
}: {
  rows: DraftRow[]
  biomarkers: BiomarkerRead[]
  onPatch: (id: string, patch: Partial<DraftRow>) => void
  onMap: (id: string, slug: string) => void
}) {
  // Auto layout: the Biomarker column takes the slack, every other column
  // sizes to its content (inputs use field-sizing), so nothing clips.
  return (
    <Table>
      <colgroup>
        <col />
        <col className="w-full" />
        <col />
        <col />
        <col />
        <col />
      </colgroup>
      <TableHeader>
        <TableRow>
          <TableHead>Keep</TableHead>
          <TableHead>Biomarker</TableHead>
          <TableHead className="text-right">Value</TableHead>
          <TableHead>Unit</TableHead>
          <TableHead className="text-right">Ref. low</TableHead>
          <TableHead className="text-right">Ref. high</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row) => {
          const name = row.sourceName ?? row.displayName ?? 'biomarker'
          return (
            <TableRow key={row.id}>
              <TableCell>
                <Checkbox
                  checked={row.included}
                  onCheckedChange={(c) => onPatch(row.id, { included: c === true })}
                  aria-label={`Keep ${name}`}
                />
              </TableCell>
              <TableCell>
                <div className="flex flex-col gap-1">
                  {row.sourceName && (
                    <span className="text-xs text-muted-foreground">{row.sourceName}</span>
                  )}
                  <BiomarkerSelect
                    biomarkers={biomarkers}
                    value={row.slug}
                    onChange={(slug) => onMap(row.id, slug)}
                    triggerClassName={SELECT_CELL_CLASS}
                  />
                </div>
              </TableCell>
              <TableCell className="text-right">
                <NumberCell
                  value={row.value}
                  onChange={(v) => onPatch(row.id, { value: v })}
                />
              </TableCell>
              <TableCell>
                <TextCell value={row.unit} onChange={(v) => onPatch(row.id, { unit: v })} />
              </TableCell>
              <TableCell className="text-right">
                <NumberCell
                  value={row.referenceLow}
                  onChange={(v) => onPatch(row.id, { referenceLow: v })}
                />
              </TableCell>
              <TableCell className="text-right">
                <NumberCell
                  value={row.referenceHigh}
                  onChange={(v) => onPatch(row.id, { referenceHigh: v })}
                />
              </TableCell>
            </TableRow>
          )
        })}
      </TableBody>
    </Table>
  )
}

function NumberCell({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <Input
      inputMode="decimal"
      className={cn(CELL_CLASS, 'text-right tabular-nums')}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  )
}

function TextCell({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <Input
      className={CELL_CLASS}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  )
}
