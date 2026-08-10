import { useRef } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { uploadLabMutation } from '@/client/@tanstack/react-query.gen'
import { ApiErrorAlert } from '@/components/api-error-alert'
import { Button } from '@/components/ui/button'
import { invalidateLabUploads } from '@/features/lab-uploads/api'

// Self-contained Add-data tab: the dialog only registers it, so all upload
// state lives here. The dialog unmounts its content on close, which is what
// keeps a previous error from resurfacing on the next open.
export function UploadTab() {
  const queryClient = useQueryClient()
  const inputRef = useRef<HTMLInputElement>(null)

  const upload = useMutation({
    ...uploadLabMutation(),
    // Parsing is async: the new report appears under Sources as queued.
    onSuccess: () => {
      invalidateLabUploads(queryClient)
      toast.success('Report uploaded', {
        description:
          'We’re reading it now — review it under Sources before it’s added to your record.',
      })
    },
  })

  function onFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    // Reset so re-selecting the same file fires onChange again.
    event.target.value = ''
    if (file) upload.mutate({ body: { file } })
  }

  return (
    <div className="flex flex-col gap-3">
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={onFileChange}
      />
      <div>
        <Button onClick={() => inputRef.current?.click()} disabled={upload.isPending}>
          {upload.isPending ? 'Uploading…' : 'Choose PDF'}
        </Button>
      </div>

      {upload.isError && <ApiErrorAlert error={upload.error} />}
    </div>
  )
}
