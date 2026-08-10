import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from '@tanstack/react-router'
import { toast } from 'sonner'
import { ApiErrorAlert } from '@/components/api-error-alert'
import { QueryPane } from '@/components/query-pane'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  confirmLabUploadMutation,
  getLabUploadOptions,
  listBiomarkersOptions,
  updateLabDraftMutation,
} from '@/client/@tanstack/react-query.gen'
import type { LabDraft, LabUploadDetail } from '@/client'
import { pluralize } from '@/lib/text'
import { detailPollInterval, invalidateAfterLabWrite } from '@/features/lab-uploads/api'
import { DraftItemsTable, toRow, type DraftRow } from '@/features/lab-uploads/components/draft-items-table'
import { IN_PROGRESS } from '@/features/lab-uploads/status'

// The route owns the param and passes it in: a feature page importing its own
// route file would invert the layer direction and cycle.
export function ReviewPage({ uploadId }: { uploadId: string }) {
  const detail = useQuery({
    ...getLabUploadOptions({ path: { upload_id: uploadId } }),
    // Keep polling if the user lands here before parsing has finished.
    refetchInterval: (query) => detailPollInterval(query.state.data),
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
  if (detail.status === 'confirmed') {
    return <p className="text-sm text-muted-foreground">This report has been confirmed.</p>
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
    const canonical = biomarkers.data?.find((b) => b.slug === slug)
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

    invalidateAfterLabWrite(queryClient)
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

      {/* The negative margin cancels the `p-6` padding on <main> in _authenticated.tsx so the bar spans full width. */}
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
