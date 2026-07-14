import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, createFileRoute, useNavigate } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
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

export const Route = createFileRoute('/sources/$uploadId/review')({
  component: ReviewComponent,
})

const IN_PROGRESS = new Set(['pending', 'processing'])

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

function toItemRow(item: LabDraftItemRead): ItemRow {
  return {
    id: item.id,
    displayName: item.display_name,
    value: item.value ?? '',
    unit: item.unit ?? '',
    referenceLow: item.reference_low ?? '',
    referenceHigh: item.reference_high ?? '',
    included: item.included,
  }
}

function toSkippedRow(item: LabDraftItemRead): SkippedRow {
  return {
    id: item.id,
    sourceName: item.source_name,
    slug: '',
    value: item.raw_value ?? '',
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

  function patchItem(id: string, patch: Partial<ItemRow>) {
    setItems((rows) => rows.map((r) => (r.id === id ? { ...r, ...patch } : r)))
  }

  function patchSkipped(id: string, patch: Partial<SkippedRow>) {
    setSkipped((rows) => rows.map((r) => (r.id === id ? { ...r, ...patch } : r)))
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
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Review {detail.filename}</h1>
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
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">No biomarkers were matched.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="py-2 font-medium">Keep</th>
                <th className="py-2 font-medium">Biomarker</th>
                <th className="py-2 font-medium">Value</th>
                <th className="py-2 font-medium">Unit</th>
                <th className="py-2 font-medium">Ref. low</th>
                <th className="py-2 font-medium">Ref. high</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-b">
                  <td className="py-2">
                    <Checkbox
                      checked={item.included}
                      onCheckedChange={(c) => patchItem(item.id, { included: c === true })}
                      aria-label={`Keep ${item.displayName ?? 'biomarker'}`}
                    />
                  </td>
                  <td className="py-2">{item.displayName}</td>
                  <td className="py-2">
                    <NumberCell
                      value={item.value}
                      onChange={(v) => patchItem(item.id, { value: v })}
                    />
                  </td>
                  <td className="py-2">
                    <TextCell
                      value={item.unit}
                      onChange={(v) => patchItem(item.id, { unit: v })}
                    />
                  </td>
                  <td className="py-2">
                    <NumberCell
                      value={item.referenceLow}
                      onChange={(v) => patchItem(item.id, { referenceLow: v })}
                    />
                  </td>
                  <td className="py-2">
                    <NumberCell
                      value={item.referenceHigh}
                      onChange={(v) => patchItem(item.id, { referenceHigh: v })}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
                  onChange={(slug) => patchSkipped(row.id, { slug })}
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

      <div>
        <Button onClick={onConfirm} disabled={pending || keptCount === 0}>
          {pending
            ? 'Adding…'
            : `Add ${keptCount} measurement${keptCount === 1 ? '' : 's'} to my record`}
        </Button>
      </div>
    </div>
  )
}

function NumberCell({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <Input
      inputMode="decimal"
      className="h-8"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  )
}

function TextCell({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return <Input className="h-8" value={value} onChange={(e) => onChange(e.target.value)} />
}

function BiomarkerSelect({
  catalogue,
  value,
  onChange,
}: {
  catalogue: BiomarkerRead[]
  value: string
  onChange: (slug: string) => void
}) {
  const byCategory = useMemo(() => {
    const groups = new Map<string, BiomarkerRead[]>()
    for (const b of catalogue) {
      const group = groups.get(b.category)
      if (group) group.push(b)
      else groups.set(b.category, [b])
    }
    return groups
  }, [catalogue])

  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-56">
        <SelectValue placeholder="Map to biomarker" />
      </SelectTrigger>
      <SelectContent>
        {[...byCategory.entries()].map(([category, biomarkers]) => (
          <SelectGroup key={category}>
            <SelectLabel>{category}</SelectLabel>
            {biomarkers.map((b) => (
              <SelectItem key={b.slug} value={b.slug}>
                {b.display_name}
              </SelectItem>
            ))}
          </SelectGroup>
        ))}
      </SelectContent>
    </Select>
  )
}
