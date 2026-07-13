import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
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
  deleteLabUploadMutation,
  listBiomarkersQueryKey,
  listLabUploadsOptions,
  listLabUploadsQueryKey,
} from '@/client/@tanstack/react-query.gen'
import type { LabUploadSummary } from '@/client'
import { apiErrorMessage } from '@/lib/api'
import { cn, localIsoDate } from '@/lib/utils'

export function ReportsList() {
  const uploads = useQuery(listLabUploadsOptions())

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
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-muted-foreground">
              <th className="py-2 font-medium">Report</th>
              <th className="py-2 font-medium">Uploaded</th>
              <th className="py-2 font-medium">Status</th>
              <th className="py-2 font-medium">Measurements</th>
              <th className="py-2" />
            </tr>
          </thead>
          <tbody>
            {uploads.data.map((upload) => (
              <ReportRow key={upload.id} upload={upload} />
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

function ReportRow({ upload }: { upload: LabUploadSummary }) {
  const queryClient = useQueryClient()
  const [deleteMeasurements, setDeleteMeasurements] = useState(false)
  const remove = useMutation({
    ...deleteLabUploadMutation(),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: listLabUploadsQueryKey() })
      // Orphaning keeps the measurements, so the biomarkers payload is unchanged.
      if (variables.query?.delete_measurements) {
        queryClient.invalidateQueries({ queryKey: listBiomarkersQueryKey() })
      }
    },
  })

  return (
    <tr className="border-b">
      <td className="py-2">{upload.filename}</td>
      <td className="py-2 whitespace-nowrap">
        {localIsoDate(new Date(upload.created_at))}
      </td>
      <td
        className={cn(
          'py-2',
          upload.status === 'failed' ? 'text-destructive' : 'text-muted-foreground',
        )}
      >
        {upload.status}
      </td>
      <td className="py-2">{upload.measurement_count}</td>
      <td className="py-2 text-right">
        {remove.isError && (
          <span className="mr-2 text-xs text-destructive">
            {apiErrorMessage(remove.error)}
          </span>
        )}
        <AlertDialog onOpenChange={(open) => open && setDeleteMeasurements(false)}>
          <AlertDialogTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              aria-label={`Delete ${upload.filename}`}
              disabled={remove.isPending}
            >
              <Trash2 />
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete {upload.filename}?</AlertDialogTitle>
              <AlertDialogDescription>
                The report is deleted; its {upload.measurement_count}{' '}
                measurement{upload.measurement_count === 1 ? '' : 's'} stay unless
                you delete them too.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <Label className="flex items-center gap-2 font-normal">
              <Checkbox
                checked={deleteMeasurements}
                onCheckedChange={(checked) => setDeleteMeasurements(checked === true)}
              />
              Also delete its measurements
            </Label>
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
                Delete report
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </td>
    </tr>
  )
}
