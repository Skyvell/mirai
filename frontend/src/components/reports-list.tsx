import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
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
import { cn } from '@/lib/utils'

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
  const remove = useMutation({
    ...deleteLabUploadMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: listLabUploadsQueryKey() })
      queryClient.invalidateQueries({ queryKey: listBiomarkersQueryKey() })
    },
  })

  return (
    <tr className="border-b">
      <td className="py-2">{upload.filename}</td>
      <td className="py-2 whitespace-nowrap">{upload.created_at.slice(0, 10)}</td>
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
        <AlertDialog>
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
                The PDF is removed either way. Its {upload.measurement_count}{' '}
                measurement{upload.measurement_count === 1 ? '' : 's'} can be kept
                (no longer linked to a report) or deleted with it.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={() =>
                  remove.mutate({
                    path: { upload_id: upload.id },
                    query: { delete_measurements: false },
                  })
                }
              >
                Delete report only
              </AlertDialogAction>
              <AlertDialogAction
                className="bg-destructive text-white hover:bg-destructive/90"
                onClick={() =>
                  remove.mutate({
                    path: { upload_id: upload.id },
                    query: { delete_measurements: true },
                  })
                }
              >
                Delete report and measurements
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </td>
    </tr>
  )
}
