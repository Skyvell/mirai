import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  deleteLabUploadMutation,
  listBiomarkerSeriesQueryKey,
  listLabUploadsOptions,
  listLabUploadsQueryKey,
} from '@/client/@tanstack/react-query.gen'
import type { LabUploadSummary, UploadStatus } from '@/client'
import { apiErrorMessage } from '@/lib/api'
import { IN_PROGRESS } from '@/lib/lab-uploads'
import { cn, localIsoDate } from '@/lib/utils'

// User-facing label per lifecycle state; pending and processing read the same.
const STATUS_LABEL: Record<UploadStatus, string> = {
  pending: 'Processing',
  processing: 'Processing',
  awaiting_review: 'Ready to review',
  committed: 'Committed',
  failed: 'Failed',
}

export function ReportsList() {
  const uploads = useQuery({
    ...listLabUploadsOptions(),
    // Poll only while something is still parsing; stop once all rows are terminal.
    refetchInterval: (query) =>
      query.state.data?.some((u) => IN_PROGRESS.has(u.status)) ? 3000 : false,
  })

  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-xl font-semibold tracking-tight">Reports</h2>
      {uploads.isError ? (
        <p className="text-sm text-destructive">{apiErrorMessage(uploads.error)}</p>
      ) : uploads.data === undefined ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : uploads.data.length === 0 ? (
        <p className="text-sm text-muted-foreground">No reports uploaded yet.</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Report</TableHead>
              <TableHead>Uploaded</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Measurements</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {uploads.data.map((upload) => (
              <ReportRow key={upload.id} upload={upload} />
            ))}
          </TableBody>
        </Table>
      )}
    </section>
  )
}

function ReportRow({ upload }: { upload: LabUploadSummary }) {
  const queryClient = useQueryClient()
  const [deleteMeasurements, setDeleteMeasurements] = useState(false)
  const measurements =
    upload.measurement_count === 0
      ? ''
      : `${upload.measurement_count} measurement${upload.measurement_count === 1 ? '' : 's'}`
  const remove = useMutation({
    ...deleteLabUploadMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: listLabUploadsQueryKey() })
      // Deletion removes points or nulls their lab_upload_id; either way the
      // series payload changed.
      queryClient.invalidateQueries({ queryKey: listBiomarkerSeriesQueryKey() })
    },
  })

  const inProgress = IN_PROGRESS.has(upload.status)

  return (
    <TableRow>
      <TableCell>{upload.filename}</TableCell>
      <TableCell>{localIsoDate(new Date(upload.created_at))}</TableCell>
      <TableCell
        className={cn(
          upload.status === 'failed'
            ? 'text-destructive'
            : upload.status === 'awaiting_review'
              ? 'font-medium text-foreground'
              : 'text-muted-foreground',
        )}
      >
        {STATUS_LABEL[upload.status]}
      </TableCell>
      <TableCell>{upload.measurement_count || '—'}</TableCell>
      <TableCell className="text-right">
        {remove.isError && (
          <span className="mr-2 text-xs text-destructive">
            {apiErrorMessage(remove.error)}
          </span>
        )}
        {upload.status === 'awaiting_review' && (
          <Button asChild size="sm" variant="outline" className="mr-1">
            <Link to="/sources/$uploadId/review" params={{ uploadId: upload.id }}>
              Review
            </Link>
          </Button>
        )}
        <AlertDialog onOpenChange={(open) => open && setDeleteMeasurements(false)}>
          <AlertDialogTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              aria-label={`Delete ${upload.filename}`}
              // Deleting mid-parse would strand the worker's inserts; the API blocks it too.
              disabled={remove.isPending || inProgress}
            >
              <Trash2 />
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle className="break-all">
                Delete {upload.filename}?
              </AlertDialogTitle>
              <AlertDialogDescription>
                This action will permanently delete the report.
                {measurements !== '' && (
                  <>
                    {' '}
                    To also delete the {measurements} associated with this
                    report &ndash; use the checkbox.
                  </>
                )}
              </AlertDialogDescription>
            </AlertDialogHeader>
            {measurements !== '' && (
              <Label className="flex items-center gap-2 font-normal">
                <Checkbox
                  checked={deleteMeasurements}
                  onCheckedChange={(checked) =>
                    setDeleteMeasurements(checked === true)
                  }
                />
                Also delete its {measurements}
              </Label>
            )}
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                variant="destructive"
                onClick={() =>
                  remove.mutate({
                    path: { upload_id: upload.id },
                    query: { delete_measurements: deleteMeasurements },
                  })
                }
              >
                {deleteMeasurements
                  ? `Delete report & ${measurements}`
                  : 'Delete report'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </TableCell>
    </TableRow>
  )
}
