import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, getRouteApi, useNavigate } from '@tanstack/react-router'
import { toast } from 'sonner'
import { ApiErrorAlert } from '@/components/api-error-alert'
import { QueryPane } from '@/components/query-pane'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  confirmLabUploadMutation,
  getLabUploadOptions,
  updateLabDraftMutation,
} from '@/client/@tanstack/react-query.gen'
import type { LabDraft, LabUploadDetail } from '@/client'
import { pluralize } from '@/lib/text'
import { biomarkersOptions, findBiomarker } from '@/features/biomarkers'
import { invalidateLabUploadsAndSeries } from '../api/queries'
import { LabUploadDraftItemsTable } from '../components/draft-items-table'
import { constructLabUploadDraftRow, type LabUploadDraftRow } from '../components/draft-row'
import { LAB_UPLOAD_POLL_MS } from '../api/polling'
import { LAB_UPLOAD_IN_PROGRESS } from '../domain/status'

const route = getRouteApi('/_authenticated/sources/$uploadId/review')

export function LabUploadReviewPage() {
  const { uploadId } = route.useParams()

  const detail = useQuery({
    ...getLabUploadOptions({ path: { upload_id: uploadId } }),
    // Keep polling if the user lands here before parsing has finished.
    refetchInterval: (query) =>
      query.state.data && LAB_UPLOAD_IN_PROGRESS.has(query.state.data.status) ? LAB_UPLOAD_POLL_MS : false,
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

// Exhaustive over UploadStatus so a new lifecycle state is a compile error here,
// not a silent fall-through to "Nothing to review".
function ReviewBody({ detail }: { detail: LabUploadDetail }) {
  switch (detail.status) {
    case 'queued':
    case 'processing':
      return <p className="text-sm text-muted-foreground">Still reading this report…</p>
    case 'failed':
      return <ApiErrorAlert message={detail.error_message ?? 'Parsing failed.'} />
    case 'confirmed':
      return <p className="text-sm text-muted-foreground">This report has been confirmed.</p>
    case 'awaiting_review':
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
    default:
      detail.status satisfies never
      return null
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
  const biomarkers = useQuery(biomarkersOptions())

  const [measuredAt, setMeasuredAt] = useState(draft.measured_at ?? '')
  const [rows, setRows] = useState<LabUploadDraftRow[]>(() => [
    ...draft.items.map((i) => constructLabUploadDraftRow(i, 'matched')),
    ...draft.skipped.map((i) => constructLabUploadDraftRow(i, 'unmatched')),
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

  // Confirm commits only rows that are kept and mapped, so the count shows what will
  // land.
  const keptCount = rows.filter((r) => r.included && r.slug).length

  function patchRow(id: string, patch: Partial<LabUploadDraftRow>) {
    setRows((rs) => rs.map((r) => (r.id === id ? { ...r, ...patch } : r)))
  }

  function mapRow(id: string, slug: string) {
    const canonical = findBiomarker(biomarkers.data, slug)
    setRows((rs) =>
      rs.map((r) =>
        r.id === id
          ? { ...r, slug, included: true, unit: r.unit || canonical?.canonical_unit || '' }
          : r,
      ),
    )
  }

  async function confirmDraft() {
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

    invalidateLabUploadsAndSeries(queryClient)
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
          <LabUploadDraftItemsTable
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
          <LabUploadDraftItemsTable
            rows={unmatched}
            biomarkers={biomarkers.data ?? []}
            onPatch={patchRow}
            onMap={mapRow}
          />
        </section>
      )}

      {error && <ApiErrorAlert error={error} />}

      {/* The negative margin cancels the `p-6` padding on <main> in _authenticated.tsx so the bar spans full width. */}
      <div className="sticky bottom-0 -mx-6 flex items-center gap-3 border-t bg-background px-6 py-3">
        <Button onClick={confirmDraft} disabled={pending || keptCount === 0 || !measuredAt}>
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
