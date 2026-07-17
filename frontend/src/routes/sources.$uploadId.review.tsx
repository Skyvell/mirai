import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, createFileRoute, useNavigate } from '@tanstack/react-router'
import { toast } from 'sonner'
import { ApiErrorAlert } from '@/components/api-error-alert'
import { BiomarkerSelect } from '@/components/biomarker-select'
import { QueryPane } from '@/components/query-pane'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  confirmLabUploadMutation,
  getLabUploadOptions,
  listBiomarkerSeriesQueryKey,
  listBiomarkersOptions,
  listLabUploadsQueryKey,
  updateLabDraftMutation,
} from '@/client/@tanstack/react-query.gen'
import type { BiomarkerRead, LabDraft, LabDraftItemRead, LabUploadDetail } from '@/client'
import { cn, pluralize } from '@/lib/utils'
import { IN_PROGRESS } from '@/lib/lab-uploads'

export const Route = createFileRoute('/sources/$uploadId/review')({
  component: ReviewComponent,
})

function ReviewComponent() {
  const { uploadId } = Route.useParams()
  const detail = useQuery({
    ...getLabUploadOptions({ path: { upload_id: uploadId } }),
    // Keep polling if the user lands here before parsing has finished.
    refetchInterval: (query) =>
      query.state.data && IN_PROGRESS.has(query.state.data.status) ? 3000 : false,
  })

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4">
      <Link
        to="/sources"
        className="text-sm text-muted-foreground underline underline-offset-3 hover:text-foreground"
      >
        ← Back to sources
      </Link>

      <QueryPane query={detail}>{(data) => <ReviewBody detail={data} />}</QueryPane>
    </div>
  )
}

function ReviewBody({ detail }: { detail: LabUploadDetail }) {
  if (IN_PROGRESS.has(detail.status)) {
    return <p className="text-sm text-muted-foreground">Still reading this report…</p>
  }
  if (detail.status === 'failed') {
    return <ApiErrorAlert message={detail.error_message ?? 'Parsing failed.'} />
  }
  if (detail.status === 'committed') {
    return <p className="text-sm text-muted-foreground">This report has been committed.</p>
  }
  if (detail.draft === null) {
    return <p className="text-sm text-muted-foreground">Nothing to review.</p>
  }
  // Key on the id so local edit state initializes once from the loaded draft.
  return (
    <ReviewForm
      key={detail.id}
      uploadId={detail.id}
      filename={detail.filename}
      draft={detail.draft}
    />
  )
}

// One editable draft row, shared by both tables. Matched rows arrive pre-mapped;
// unmatched rows carry the parser's original label and start unmapped.
type DraftRow = {
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

function toRow(item: LabDraftItemRead, origin: 'matched' | 'unmatched'): DraftRow {
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

function ReviewForm({
  uploadId,
  filename,
  draft,
}: {
  uploadId: string
  filename: string
  draft: LabDraft
}) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const biomarkers = useQuery(listBiomarkersOptions())

  const [measuredAt, setMeasuredAt] = useState(draft.measured_at ?? '')
  const [rows, setRows] = useState<DraftRow[]>(() => [
    ...draft.items.map((i) => toRow(i, 'matched')),
    ...draft.skipped.map((i) => toRow(i, 'unmatched')),
  ])

  const update = useMutation(updateLabDraftMutation())
  const confirm = useMutation({
    ...confirmLabUploadMutation(),
    onSuccess: () => {
      toast.success(`Added ${pluralize(keptCount, 'measurement')} to your record`)
    },
  })
  const pending = update.isPending || confirm.isPending
  const error = update.error ?? confirm.error

  const matched = rows.filter((r) => r.origin === 'matched')
  const unmatched = rows.filter((r) => r.origin === 'unmatched')

  // A row commits only once kept and mapped to a known biomarker.
  const keptCount = rows.filter((r) => r.included && r.slug).length

  function patchRow(id: string, patch: Partial<DraftRow>) {
    setRows((rs) => rs.map((r) => (r.id === id ? { ...r, ...patch } : r)))
  }

  // Mapping a marker keeps it and fills the unit from the mapped biomarker when blank.
  function mapRow(id: string, slug: string) {
    const canonical = biomarkers.data?.find((b: BiomarkerRead) => b.slug === slug)
    setRows((rs) =>
      rs.map((r) =>
        r.id === id
          ? { ...r, slug, included: true, unit: r.unit || canonical?.canonical_unit || '' }
          : r,
      ),
    )
  }

  async function onConfirm() {
    // One edit payload carries every row's fields and mapping, then commit.
    const body = {
      measured_at: measuredAt || null,
      items: rows.map((r) => ({
        id: r.id,
        value: r.value,
        unit: r.unit || null,
        reference_low: r.referenceLow || null,
        reference_high: r.referenceHigh || null,
        included: r.included,
        ...(r.slug ? { biomarker_slug: r.slug } : {}),
      })),
    }

    // A failed mutation renders inline via its error state; just stop here.
    try {
      await update.mutateAsync({ path: { upload_id: uploadId }, body })
      await confirm.mutateAsync({ path: { upload_id: uploadId } })
    } catch {
      return
    }

    queryClient.invalidateQueries({ queryKey: listLabUploadsQueryKey() })
    queryClient.invalidateQueries({ queryKey: listBiomarkerSeriesQueryKey() })
    navigate({ to: '/sources' })
  }

  return (
    <div className="flex flex-col gap-5 pb-20">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Review {filename}</h1>
        <p className="text-muted-foreground">
          Check the extracted values, then add them to your record.
        </p>
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="measured-at">Collection date</Label>
        <Input
          id="measured-at"
          type="date"
          className="w-fit"
          value={measuredAt}
          onChange={(e) => setMeasuredAt(e.target.value)}
        />
      </div>

      <section className="flex flex-col gap-2">
        <h2 className="text-lg font-medium">Extracted biomarkers</h2>
        {matched.length === 0 ? (
          <p className="text-sm text-muted-foreground">No biomarkers were matched.</p>
        ) : (
          <DraftItemsTable
            rows={matched}
            biomarkers={biomarkers.data ?? []}
            onPatch={patchRow}
            onMap={mapRow}
          />
        )}
      </section>

      {unmatched.length > 0 && (
        <section className="flex flex-col gap-2">
          <h2 className="text-lg font-medium">Unmapped biomarkers</h2>
          <p className="text-sm text-muted-foreground">
            These labels weren&rsquo;t recognized. Map one to a biomarker to include it.
          </p>
          <DraftItemsTable
            rows={unmatched}
            biomarkers={biomarkers.data ?? []}
            onPatch={patchRow}
            onMap={mapRow}
          />
        </section>
      )}

      {error && <ApiErrorAlert error={error} />}

      {/* The negative margin cancels the `p-6` padding on <main> in __root.tsx so the bar spans full width. */}
      <div className="sticky bottom-0 -mx-6 flex items-center gap-3 border-t bg-background px-6 py-3">
        <Button onClick={onConfirm} disabled={pending || keptCount === 0 || !measuredAt}>
          {pending ? 'Adding…' : `Add ${pluralize(keptCount, 'measurement')} to my record`}
        </Button>
        {!measuredAt && (
          <p className="text-sm text-muted-foreground">
            Set the collection date to add these measurements.
          </p>
        )}
      </div>
    </div>
  )
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
function DraftItemsTable({
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

