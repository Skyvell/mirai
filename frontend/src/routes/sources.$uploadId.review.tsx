import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, createFileRoute, useNavigate } from '@tanstack/react-router'
import { BiomarkerSelect } from '@/components/biomarker-select'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  confirmLabUploadMutation,
  getLabUploadOptions,
  listBiomarkerSeriesQueryKey,
  listBiomarkersOptions,
  listLabUploadsQueryKey,
  updateLabDraftMutation,
} from '@/client/@tanstack/react-query.gen'
import type { BiomarkerRead, LabDraftItemRead, LabUploadDetail } from '@/client'
import { apiErrorMessage } from '@/lib/api'
import { cn } from '@/lib/utils'
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
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <Link
        to="/sources"
        className="text-sm text-muted-foreground underline underline-offset-3 hover:text-foreground"
      >
        ← Back to sources
      </Link>

      {detail.isError ? (
        <p className="text-sm text-destructive">{apiErrorMessage(detail.error)}</p>
      ) : detail.data === undefined ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <ReviewBody detail={detail.data} />
      )}
    </div>
  )
}

function ReviewBody({ detail }: { detail: LabUploadDetail }) {
  if (IN_PROGRESS.has(detail.status)) {
    return <p className="text-sm text-muted-foreground">Still reading this report…</p>
  }
  if (detail.status === 'failed') {
    return (
      <p className="text-sm text-destructive">
        {detail.error_message ?? 'Parsing failed.'}
      </p>
    )
  }
  if (detail.status === 'committed') {
    return <p className="text-sm text-muted-foreground">This report has been committed.</p>
  }
  if (detail.draft === null) {
    return <p className="text-sm text-muted-foreground">Nothing to review.</p>
  }
  // Key on the id so local edit state initializes once from the loaded draft.
  return <ReviewForm key={detail.id} detail={detail} />
}

type ItemRow = {
  id: string
  displayName: string | null
  value: string
  unit: string
  referenceLow: string
  referenceHigh: string
  included: boolean
}

type SkippedRow = {
  id: string
  sourceName: string | null
  slug: string
  value: string
  unit: string
  referenceLow: string
  referenceHigh: string
}

// Strip trailing zeros (and a bare trailing dot) so parsed decimals read
// cleanly; only touches strings that carry a decimal point.
function trimDecimal(value: string): string {
  if (!value.includes('.')) return value
  return value.replace(/\.?0+$/, '')
}

// Only out-of-range needs surfacing; 'ok' covers in-range, unbounded, and unparseable.
type RangeStatus = 'low' | 'high' | 'ok'

// Classify a value against its reference bounds from the live edit strings.
function rangeStatus(value: string, low: string, high: string): RangeStatus {
  const v = Number(value)
  if (value === '' || Number.isNaN(v)) return 'ok'

  const hi = high === '' ? null : Number(high)
  const lo = low === '' ? null : Number(low)
  if (hi !== null && !Number.isNaN(hi) && v > hi) return 'high'
  if (lo !== null && !Number.isNaN(lo) && v < lo) return 'low'
  return 'ok'
}

function toItemRow(item: LabDraftItemRead): ItemRow {
  return {
    id: item.id,
    displayName: item.display_name,
    value: trimDecimal(item.value ?? ''),
    unit: item.unit ?? '',
    referenceLow: trimDecimal(item.reference_low ?? ''),
    referenceHigh: trimDecimal(item.reference_high ?? ''),
    included: item.included,
  }
}

function toSkippedRow(item: LabDraftItemRead): SkippedRow {
  return {
    id: item.id,
    sourceName: item.source_name,
    slug: '',
    value: trimDecimal(item.raw_value ?? ''),
    unit: item.unit ?? '',
    referenceLow: '',
    referenceHigh: '',
  }
}

function ReviewForm({ detail }: { detail: LabUploadDetail }) {
  const draft = detail.draft!
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const catalogue = useQuery(listBiomarkersOptions())

  const [measuredAt, setMeasuredAt] = useState(draft.measured_at ?? '')
  const [items, setItems] = useState<ItemRow[]>(() => draft.items.map(toItemRow))
  const [skipped, setSkipped] = useState<SkippedRow[]>(() => draft.skipped.map(toSkippedRow))

  const update = useMutation(updateLabDraftMutation())
  const confirm = useMutation(confirmLabUploadMutation())
  const pending = update.isPending || confirm.isPending
  const error = update.error ?? confirm.error

  const keptCount =
    items.filter((i) => i.included).length + skipped.filter((s) => s.slug).length
  const allKept = items.length > 0 && items.every((i) => i.included)
  // Classify each row once; reused for both the summary count and its badge.
  const statuses = items.map((i) => rangeStatus(i.value, i.referenceLow, i.referenceHigh))
  const outOfRange = statuses.filter((s) => s !== 'ok').length

  function patchItem(id: string, patch: Partial<ItemRow>) {
    setItems((rows) => rows.map((r) => (r.id === id ? { ...r, ...patch } : r)))
  }

  function patchSkipped(id: string, patch: Partial<SkippedRow>) {
    setSkipped((rows) => rows.map((r) => (r.id === id ? { ...r, ...patch } : r)))
  }

  function toggleAll(included: boolean) {
    setItems((rows) => rows.map((r) => ({ ...r, included })))
  }

  // Map an unmatched marker, prefilling the unit from the catalogue when blank.
  function mapSkipped(row: SkippedRow, slug: string) {
    const canonical = catalogue.data?.find((b: BiomarkerRead) => b.slug === slug)
    patchSkipped(row.id, {
      slug,
      unit: row.unit || canonical?.canonical_unit || '',
    })
  }

  async function onConfirm() {
    // One edit payload, then commit; mapped skipped rows join as included items.
    const body = {
      measured_at: measuredAt || null,
      items: [
        ...items.map((i) => ({
          id: i.id,
          value: i.value,
          unit: i.unit || null,
          reference_low: i.referenceLow || null,
          reference_high: i.referenceHigh || null,
          included: i.included,
        })),
        ...skipped
          .filter((s) => s.slug)
          .map((s) => ({
            id: s.id,
            biomarker_slug: s.slug,
            value: s.value,
            unit: s.unit || null,
            reference_low: s.referenceLow || null,
            reference_high: s.referenceHigh || null,
            included: true,
          })),
      ],
    }

    await update.mutateAsync({ path: { upload_id: detail.id }, body })
    await confirm.mutateAsync({ path: { upload_id: detail.id } })
    queryClient.invalidateQueries({ queryKey: listLabUploadsQueryKey() })
    queryClient.invalidateQueries({ queryKey: listBiomarkerSeriesQueryKey() })
    navigate({ to: '/sources' })
  }

  return (
    <div className="flex flex-col gap-5 pb-20">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Review {detail.filename}</h1>
        <p className="text-muted-foreground">
          Check the extracted values, then add them to your record.
        </p>
        {outOfRange > 0 && (
          <p className="mt-1 text-sm text-warning">
            {outOfRange} of {items.length} outside reference range
          </p>
        )}
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
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">No biomarkers were matched.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[34rem] text-sm">
              <colgroup>
                <col className="w-10" />
                <col />
                <col className="w-24" />
                <col className="w-24" />
                <col className="w-20" />
                <col className="w-20" />
                <col className="w-16" />
              </colgroup>
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="py-2 font-medium">
                    <Checkbox
                      checked={allKept}
                      onCheckedChange={(c) => toggleAll(c === true)}
                      aria-label="Keep all biomarkers"
                      title="Keep all"
                    />
                  </th>
                  <th className="py-2 font-medium">Biomarker</th>
                  <th className="py-2 text-right font-medium">Value</th>
                  <th className="py-2 font-medium">Unit</th>
                  <th className="py-2 text-right font-medium">Ref. low</th>
                  <th className="py-2 text-right font-medium">Ref. high</th>
                  <th className="py-2 font-medium" />
                </tr>
              </thead>
              <tbody>
                {items.map((item, index) => {
                  const status = statuses[index]
                  return (
                    <tr key={item.id} className="border-b">
                      <td className="py-1">
                        <Checkbox
                          checked={item.included}
                          onCheckedChange={(c) => patchItem(item.id, { included: c === true })}
                          aria-label={`Keep ${item.displayName ?? 'biomarker'}`}
                        />
                      </td>
                      <td className="py-1 pr-2">{item.displayName}</td>
                      <td className="py-1">
                        <NumberCell
                          value={item.value}
                          flagged={status !== 'ok'}
                          onChange={(v) => patchItem(item.id, { value: v })}
                        />
                      </td>
                      <td className="py-1">
                        <TextCell
                          value={item.unit}
                          onChange={(v) => patchItem(item.id, { unit: v })}
                        />
                      </td>
                      <td className="py-1">
                        <NumberCell
                          value={item.referenceLow}
                          onChange={(v) => patchItem(item.id, { referenceLow: v })}
                        />
                      </td>
                      <td className="py-1">
                        <NumberCell
                          value={item.referenceHigh}
                          onChange={(v) => patchItem(item.id, { referenceHigh: v })}
                        />
                      </td>
                      <td className="py-1 pl-1">
                        <RangeBadge status={status} />
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {skipped.length > 0 && (
        <section className="flex flex-col gap-2">
          <h2 className="text-lg font-medium">Couldn&rsquo;t match</h2>
          <p className="text-sm text-muted-foreground">
            Map any of these to a biomarker to include them.
          </p>
          <div className="flex flex-col gap-3">
            {skipped.map((row) => (
              <div key={row.id} className="flex flex-wrap items-end gap-2 border-b pb-3">
                <div className="flex flex-col gap-1">
                  <span className="text-sm font-medium">{row.sourceName}</span>
                  <span className="text-xs text-muted-foreground">printed: {row.value}</span>
                </div>
                <BiomarkerSelect
                  catalogue={catalogue.data ?? []}
                  value={row.slug}
                  onChange={(slug) => mapSkipped(row, slug)}
                  triggerClassName="w-56"
                />
                <div className="w-24">
                  <NumberCell
                    value={row.value}
                    onChange={(v) => patchSkipped(row.id, { value: v })}
                  />
                </div>
                <div className="w-24">
                  <TextCell
                    value={row.unit}
                    onChange={(v) => patchSkipped(row.id, { unit: v })}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {error && <p className="text-sm text-destructive">{apiErrorMessage(error)}</p>}

      {/* The negative margin cancels the `p-6` padding on <main> in __root.tsx so the bar spans full width. */}
      <div className="sticky bottom-0 -mx-6 flex items-center gap-3 border-t bg-background px-6 py-3">
        <Button onClick={onConfirm} disabled={pending || keptCount === 0}>
          {pending
            ? 'Adding…'
            : `Add ${keptCount} measurement${keptCount === 1 ? '' : 's'} to my record`}
        </Button>
      </div>
    </div>
  )
}

const CELL_CLASS =
  'h-8 border-transparent bg-transparent px-1.5 shadow-none hover:border-input focus-visible:border-ring dark:bg-transparent'

function NumberCell({
  value,
  onChange,
  flagged,
}: {
  value: string
  onChange: (v: string) => void
  flagged?: boolean
}) {
  return (
    <Input
      inputMode="decimal"
      className={cn(CELL_CLASS, 'text-right tabular-nums', flagged && 'text-warning')}
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

const RANGE_BADGE = {
  high: { label: 'High ↑', title: 'Above reference range' },
  low: { label: 'Low ↓', title: 'Below reference range' },
} as const

function RangeBadge({ status }: { status: RangeStatus }) {
  if (status === 'ok') return null
  const { label, title } = RANGE_BADGE[status]
  return (
    <span className="text-xs font-medium text-warning" title={title}>
      {label}
    </span>
  )
}
